import json
import time
import uuid
from datetime import datetime
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from .engine import ChatEngine
from .memory import MemorySystem
from .context_engine import ContextEngine
from .analytics import Analytics


socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
engine = ChatEngine()
memory = MemorySystem()
context_engine = ContextEngine()
analytics = Analytics()

active_connections = {}
audio_buffers = {}


@socketio.on("connect")
def handle_connect():
    user_id = request.args.get("user_id", str(uuid.uuid4()))
    join_room(user_id)
    active_connections[user_id] = {
        "sid": request.sid,
        "connected_at": datetime.now().isoformat(),
        "streaming": False,
    }
    analytics.track_event("connection", user_id)
    emit("connected", {"user_id": user_id, "status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    user_id = request.args.get("user_id")
    if user_id:
        leave_room(user_id)
        active_connections.pop(user_id, None)
        audio_buffers.pop(user_id, None)


@socketio.on("message")
def handle_message(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        user_id = data.get("user_id", "anonymous")
        message = data.get("message", "")

        if not message:
            emit("error", {"error": "Message required"})
            return

        analytics.track_event("message_received", user_id)

        result = engine.chat(user_id, message)

        memory.add_memory(
            user_id, "short_term",
            f"User: {message}\nMahi: {result['response']}",
            importance=0.3,
        )

        context_engine.update_context(
            user_id, message, result["intent"], result["response"]
        )

        analytics.track_event("message_sent", user_id, {"intent": result["intent"]})

        response = {
            "type": "chat_response",
            "response": result["response"],
            "intent": result["intent"],
            "emotion": result["emotion"],
            "user_mood": result["user_mood"],
            "timestamp": datetime.now().isoformat(),
        }

        if "command" in result:
            response["command"] = result["command"]

        emit("response", response, room=user_id)

    except Exception as e:
        analytics.track_event("error", data.get("user_id", "unknown"), {"error": str(e)})
        emit("error", {"error": "Processing error", "details": str(e)})


@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    try:
        user_id = data.get("user_id", "anonymous")
        chunk = data.get("audio")
        is_final = data.get("is_final", False)

        if user_id not in audio_buffers:
            audio_buffers[user_id] = {
                "chunks": [],
                "start_time": time.time(),
                "language": data.get("language", "hi-IN"),
            }

        audio_buffers[user_id]["chunks"].append(chunk)

        if len(audio_buffers[user_id]["chunks"]) % 10 == 0:
            emit("audio_progress", {
                "chunks_received": len(audio_buffers[user_id]["chunks"]),
                "status": "receiving",
            }, room=user_id)

        if is_final:
            process_complete_audio(user_id)

    except Exception as e:
        emit("error", {"error": f"Audio processing error: {str(e)}"})


def process_complete_audio(user_id: str):
    if user_id not in audio_buffers:
        return

    buffer = audio_buffers.pop(user_id)
    duration = time.time() - buffer["start_time"]

    analytics.track_event("audio_received", user_id, {
        "chunks": len(buffer["chunks"]),
        "duration": duration,
    })

    emit("audio_status", {
        "status": "processing",
        "chunks": len(buffer["chunks"]),
    }, room=user_id)

    emit("audio_result", {
        "status": "ready_for_stt",
        "user_id": user_id,
        "chunks": len(buffer["chunks"]),
    }, room=user_id)


@socketio.on("start_listening")
def handle_start_listening(data):
    user_id = data.get("user_id", "anonymous")
    if user_id in active_connections:
        active_connections[user_id]["streaming"] = True
        audio_buffers[user_id] = {
            "chunks": [],
            "start_time": time.time(),
            "language": data.get("language", "hi-IN"),
        }
        emit("listening_started", {"status": "listening"}, room=user_id)


@socketio.on("stop_listening")
def handle_stop_listening(data):
    user_id = data.get("user_id", "anonymous")
    if user_id in active_connections:
        active_connections[user_id]["streaming"] = False
        if user_id in audio_buffers:
            process_complete_audio(user_id)


@socketio.on("interrupt")
def handle_interrupt(data):
    user_id = data.get("user_id", "anonymous")
    analytics.track_event("interrupt", user_id)

    if user_id in audio_buffers:
        del audio_buffers[user_id]

    emit("interrupt_handled", {
        "status": "stopped",
        "message": "Previous response stopped. Ready for new input.",
    }, room=user_id)


@socketio.on("tts_request")
def handle_tts_request(data):
    user_id = data.get("user_id", "anonymous")
    text = data.get("text", "")
    voice = data.get("voice", "female")
    speed = data.get("speed", 1.0)

    if not text:
        emit("error", {"error": "Text required for TTS"})
        return

    emit("tts_status", {
        "status": "processing",
        "text": text[:100],
    }, room=user_id)

    analytics.track_event("tts_request", user_id, {
        "text_length": len(text),
        "voice": voice,
    })

    emit("tts_ready", {
        "status": "ready",
        "text": text,
        "voice": voice,
        "speed": speed,
    }, room=user_id)


@socketio.on("tts_chunk")
def handle_tts_chunk(data):
    user_id = data.get("user_id", "anonymous")
    chunk = data.get("chunk")
    is_final = data.get("is_final", False)

    emit("tts_audio", {
        "chunk": chunk,
        "is_final": is_final,
    }, room=user_id)


@socketio.on("ping")
def handle_ping(data):
    emit("pong", {"timestamp": datetime.now().isoformat()})


def get_active_connections():
    return {
        uid: {
            "connected_at": info["connected_at"],
            "streaming": info["streaming"],
        }
        for uid, info in active_connections.items()
    }
