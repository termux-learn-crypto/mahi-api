from flask import Flask, request, jsonify
from chatbot import ChatEngine
from chatbot.ratelimit import limiter
from chatbot.database import get_messages, get_user_stats, get_all_users, init_db

app = Flask(__name__)
engine = ChatEngine()
init_db()


@app.route("/")
def root():
    return jsonify({"status": "running", "version": "1.0.0", "features": [
        "chat", "facts", "quotes", "games", "calculator", "translator", "mobile_commands"
    ]})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


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
        "remaining": rate_check["remaining"],
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
    user_stats = get_user_stats(user_id)
    return jsonify(user_stats)


@app.route("/users", methods=["GET"])
def users():
    limit = request.args.get("limit", 100, type=int)
    all_users = get_all_users(limit=limit)
    return jsonify({
        "users": all_users,
        "count": len(all_users),
    })


@app.route("/usage/<user_id>", methods=["GET"])
def usage(user_id):
    return jsonify(limiter.get_usage(user_id))


@app.route("/session/<user_id>", methods=["DELETE"])
def delete_session(user_id):
    deleted = engine.clear_session(user_id)
    return jsonify({"deleted": deleted, "user_id": user_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
