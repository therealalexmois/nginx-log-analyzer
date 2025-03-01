"""Модуль парсинга логов Nginx.

Этот модуль предоставляет функциональность для работы с логами Nginx:
- Поиск последнего файла журнала в указанной директории.
- Распаковка сжатых файлов `.gz` (если требуется).
- Разбор строк логов, извлечение URL и времени обработки запросов.
- Контроль ошибок парсинга с заданным порогом допустимых ошибок.

Структура логов:
- Поддерживается стандартный формат access.log в Nginx.
- Формат строки лога должен соответствовать регулярному выражению `LOG_LINE_PATTERN`.

Классы:
    LogFileType (Enum):
        Перечисление типов файлов журнала (PLAIN, GZ).

    LogFileMetadata (dataclass):
        Хранит метаинформацию о файле журнала:
        - Путь к файлу.
        - Дата из имени файла.
        - Тип файла (обычный или сжатый).

Функции:
    find_latest_log:
        Ищет самый свежий лог-файл в указанной директории.

    unzip_if_needed:
        Читает строки лога, разархивируя `.gz`, если требуется.

    parse_log:
        Разбирает строки лога, извлекая URL и request_time.
        Контролирует процент ошибок, выбрасывая исключение при превышении порога.

Константы:
    LOG_FILENAME_PATTERN (Pattern):
        Регулярное выражение для поиска лог-файлов Nginx с датами.

    LOG_LINE_PATTERN (Pattern):
        Регулярное выражение для разбора строк лога.

    ParsedLogEntry (namedtuple):
        Структура данных для хранения распарсенных URL и request_time.

Исключения:
    ValueError:
        Выбрасывается, если процент ошибок при разборе логов превышает `error_threshold`.

Пример использования:
    >>> from pathlib import Path
    >>> log_metadata = find_latest_log(Path('/var/log/nginx'))
    >>> if log_metadata:
    >>>     with unzip_if_needed(log_metadata.path) as log_file:
    >>>         entries = list(parse_log(log_file, error_threshold=0.1))
    >>>         print(entries[:5])  # Выведет первые 5 записей
"""

import gzip
import re
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from src.nginx_log_analyzer.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


logger = get_logger()

LOG_FILENAME_PATTERN = re.compile(r'nginx-access-ui\.log-(\d{8})(\.gz)?$')
LOG_LINE_PATTERN = re.compile(
    r'(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+'  # IP Address
    r'(?P<remote_user>-|\S+)\s+'  # Remote User (can be "-")
    r'(?P<http_x_real_ip>-|\S+)\s+'  # X-Real-IP (can be "-")
    r'\[(?P<time_local>[^\]]+)]\s+'  # Time Local
    r'"(?P<method>GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+'  # HTTP Method
    r'(?P<url>\S+)\s+HTTP/\d+\.\d+"\s+'  # URL and HTTP version
    r'(?P<status>\d{3})\s+'  # HTTP Status Code
    r'(?P<body_bytes_sent>\d+|-)\s+'  # Bytes sent (or "-")
    r'"(?P<http_referer>[^"]*)"\s+'  # Referer (optional)
    r'"(?P<http_user_agent>[^"]*)"\s+'  # User-Agent (optional)
    r'"(?P<http_x_forwarded_for>[^"]*)"\s+'  # X-Forwarded-For (optional)
    r'"(?P<http_x_request_id>[^"]*)"\s+'  # X-Request-ID (optional)
    r'"(?P<http_x_rb_user>[^"]*)"\s*'  # X-RB-User (optional)
    r'(?P<request_time>\d+\.\d+)?'  # Request time (optional, at the end)
)


class LogFileType(Enum):
    """Перечисление типов файлов журнала."""

    PLAIN = 'plain'
    GZ = 'gz'


@dataclass(frozen=True)
class LogFileMetadata:
    """Хранит информацию о файле журнала."""

    path: 'Path'
    date: datetime
    file_type: LogFileType


def find_latest_log(log_dir: 'Path') -> LogFileMetadata | None:
    """Находит последний файл журнала в указанной директории.

    Args:
        log_dir (Path): Директория, в которой ищется последний лог.

    Returns:
        LogFileMetadata | None: Метаданные найденного файла или None, если файлы не найдены.
    """
    log_files = []

    for file in log_dir.iterdir():
        match = LOG_FILENAME_PATTERN.match(file.name)

        if match:
            date_str, gz_ext = match.groups()
            log_date = datetime.strptime(date_str, '%Y%m%d')
            file_type = LogFileType.GZ if gz_ext else LogFileType.PLAIN
            log_files.append(LogFileMetadata(file, log_date, file_type))

    return max(log_files, key=lambda log_meta: log_meta.date) if log_files else None


def unzip_if_needed(log_path: 'Path') -> 'Generator[str, None, None]':
    """Распаковывает сжатый `.gz` файл, если это необходимо.

    Args:
        log_path (Path): Путь к файлу журнала.

    Yields:
        str: Построчное содержимое файла.
    """
    if log_path.suffix == '.gz':
        with gzip.open(log_path, 'rt', encoding='utf-8') as f:
            yield from f
    else:
        with log_path.open(encoding='utf-8') as f:
            yield from f


ParsedLogEntry = namedtuple('ParsedLogEntry', ['url', 'request_time'])


def parse_log(
    log_file: 'Generator[str, None, None]',
    error_threshold: float,
) -> 'Generator[ParsedLogEntry, None, None]':
    """Разбирает строки лога, извлекая URL и request_time.

    Args:
        log_file (Generator[str, None, None]): Генератор строк файла лога.
        error_threshold (float): Порог допустимого процента ошибок разбора.

    Yields:
        tuple[str, float]: Кортеж (URL, request_time).

    Raises:
        ValueError: Если процент ошибок превышает `error_threshold`.
    """
    errors = 0
    total_lines = 0
    parsed_count = 0

    for line in log_file:
        total_lines += 1
        match = LOG_LINE_PATTERN.match(line.strip())

        if match:
            parsed_count += 1
            yield ParsedLogEntry(
                url=match.group('url'),
                request_time=float(match.group('request_time')),
            )
        else:
            errors += 1

    if total_lines == 0:
        logger.warning('Empty log file provided')
        return None

    error_rate = errors / total_lines

    if error_rate > error_threshold:
        logger.error(
            'Превышен допустимый порог ошибок разбора логов',
            error_rate=f'{error_rate:.2%}',
            error_threshold=f'{error_threshold:.2%}',
            total_lines=total_lines,
            errors=errors,
        )
        raise ValueError(f'Превышен порог ошибок при разборе логов: {error_rate:.2%} (допустимо {error_threshold:.2%})')
