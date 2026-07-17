import time
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from chatbot.config import config
from chatbot.engine import ChatEngine
from chatbot.ratelimit import limiter
from chatbot.database import get_messages, get_user_stats, get_all_users, init_db
from chatbot.auth import generate_token, token_required, admin_required, optional_auth
from chatbot.errors import register_error_handlers, ValidationError, RateLimitError
from chatbot.logging_config import setup_logging, RequestLogger, performance_tracker
from chatbot.websocket import socketio
from chatbot.knowledge import KnowledgeSystem
from chatbot.analytics import Analytics

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

CORS(app, resources={r"/*": {"origins": config.CORS_ORIGINS}})

register_error_handlers(app)
logger = setup_logging()
req_logger = RequestLogger(app)
engine = ChatEngine()
knowledge = KnowledgeSystem()
analytics = Analytics()
init_db()


@app.before_request
def before_request():
    g.start_time = time.time()


@app.after_request
def after_request(response):
    if hasattr(g, "start_time"):
        duration = (time.time() - g.start_time) * 1000
        user_id = getattr(g, "current_user", None)
        req_logger.log_request(user_id or "anonymous", request.method, request.path, response.status_code, duration)
        performance_tracker.track(duration, response.status_code < 400)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.route("/")
def root():
    return jsonify({
        "status": "running",
        "version": "2.0.0",
        "name": "Mahi AI Assistant API",
        "features": [
            "chat", "memory", "context", "personality", "plugins",
            "knowledge", "search", "voice", "streaming", "analytics",
        ],
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "2.0.0"})


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "user_id" not in data:
        return jsonify({"error": "user_id required"}), 400
    user_id = data["user_id"]
    token = generate_token(user_id, data.get("role", "user"))
    return jsonify({"token": token, "user_id": user_id, "expires_in": config.JWT_EXPIRY_HOURS * 3600})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "user_id" not in data or "message" not in data:
        return jsonify({"error": "user_id and message required"}), 400

    user_id = data["user_id"]
    message = data["message"]

    rate_check = limiter.is_allowed(user_id)
    if not rate_check["allowed"]:
        return jsonify({
            "error": "Rate limit exceeded",
            "retry_after": rate_check["retry_after"],
            "remaining": 0,
        }), 429

    result = engine.chat(user_id, message)
    response_data = {
        "response": result["response"],
        "intent": result["intent"],
        "emotion": result["emotion"],
        "user_mood": result["user_mood"],
        "remaining": rate_check["remaining"],
        "context": result.get("context", {}),
    }

    if "command" in result:
        response_data["command"] = result["command"]

    return jsonify(response_data)


@app.route("/history/<user_id>", methods=["GET"])
def history(user_id):
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    messages = get_messages(user_id, limit=limit, offset=offset)
    return jsonify({
        "user_id": user_id,
        "messages": messages,
        "count": len(messages),
        "limit": limit,
        "offset": offset,
    })


@app.route("/stats/<user_id>", methods=["GET"])
def stats(user_id):
    return jsonify(get_user_stats(user_id))


@app.route("/users", methods=["GET"])
def users():
    limit = request.args.get("limit", 100, type=int)
    return jsonify({"users": get_all_users(limit), "count": len(get_all_users(limit))})


@app.route("/usage/<user_id>", methods=["GET"])
def usage(user_id):
    return jsonify(limiter.get_usage(user_id))


@app.route("/session/<user_id>", methods=["DELETE"])
def delete_session(user_id):
    deleted = engine.clear_session(user_id)
    return jsonify({"deleted": deleted, "user_id": user_id})


@app.route("/memory/<user_id>", methods=["GET"])
def get_memory(user_id):
    return jsonify(engine.get_memory(user_id))


@app.route("/memory/<user_id>", methods=["POST"])
def add_memory(user_id):
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "content required"}), 400
    engine.add_memory(
        user_id, data["content"],
        data.get("type", "short_term"),
        data.get("importance", 0.5),
    )
    return jsonify({"success": True})


@app.route("/memory/<user_id>/search", methods=["POST"])
def search_memory(user_id):
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "query required"}), 400
    results = engine.search_memory(user_id, data["query"])
    return jsonify({"results": results, "count": len(results)})


@app.route("/context/<user_id>", methods=["GET"])
def get_context(user_id):
    return jsonify(engine.get_context(user_id))


@app.route("/context/<user_id>", methods=["DELETE"])
def clear_context(user_id):
    engine.context_engine.clear_context(user_id)
    return jsonify({"success": True, "user_id": user_id})


@app.route("/knowledge/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400

    file = request.files["file"]
    user_id = request.form.get("user_id", "anonymous")

    if not file.filename:
        return jsonify({"error": "filename required"}), 400

    import os
    from chatbot.config import config as cfg
    upload_path = os.path.join(str(cfg.UPLOADS_DIR), file.filename)
    file.save(upload_path)

    result = knowledge.add_document(user_id, upload_path, file.filename)
    return jsonify(result)


@app.route("/knowledge/<user_id>", methods=["GET"])
def list_documents(user_id):
    return jsonify({"documents": knowledge.list_documents(user_id)})


@app.route("/knowledge/<user_id>/search", methods=["POST"])
def search_knowledge(user_id):
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "query required"}), 400
    results = knowledge.search(user_id, data["query"])
    return jsonify({"results": results, "count": len(results)})


@app.route("/knowledge/<user_id>/stats", methods=["GET"])
def knowledge_stats(user_id):
    return jsonify(knowledge.get_stats(user_id))


@app.route("/knowledge/doc/<int:doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    user_id = request.args.get("user_id", "anonymous")
    deleted = knowledge.delete_document(doc_id, user_id)
    return jsonify({"deleted": deleted})


@app.route("/plugins", methods=["GET"])
def list_plugins():
    return jsonify({"plugins": engine.list_plugins()})


@app.route("/plugins/<name>/execute", methods=["POST"])
def execute_plugin(name):
    data = request.get_json()
    if not data or "user_id" not in data or "message" not in data:
        return jsonify({"error": "user_id and message required"}), 400
    result = engine.execute_plugin(name, data["user_id"], data["message"])
    if result:
        return jsonify(result)
    return jsonify({"error": f"Plugin {name} not found or failed"}), 404


@app.route("/analytics", methods=["GET"])
def get_analytics():
    return jsonify(engine.get_analytics())


@app.route("/analytics/user/<user_id>", methods=["GET"])
def user_analytics(user_id):
    return jsonify(analytics.get_user_activity(user_id))


@app.route("/analytics/errors", methods=["GET"])
def error_report():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"errors": analytics.get_error_report(limit)})


@app.route("/analytics/hourly", methods=["GET"])
def hourly_stats():
    hours = request.args.get("hours", 24, type=int)
    return jsonify({"hourly": analytics.get_hourly_stats(hours)})


@app.route("/search", methods=["POST"])
def web_search():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "query required"}), 400
    results = engine.search.search(data["query"])
    return jsonify(results)


if __name__ == "__main__":
    socketio.init_app(app)
    socketio.run(app, host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
