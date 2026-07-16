from flask import Flask, request, jsonify
from chatbot import ChatEngine

app = Flask(__name__)
engine = ChatEngine()


@app.route("/")
def root():
    return jsonify({"status": "running", "version": "1.0.0"})


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

    result = engine.chat(user_id, message)
    return jsonify({
        "response": result["response"],
        "intent": result["intent"],
        "emotion": result["emotion"],
    })


@app.route("/session/<user_id>", methods=["DELETE"])
def delete_session(user_id):
    deleted = engine.clear_session(user_id)
    return jsonify({"deleted": deleted, "user_id": user_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
