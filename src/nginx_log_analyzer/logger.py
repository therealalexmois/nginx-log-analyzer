"""Настройка логирования через Structlog с JSON-выводом."""

import functools
import json
import logging
import sys
from enum import Enum, unique
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType


APP_NAME = 'nginx_log_analyzer'
DEFAULT_LOG_LEVEL = 'info'


@unique
class LogLevel(Enum):
    """Уровень журналирования."""

    info = 'info'
    warning = 'warning'
    error = 'error'


def configure_logging(log_file: 'Path | None') -> None:
    """Настраивает Structlog-логгер с JSON-выводом.

    Args:
        log_file: Путь до файла, куда будет записывать логи.
    """

    def handle_exception(
        exc_type: 'type[BaseException]', exc_value: BaseException, exc_traceback: 'TracebackType | None'
    ) -> None:
        """Обрабатывает необработанные исключения и логирует их."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        get_logger().error('Необработанное исключение', exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    log_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file and log_file.exists():
        log_handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt='iso', utc=True),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(serializer=lambda obj: json.dumps(obj, ensure_ascii=False)),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),  # Use stdlib logger
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),  # Default INFO level
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in log_handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


@functools.cache
def get_logger() -> structlog.BoundLogger:
    """Возвращает экземпляр логгера."""
    return structlog.get_logger(APP_NAME).bind(app=APP_NAME)
