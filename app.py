import time
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from chatbot.config import config
from chatbot.engine import ChatEngine
from chatbot.ratelimit import limiter
from chatbot.database import get_messages, get_user_stats, get_all_users, init_db
from chatbot.auth import generate_token, token_required, admin_required, optional_auth, register_api_key
from chatbot.errors import register_error_handlers, ValidationError, RateLimitError
from chatbot.logging_config import setup_logging, RequestLogger, performance_tracker
from chatbot.websocket import socketio
from chatbot.knowledge import KnowledgeSystem
from chatbot.analytics import Analytics
from chatbot.encryption import encryption
from chatbot.gdpr import gdpr
from chatbot.audit import audit
from chatbot.offline import offline
from chatbot.notifications import notifications
from chatbot.background import background
from chatbot.optimization import optimizer
from chatbot.tenant import tenant_manager
from chatbot.billing import billing

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
        "version": "3.0.0",
        "name": "Mahi AI Assistant API",
        "features": [
            "chat", "memory", "context", "personality", "plugins",
            "knowledge", "search", "voice", "streaming", "analytics",
            "auth", "barge-in", "stt", "tts", "entity_extraction",
            "sentiment", "multi_language", "knowledge_graph", "ab_testing",
            "encryption", "gdpr", "audit", "offline", "notifications",
            "background_tasks", "optimization", "multi_tenant", "billing",
            "integrations",
        ],
        "total_plugins": 20,
        "total_intents": 50,
        "total_features": 19,
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "3.0.0"})


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
@optional_auth
def stats(user_id):
    return jsonify(get_user_stats(user_id))


@app.route("/users", methods=["GET"])
@admin_required
def users():
    limit = request.args.get("limit", 100, type=int)
    return jsonify({"users": get_all_users(limit), "count": len(get_all_users(limit))})


@app.route("/usage/<user_id>", methods=["GET"])
@optional_auth
def usage(user_id):
    return jsonify(limiter.get_usage(user_id))


@app.route("/session/<user_id>", methods=["DELETE"])
def delete_session(user_id):
    deleted = engine.clear_session(user_id)
    return jsonify({"deleted": deleted, "user_id": user_id})


@app.route("/memory/<user_id>", methods=["GET"])
@optional_auth
def get_memory(user_id):
    return jsonify(engine.get_memory(user_id))


@app.route("/memory/<user_id>", methods=["POST"])
@optional_auth
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
@optional_auth
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
@optional_auth
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
@optional_auth
def list_documents(user_id):
    return jsonify({"documents": knowledge.list_documents(user_id)})


@app.route("/knowledge/<user_id>/search", methods=["POST"])
@optional_auth
def search_knowledge(user_id):
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "query required"}), 400
    results = knowledge.search(user_id, data["query"])
    return jsonify({"results": results, "count": len(results)})


@app.route("/knowledge/<user_id>/stats", methods=["GET"])
@optional_auth
def knowledge_stats(user_id):
    return jsonify(knowledge.get_stats(user_id))


@app.route("/knowledge/doc/<int:doc_id>", methods=["DELETE"])
@optional_auth
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
@admin_required
def get_analytics():
    return jsonify(engine.get_analytics())


@app.route("/analytics/user/<user_id>", methods=["GET"])
@optional_auth
def user_analytics(user_id):
    return jsonify(analytics.get_user_activity(user_id))


@app.route("/analytics/errors", methods=["GET"])
@admin_required
def error_report():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"errors": analytics.get_error_report(limit)})


@app.route("/analytics/hourly", methods=["GET"])
@admin_required
def hourly_stats():
    hours = request.args.get("hours", 24, type=int)
    return jsonify({"hourly": analytics.get_hourly_stats(hours)})


@app.route("/analytics/predict", methods=["GET"])
@admin_required
def predict_usage():
    user_id = request.args.get("user_id")
    return jsonify({"prediction": analytics.predict_usage(user_id)})


@app.route("/analytics/trends", methods=["GET"])
@admin_required
def trend_report():
    days = request.args.get("days", 7, type=int)
    return jsonify({"trends": analytics.get_trend_report(days)})


@app.route("/analytics/performance", methods=["GET"])
@admin_required
def performance_report():
    return jsonify({"performance": analytics.get_performance_report()})


@app.route("/search", methods=["POST"])
def web_search():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "query required"}), 400
    results = engine.search.search(data["query"])
    return jsonify(results)


@app.route("/auth/api-key", methods=["POST"])
@admin_required
def create_api_key():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "name required"}), 400
    api_key = register_api_key(data["name"])
    return jsonify({"api_key": api_key, "name": data["name"]})


