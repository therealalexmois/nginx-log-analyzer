"""Модуль конфигурации лог-анализатора.

Этот модуль объединяет:
- Валидацию входных данных
- Значения по умолчанию
- Формирование финальной конфигурации в виде объекта

Классы:
    ConfigModel: Основной класс конфигурации.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


DEFAULT_LOG_DIR = Path().absolute().joinpath('logs')
DEFAULT_REPORT_DIR = Path().absolute().joinpath('reports')
DEFAULT_REPORT_SIZE = 1000
DEFAULT_ERROR_THRESHOLD = 0.1
DEFAULT_REPORT_TEMPLATE_FILENAME = 'report.html'
DEFAULT_REPORT_TEMPLATE_PATH = Path().absolute().joinpath(DEFAULT_REPORT_TEMPLATE_FILENAME)


@dataclass(frozen=True)
class ConfigModel:
    """Конфигурация лог-анализатора.

    Выполняет валидацию и обработку входных данных, объединяя:
    - Значения из файла конфигурации (если указан)
    - Значения по умолчанию
    """

    log_dir: Path = field(default=DEFAULT_LOG_DIR)
    report_dir: Path = field(default=DEFAULT_REPORT_DIR)
    log_file: Path | None = None
    report_size: int = DEFAULT_REPORT_SIZE
    error_threshold: float = DEFAULT_ERROR_THRESHOLD
    report_template_path: Path = field(default=DEFAULT_REPORT_TEMPLATE_PATH)

    @classmethod
    def from_dict(cls, config_data: dict[str, 'Any']) -> 'ConfigModel':
        """Создает объект конфигурации из словаря.

        Args:
            config_data (dict): Исходные данные конфигурации.

        Returns:
            ConfigModel: Объект настроек.

        Raises:
            ValueError: Если параметры не проходят валидацию.
        """
        return cls(
            error_threshold=cls._validate_error_threshold(config_data.get('error_threshold', DEFAULT_ERROR_THRESHOLD)),
            log_dir=cls._validate_directory(config_data.get('log_dir', DEFAULT_LOG_DIR), 'log_dir'),
            log_file=cls._validate_log_file(config_data.get('log_file')),
            report_dir=cls._validate_directory(config_data.get('report_dir', DEFAULT_REPORT_DIR), 'report_dir'),
            report_size=cls._validate_report_size(config_data.get('report_size', DEFAULT_REPORT_SIZE)),
            report_template_path=cls.report_template_path,
        )

    @classmethod
    def from_toml(cls, config_path: Path) -> 'ConfigModel':
        """Загружает конфигурацию из TOML-файла.

        Args:
            config_path (Path): Путь к TOML файлу.

        Returns:
            ConfigModel: Загруженная конфигурация.

        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если TOML некорректен.
        """
        if not config_path.exists():
            raise FileNotFoundError(f'Файл конфигурации {config_path} не найден.')

        with config_path.open('rb') as f:
            try:
                config_data = tomllib.load(f)
            except tomllib.TOMLDecodeError as error:
                raise ValueError(f'Ошибка при разборе TOML: {error}') from error

        config_dir = config_path.parent
        log_dir = config_dir / config_data.get('log_dir', 'logs')
        report_dir = config_dir / config_data.get('report_dir', 'reports')

        log_file_value = config_data.get('log_file')
        log_file = (
            cls._validate_log_file(config_dir / log_file_value) if isinstance(log_file_value, (str | Path)) else None
        )

        report_size = config_data.get('report_size', DEFAULT_REPORT_SIZE)
        error_threshold = config_data.get('error_threshold', DEFAULT_ERROR_THRESHOLD)

        return cls(
            error_threshold=cls._validate_error_threshold(error_threshold),
            log_dir=cls._validate_directory(log_dir, 'log_dir'),
            log_file=log_file,
            report_dir=cls._validate_directory(report_dir, 'report_dir'),
            report_size=cls._validate_report_size(report_size),
            report_template_path=cls.report_template_path,
        )

    @staticmethod
    def _validate_directory(value: str | Path, folder_name: str) -> Path:
        """Валидирует директорию.

        Args:
            value (str | Path): Значение директории.
            folder_name (str): Название поля для ошибки.

        Returns:
            Path: Проверенный путь.

        Raises:
            ValueError: Если директория не существует.
        """
        path = Path(value).resolve()
        if not path.is_dir():
            raise ValueError(f'{folder_name} должен быть существующей директорией: {path}')
        return path

    @staticmethod
    def _validate_log_file(value: str | Path | None) -> Path | None:
        """Валидирует путь к лог-файлу.

        Args:
            value (str | Path | None): Значение пути.

        Returns:
            Path | None: Проверенный путь или None.

        Raises:
            ValueError: Если файл не существует.
        """
        if value is None:
            return None
        path = Path(value).resolve()
        if not path.is_file():
            raise ValueError(f'log_file должен быть существующим файлом: {path}')
        return path

    @staticmethod
    def _validate_report_size(value: int) -> int:
        """Валидирует размер отчета.

        Args:
            value (int): Размер отчета.

        Returns:
            int: Проверенное значение.

        Raises:
            ValueError: Если значение некорректно.
        """
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f'report_size должен быть положительным числом: {value}')
        return value

    @staticmethod
    def _validate_error_threshold(value: float) -> float:
        """Валидирует порог ошибок.

        Args:
            value (float): Порог ошибок.

        Returns:
            float: Проверенное значение.

        Raises:
            ValueError: Если значение некорректно.
        """
        if not isinstance(value, (int | float)) or not (0.0 <= value <= 1.0):
            raise ValueError(f'error_threshold должен быть числом от 0 до 1: {value}')
        return float(value)


_CONFIG_CONTAINER: dict[str, 'ConfigModel'] = {}


def set_config(config: 'ConfigModel') -> None:
    """Устанавливает глобальную конфигурацию."""
    if 'instance' in _CONFIG_CONTAINER:
        raise RuntimeError('Конфигурация уже установлена и не может быть изменена.')
    _CONFIG_CONTAINER['instance'] = config


def get_config() -> 'ConfigModel':
    """Возвращает глобальную конфигурацию, установленную через `set_config`."""
    if 'instance' not in _CONFIG_CONTAINER:
        raise RuntimeError('Конфигурация не установлена. Вызовите `set_config()` перед `get_config()`.')
    return _CONFIG_CONTAINER['instance']
