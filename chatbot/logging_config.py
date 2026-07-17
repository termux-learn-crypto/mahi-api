import logging
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from .config import config


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"{color}[{timestamp}] {record.levelname:8s}{reset} {record.name}: {record.getMessage()}"


def setup_logging():
    root_logger = logging.getLogger("mahi")
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)

    try:
        log_file = config.LOGS_DIR / "mahi.log"
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    except Exception:
        pass

    access_logger = logging.getLogger("mahi.access")
    error_logger = logging.getLogger("mahi.error")
    plugin_logger = logging.getLogger("mahi.plugins")
    voice_logger = logging.getLogger("mahi.voice")

    return root_logger


class RequestLogger:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("mahi.access")

    def log_request(self, user_id: str, method: str, path: str, status: int, duration: float):
        self.logger.info(
            f"{method} {path} {status} {duration:.3f}s",
            extra={"user_id": user_id, "duration": duration, "status": status},
        )


class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            "api_calls": 0,
            "total_duration": 0.0,
            "errors": 0,
            "avg_latency": 0.0,
        }
        self.latencies = []

    def track(self, duration: float, success: bool = True):
        self.metrics["api_calls"] += 1
        self.metrics["total_duration"] += duration
        self.latencies.append(duration)
        if not success:
            self.metrics["errors"] += 1
        if self.latencies:
            self.metrics["avg_latency"] = sum(self.latencies) / len(self.latencies)

    def get_metrics(self):
        return {
            **self.metrics,
            "error_rate": (
                self.metrics["errors"] / max(self.metrics["api_calls"], 1) * 100
            ),
        }


performance_tracker = PerformanceTracker()
