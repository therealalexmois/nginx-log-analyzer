"""Управление конфигурацией анализатора логов Nginx.

Модуль предоставляет функциональность для управления настройками приложения,
загрузки конфигураций из JSON-файла и объединения их со значениями по умолчанию.

Classes:
    Settings: Представляет собой конфигурацию приложения.

Functions:
    get_settings: Возвращает объекта конфигурации.
"""

import functools
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

_T = TypeVar('_T')

DEFAULT_LOG_DIR = Path('./log')
DEFAULT_REPORT_DIR = Path('./reports')
DEFAULT_REPORT_SIZE = 1000
DEFAULT_ERROR_THRESHOLD = 0.1

_ENV_PREFIX = 'LOG_ANALYZER_'


@dataclass(frozen=True)
class Settings:
    """Настройки конфигурации для анализатора логов."""

    error_threshold: float = field(default=DEFAULT_ERROR_THRESHOLD)
    log_dir: Path = field(default_factory=lambda: Path(os.getenv('LOG_DIR', DEFAULT_LOG_DIR)))
    log_file: Path | None = None
    report_dir: Path = field(default_factory=lambda: Path(os.getenv('REPORT_DIR', DEFAULT_REPORT_DIR)))
    report_size: int = DEFAULT_REPORT_SIZE
    structured_log_path: Path | None = None

    @staticmethod
    def from_env() -> 'Settings':
        """Создает объект LogAnalyzerSettings из окружения.

        Args:
            None

        Returns:
            LogAnalyzerSettings: Объект с настройками, загруженными из переменных окружения.
        """

        def get_env_var(name: str, /, default: _T) -> str | _T:
            """Получает переменную окружения с учетом префикса.

            Args:
                name (str): Название переменной окружения (без префикса).
                default (_T): Значение по умолчанию, если переменная окружения отсутствует.

            Returns:
                str | _T: Значение переменной окружения или значение по умолчанию.
            """
            return os.environ.get(f'{_ENV_PREFIX}{name}', default)

        return Settings(
            log_dir=Path(get_env_var('LOG_DIR', DEFAULT_LOG_DIR)),
            report_dir=Path(get_env_var('REPORT_DIR', DEFAULT_REPORT_DIR)),
            report_size=int(get_env_var('REPORT_SIZE', DEFAULT_REPORT_SIZE)),
            error_threshold=float(get_env_var('ERROR_THRESHOLD', DEFAULT_ERROR_THRESHOLD)),
            log_file=Path(value) if (value := get_env_var('LOG_FILE', '')) else None,
            structured_log_path=Path(value) if (value := get_env_var('STRUCTURED_LOG_PATH', '')) else None,
        )


@functools.cache
def get_settings(
    log_dir: Path | None = None,
    report_dir: Path | None = None,
    report_size: int | None = None,
    error_threshold: float | None = None,
    log_file: Path | None = None,
    structured_log_path: Path | None = None,
) -> 'Settings':
    """Возвращает объекта конфигурации.

    Позволяет переопределить настройки через аргументы CLI.

    Args:
        log_dir (Path | None): Директория логов.
        report_dir (Path | None): Директория отчетов.
        report_size (int | None): Максимальное количество URL в отчете.
        error_threshold (float | None): Допустимый процент ошибок парсинга.
        log_file (Path | None): Путь к конкретному файлу лога.
        structured_log_path (Path | None): Путь к файлу структурированного лога.

    Returns:
        Settings: Объект с настройками.
    """
    env_settings = Settings.from_env()

    return Settings(
        log_dir=log_dir or env_settings.log_dir,
        report_dir=report_dir or env_settings.report_dir,
        report_size=report_size or env_settings.report_size,
        error_threshold=error_threshold or env_settings.error_threshold,
        log_file=log_file or env_settings.log_file,
        structured_log_path=structured_log_path or env_settings.structured_log_path,
    )
