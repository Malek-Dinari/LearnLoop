"""Structured logging setup.

Call setup_logging() once at application startup (in main.py).
- LOG_FORMAT=text  → human-readable (default, good for local dev)
- LOG_FORMAT=json  → newline-delimited JSON (good for Railway / Datadog / CloudWatch)
"""

import logging
import sys


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    if log_format == "json":
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler(sys.stdout)
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            handler.setFormatter(formatter)
        except ImportError:
            # python-json-logger not installed — fall back to text silently
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    # Replace any existing handlers
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
