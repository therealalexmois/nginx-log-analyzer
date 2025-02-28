"""Настройка логирования через Structlog с JSON-выводом."""

import json
import sys
from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType

import structlog

DEFAULT_LOGGER_NAME = 'nginx_log_analyzer'


def configure_logging(app_name: str = DEFAULT_LOGGER_NAME, log_level: str = 'info') -> structlog.BoundLogger:
    """Создаёт и возвращает настроенный Structlog-логгер.

    Args:
        app_name (str): Название логгера (по умолчанию "nginx_log_analyzer").
        log_level (str): Уровень логирования (debug, info, warning, error).

    Returns:
        structlog.BoundLogger: Настроенный логгер.
    """

    def handle_exception(
        exc_type: 'type[BaseException]', exc_value: BaseException, exc_traceback: 'TracebackType | None'
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error('Необработанное исключение', exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt='iso', utc=True),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(serializer=partial(json.dumps, ensure_ascii=False)),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(app_name).bind(app=app_name, log_level=log_level)


logger = configure_logging()