@app.route("/gdpr/consent", methods=["POST"])
def record_consent():
    data = request.get_json()
    if not data or "user_id" not in data or "consent_type" not in data:
        return jsonify({"error": "user_id and consent_type required"}), 400
    result = gdpr.record_consent(
        data["user_id"], data["consent_type"], data.get("granted", True),
        request.remote_addr
    )
    return jsonify(result)


@app.route("/gdpr/consent/<user_id>", methods=["GET"])
def get_consents(user_id):
    return jsonify(gdpr.get_consents(user_id))


@app.route("/gdpr/export/<user_id>", methods=["GET"])
@token_required
def export_data(user_id):
    data = gdpr.export_user_data(user_id)
    return jsonify(data)


@app.route("/gdpr/delete/<user_id>", methods=["DELETE"])
@token_required
def delete_data(user_id):
    confirm = request.args.get("confirm", "false").lower() == "true"
    result = gdpr.delete_user_data(user_id, confirm)
    return jsonify(result)


@app.route("/gdpr/anonymize/<user_id>", methods=["POST"])
@admin_required
def anonymize_data(user_id):
    result = gdpr.anonymize_user_data(user_id)
    return jsonify(result)


@app.route("/gdpr/policy", methods=["GET"])
def privacy_policy():
    return jsonify(gdpr.get_privacy_policy())


@app.route("/audit/logs", methods=["GET"])
@admin_required
def get_audit_logs():
    hours = request.args.get("hours", 24, type=int)
    logs = audit.get_recent_logs(hours)
    return jsonify({"logs": logs, "count": len(logs)})


@app.route("/audit/user/<user_id>", methods=["GET"])
@admin_required
def get_user_audit(user_id):
    return jsonify(audit.get_user_activity_summary(user_id))


@app.route("/audit/stats", methods=["GET"])
@admin_required
def audit_stats():
    return jsonify(audit.get_audit_stats())


@app.route("/security/encrypt", methods=["POST"])
@token_required
def encrypt_data():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "text required"}), 400
    result = encryption.encrypt_message(data["text"], data.get("key"))
    return jsonify(result)


@app.route("/security/decrypt", methods=["POST"])
@token_required
def decrypt_data():
    data = request.get_json()
    if not data or "encrypted" not in data:
        return jsonify({"error": "encrypted text required"}), 400
    result = encryption.decrypt_message(data["encrypted"], data.get("key"))
    return jsonify(result)


@app.route("/offline/handle", methods=["POST"])
def handle_offline():
    data = request.get_json()
    if not data or "user_id" not in data or "message" not in data:
        return jsonify({"error": "user_id and message required"}), 400
    result = offline.handle_offline_message(data["user_id"], data["message"])
    return jsonify(result)


@app.route("/offline/queue/<user_id>", methods=["GET"])
def get_offline_queue(user_id):
    return jsonify({"pending": offline.get_pending_messages(user_id)})


@app.route("/offline/process/<user_id>", methods=["POST"])
def process_offline_queue(user_id):
    result = offline.process_queue(user_id, engine.chat)
    return jsonify(result)


@app.route("/offline/stats", methods=["GET"])
def offline_stats():
    return jsonify(offline.get_offline_stats())


@app.route("/notifications/register", methods=["POST"])
def register_notification():
    data = request.get_json()
    if not data or "user_id" not in data or "token" not in data:
        return jsonify({"error": "user_id and token required"}), 400
    result = notifications.register_token(data["user_id"], data.get("platform", "android"), data["token"])
    return jsonify(result)


@app.route("/notifications/send", methods=["POST"])
def send_notification():
    data = request.get_json()
    if not data or "user_id" not in data or "title" not in data:
        return jsonify({"error": "user_id and title required"}), 400
    result = notifications.send_notification(data["user_id"], data["title"], data.get("body", ""), data.get("data"))
    return jsonify(result)


@app.route("/notifications/history/<user_id>", methods=["GET"])
def notification_history(user_id):
    return jsonify({"history": notifications.get_notification_history(user_id)})


@app.route("/background/submit", methods=["POST"])
def submit_background():
    data = request.get_json()
    if not data or "user_id" not in data or "task_type" not in data:
        return jsonify({"error": "user_id and task_type required"}), 400
    task_id = background.submit_task(data["user_id"], data["task_type"], data.get("params"))
    return jsonify({"task_id": task_id})


@app.route("/background/status/<task_id>", methods=["GET"])
def background_status(task_id):
    return jsonify(background.get_task_status(task_id))


