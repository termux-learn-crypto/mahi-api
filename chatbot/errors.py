from flask import jsonify


class MahiError(Exception):
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", status: int = 500):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(self.message)


class AuthenticationError(MahiError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "AUTH_ERROR", 401)


class AuthorizationError(MahiError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "FORBIDDEN", 403)


class NotFoundError(MahiError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)


class ValidationError(MahiError):
    def __init__(self, message: str = "Invalid input"):
        super().__init__(message, "VALIDATION_ERROR", 400)


class RateLimitError(MahiError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Try again in {retry_after}s",
            "RATE_LIMIT",
            429,
        )
        self.retry_after = retry_after


class SessionError(MahiError):
    def __init__(self, message: str = "Session error"):
        super().__init__(message, "SESSION_ERROR", 500)


class PluginError(MahiError):
    def __init__(self, message: str = "Plugin error"):
        super().__init__(message, "PLUGIN_ERROR", 500)


class VoiceError(MahiError):
    def __init__(self, message: str = "Voice processing error"):
        super().__init__(message, "VOICE_ERROR", 500)


class KnowledgeError(MahiError):
    def __init__(self, message: str = "Knowledge system error"):
        super().__init__(message, "KNOWLEDGE_ERROR", 500)


class SearchError(MahiError):
    def __init__(self, message: str = "Search error"):
        super().__init__(message, "SEARCH_ERROR", 500)


class FileUploadError(MahiError):
    def __init__(self, message: str = "File upload error"):
        super().__init__(message, "FILE_ERROR", 400)


def register_error_handlers(app):
    @app.errorhandler(MahiError)
    def handle_mahi_error(error):
        response = {
            "error": error.message,
            "code": error.code,
            "status": error.status,
        }
        if hasattr(error, "retry_after"):
            response["retry_after"] = error.retry_after
        return jsonify(response), error.status

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "code": "BAD_REQUEST", "status": 400}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found", "code": "NOT_FOUND", "status": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed", "code": "METHOD_NOT_ALLOWED", "status": 405}), 405

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Rate limited", "code": "RATE_LIMIT", "status": 429}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR", "status": 500}), 500
