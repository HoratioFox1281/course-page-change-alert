"""Compatibility import for running the project directly from its checkout."""

from src.page_change_alert import (
    CourseWatch,
    InfraiClient,
    InfraiError,
    WatchResult,
    main,
    monitor_once,
)

__all__ = [
    "CourseWatch",
    "InfraiClient",
    "InfraiError",
    "WatchResult",
    "main",
    "monitor_once",
]
