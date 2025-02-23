"""Тесты для модуля `src.nginx_log_analyzer.log_parser.py`."""

import gzip
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from src.nginx_log_analyzer.log_parser import find_latest_log, LogFileType, LogParsingError, parse_log, unzip_if_needed

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest_mock import MockerFixture


def log_generator(log_lines: list[str]) -> 'Generator[str, None, None]':
    """Генерирует строки логов.

    Args:
        log_lines (list[str]): Список строк логов.

    Yields:
        Generator[str, None, None]: Генератор строк логов.
    """
    yield from log_lines


@pytest.fixture
def temp_log_dir() -> 'Generator[Path, None, None]':
    """Создает временную директорию для тестирования.

    Yields:
        Generator[Path, None, None]: Объект `Path`, указывающий на временную директорию.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_find_latest_log(temp_log_dir: Path) -> None:
    """Проверить поиск самого последнего лога в директории по дате в имени файла.

    Args:
        temp_log_dir (Path): Временная директория для тестирования.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    (temp_log_dir / 'nginx-access-ui.log-20250201').touch()
    (temp_log_dir / 'nginx-access-ui.log-20250202.gz').touch()
    (temp_log_dir / 'random-file.txt').touch()

    latest_log = find_latest_log(temp_log_dir)

    assert latest_log is not None, 'Лог-файл должен быть найден'
    assert latest_log.path.name == 'nginx-access-ui.log-20250202.gz', 'Должен быть выбран последний лог'
    assert latest_log.date == datetime(2025, 2, 2), 'Дата лога должна быть 2 фервраля 2025'
    assert latest_log.file_type == LogFileType.GZ, 'Тип файла должен быть `.gz`'


def test_find_latest_log_no_logs(temp_log_dir: Path) -> None:
    """Проверяет, если логов в директории нет.

    Args:
        temp_log_dir (Path): Временная директория для тестирования.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    latest_log = find_latest_log(temp_log_dir)
    assert latest_log is None, 'Должно вернуться None, если в директории нет логов'


def test_unzip_if_needed_plain_file() -> None:
    """Проверяет на чтение текстового файла.

    Создает временный текстовый файл журнала и гарантирует, что `unzip_if_needed` правильно прочитает его содержимое.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('Line 1\nLine 2\n')
        temp_file.close()

        file_path = Path(temp_file.name)
        lines = list(unzip_if_needed(file_path))

        assert lines == ['Line 1\n', 'Line 2\n'], 'Ожидается, что содержимое файла будет прочитано построчно'

        file_path.unlink()  # Удаляем файл после теста


def test_unzip_if_needed_gz_file() -> None:
    """Проверяет на чтение `.gz` файла.

    Создает временный gzip-файл и проверяет, что `unzip_if_needed` правильно его читает.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    temp_file_path = Path(tempfile.mkstemp(suffix='.gz')[1])

    try:
        with gzip.open(temp_file_path, 'wt', encoding='utf-8') as gz_file:
            gz_file.write('Compressed Line 1\nCompressed Line 2\n')

        lines = list(unzip_if_needed(temp_file_path))

        expected = ['Compressed Line 1\n', 'Compressed Line 2\n']
        assert lines == expected, f'Ожидаемый результат {expected}, но получен {lines}'

    finally:
        temp_file_path.unlink(missing_ok=True)


def test_parse_log_valid_entries() -> None:
    """Тест на успешный разбор строк логов.

    Проверяет, что `parse_log` корректно извлекает URL и request_time из логов.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    log_lines = log_generator(
        [
            """1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300]
            "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-"
            "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5"
            "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390""",
            """1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300]
            "GET /api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12
            "-" "Python-urllib/2.7" "-" "1498697422-32900793-4708-9752770" "-" 0.133""",
        ]
    )

    results = list(parse_log(log_lines, error_threshold=0.1))

    expected = [
        ('/api/v2/banner/25019354', 0.390),
        ('/api/1/photogenic_banners/list/?server_name=WIN7RB4', 0.133),
    ]

    assert results == expected, f'Ожидаемый результат {expected}, но получен {results}'


def test_parse_log_with_errors() -> None:
    """Проверяет, когда ошибки разбора не превышают порогове значение.

    Проверяет, что `parse_log` игнорирует некорректные строки, но продолжает обработку,
    если процент ошибок не превышает допустимый `error_threshold`.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    log_lines = log_generator(
        [
            'INVALID LOG LINE',
            '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" '
            '"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" '
            '"dc7161be3" 0.390',
            'INVALID LOG LINE',
        ]
    )

    results = list(parse_log(log_lines, error_threshold=0.75))

    expected = [('/api/v2/banner/25019354', 0.390)]

    assert results == expected, f'Ожидаемый результат {expected}, но получен {results}'


def test_parse_log_exceeds_error_threshold() -> None:
    """Тест на выброс исключения, если ошибки парсинга превышают допустимый порог.

    Проверяет, что `parse_log` выбрасывает `LogParsingError`, если процент ошибок превышает `error_threshold`.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    log_lines = log_generator(
        [
            'INVALID LOG LINE',
            'INVALID LOG LINE',
            '1.1.1.1 - - [01/Jan/2024:10:00:00 +0000] "GET /api/data HTTP/1.1" 200 123 "-" "-" "-" "-" "-" 0.150',
            'INVALID LOG LINE',
        ]
    )

    error_threshold = 0.25
    total_lines = 4
    error_count = 3

    with pytest.raises(LogParsingError, match=r'Превышен порог ошибок при разборе логов: \d+\.\d+%') as exc_info:
        list(parse_log(log_lines, error_threshold=error_threshold))

    exc = exc_info.value
    assert exc.error_rate > error_threshold, 'Error rate should exceed threshold'
    assert exc.total_lines == total_lines, 'Total lines should be 4'
    assert exc.errors == error_count, 'Error count should be 3'


def test_logging_error(mocker: 'MockerFixture') -> None:
    """Тест на логирование ошибки при превышении порога ошибок.

    Проверяет, что `parse_log` вызывает логирование ошибки,
    если процент ошибок превышает `error_threshold`.

    Args:
        mocker (MockerFixture): Фикстура для мокирования логирования.

    Returns:
        None: Функция выполняет проверки с помощью `assert`, не возвращает значений.
    """
    error_log_mock = mocker.patch('src.nginx_log_analyzer.log_parser.log.error')

    log_lines = log_generator(
        [
            'INVALID LOG LINE',
            'INVALID LOG LINE',
            'INVALID LOG LINE',
        ]
    )

    error_threshold = 0.2

    with pytest.raises(LogParsingError):
        list(parse_log(log_lines, error_threshold=error_threshold))

    error_log_mock.assert_called_once_with(
        'Превышен допустимый порог ошибок разбора логов',
        error_rate='100.00%',
        error_threshold='20.00%',
        total_lines=3,
        errors=3,
    )
