"""
AMOS-Federation Structured Logging
الهدف: سجلات JSON موحدة لكل الخدمات
النطاق: كل الخدمات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import logging as stdlib_logging

import structlog


def setup_logging(service_name: str = "amos-federation", debug: bool = True):
    """إعداد structured logging عبر structlog."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            stdlib_logging.DEBUG if debug else stdlib_logging.INFO
        ),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(service_name)