@app.route("/background/tasks/<user_id>", methods=["GET"])
def user_background_tasks(user_id):
    return jsonify({"tasks": background.get_user_tasks(user_id)})


@app.route("/background/stats", methods=["GET"])
def background_stats():
    return jsonify(background.get_stats())


@app.route("/optimization/tips", methods=["GET"])
def battery_tips():
    return jsonify({"tips": optimizer.get_battery_tips()})


@app.route("/optimization/stats", methods=["GET"])
def optimization_stats():
    user_id = request.args.get("user_id")
    return jsonify(optimizer.get_optimization_stats(user_id))


@app.route("/tenant/create", methods=["POST"])
@admin_required
def create_tenant():
    data = request.get_json()
    if not data or "tenant_id" not in data or "name" not in data:
        return jsonify({"error": "tenant_id and name required"}), 400
    result = tenant_manager.create_tenant(data["tenant_id"], data["name"], data.get("plan", "free"))
    return jsonify(result)


@app.route("/tenant/<tenant_id>", methods=["GET"])
@token_required
def get_tenant(tenant_id):
    tenant = tenant_manager.get_tenant(tenant_id)
    if tenant:
        return jsonify(tenant)
    return jsonify({"error": "Tenant not found"}), 404


@app.route("/tenant/<tenant_id>", methods=["PUT"])
@admin_required
def update_tenant(tenant_id):
    data = request.get_json()
    result = tenant_manager.update_tenant(tenant_id, **data)
    return jsonify(result)


@app.route("/tenant/<tenant_id>", methods=["DELETE"])
@admin_required
def delete_tenant(tenant_id):
    result = tenant_manager.delete_tenant(tenant_id)
    return jsonify(result)


@app.route("/tenant/<tenant_id>/users", methods=["GET"])
@token_required
def get_tenant_users(tenant_id):
    return jsonify({"users": tenant_manager.get_tenant_users(tenant_id)})


@app.route("/tenant/<tenant_id>/users", methods=["POST"])
@admin_required
def add_tenant_user(tenant_id):
    data = request.get_json()
    if not data or "user_id" not in data:
        return jsonify({"error": "user_id required"}), 400
    result = tenant_manager.add_user_to_tenant(tenant_id, data["user_id"], data.get("role", "member"))
    return jsonify(result)


@app.route("/tenant/<tenant_id>/users/<user_id>", methods=["DELETE"])
@admin_required
def remove_tenant_user(tenant_id, user_id):
    result = tenant_manager.remove_user_from_tenant(tenant_id, user_id)
    return jsonify(result)


@app.route("/tenants", methods=["GET"])
@admin_required
def list_tenants():
    return jsonify({"tenants": tenant_manager.get_all_tenants()})


@app.route("/billing/plans", methods=["GET"])
def get_plans():
    return jsonify({"plans": billing.get_all_plans()})


@app.route("/billing/usage/<tenant_id>", methods=["GET"])
@token_required
def get_billing_usage(tenant_id):
    days = request.args.get("days", 30, type=int)
    return jsonify(billing.get_usage(tenant_id, days))


@app.route("/billing/check/<tenant_id>", methods=["GET"])
def check_billing_limits(tenant_id):
    return jsonify(billing.check_limits(tenant_id))


@app.route("/billing/invoice/<tenant_id>", methods=["POST"])
@admin_required
def create_invoice(tenant_id):
    result = billing.create_invoice(tenant_id)
    return jsonify(result)


@app.route("/billing/invoices/<tenant_id>", methods=["GET"])
@token_required
def get_invoices(tenant_id):
    return jsonify({"invoices": billing.get_invoices(tenant_id)})


@app.route("/api/v2/chat", methods=["POST"])
def chat_v2():
    data = request.get_json()
    if not data or "user_id" not in data or "message" not in data:
        return jsonify({"error": "user_id and message required"}), 400

    user_id = data["user_id"]
    message = data["message"]
    tenant_id = data.get("tenant_id")

    if tenant_id:
        limits = billing.check_limits(tenant_id)
        if not limits["allowed"]:
            return jsonify({
                "error": "Rate limit exceeded",
                "plan": limits["plan"],
                "upgrade": True,
            }), 429

    rate_check = limiter.is_allowed(user_id)
    if not rate_check["allowed"]:
        return jsonify({
            "error": "Rate limit exceeded",
            "retry_after": rate_check["retry_after"],
        }), 429

    result = engine.chat(user_id, message)

    if tenant_id:
        billing.track_usage(tenant_id)

    response_data = {
        "version": "2.1.0",
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


if __name__ == "__main__":
    socketio.init_app(app)
    socketio.run(app, host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
