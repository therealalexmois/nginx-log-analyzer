"""Тесты для модуля конфигурации `src/nginx_log_analyzer/config.py`."""

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from src.nginx_log_analyzer.config import (
    ConfigModel,
    DEFAULT_ERROR_THRESHOLD,
    DEFAULT_LOG_DIR,
    DEFAULT_REPORT_DIR,
    DEFAULT_REPORT_SIZE,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any


@pytest.fixture
def valid_config() -> 'Generator[Path, None, None]':
    """Создает временный TOML-файл с корректной конфигурацией."""
    config_data = """\
        log_dir = "logs"
        report_dir = "reports"
        report_size = 500
        error_threshold = 0.2"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(config_data)
        temp_file_path = Path(temp_file.name)

    yield temp_file_path

    temp_file_path.unlink(missing_ok=True)


def test_load_valid_config(valid_config: Path) -> None:
    """Тест загрузки корректного TOML-файла."""
    log_dir = (valid_config.parent / 'logs').resolve()
    report_dir = (valid_config.parent / 'reports').resolve()

    log_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    config = ConfigModel.from_toml(valid_config)

    report_size = 500
    error_threshold = 0.2

    assert isinstance(config, ConfigModel)
    assert config.log_dir.resolve() == log_dir
    assert config.report_dir.resolve() == report_dir
    assert config.report_size == report_size
    assert config.error_threshold == error_threshold
    assert config.log_file is None


def test_load_missing_config_file() -> None:
    """Тест обработки ошибки при отсутствии TOML-файла."""
    with pytest.raises(FileNotFoundError, match='Файл конфигурации .* не найден'):
        ConfigModel.from_toml(Path('non_existing_config.toml'))


def test_invalid_toml_format(tmp_path: Path) -> None:
    """Тест обработки ошибки при некорректном формате TOML."""
    invalid_config = tmp_path / 'invalid.toml'
    invalid_config.write_text('log_dir = "logs"\nerror_threshold = !!invalid', encoding='utf-8')

    with pytest.raises(ValueError, match='Ошибка при разборе TOML'):
        ConfigModel.from_toml(invalid_config)


@pytest.mark.parametrize(
    'config_data, expected_error',
    [
        ({'log_dir': '/non/existing/dir'}, 'log_dir должен быть существующей директорией'),
        ({'report_size': -1, 'log_dir': '/tmp', 'report_dir': '/tmp'}, 'report_size должен быть положительным числом'),
        (
            {'error_threshold': 1.5, 'log_dir': '/tmp', 'report_dir': '/tmp'},
            'error_threshold должен быть числом от 0 до 1',
        ),
    ],
)
def test_invalid_config_values(tmp_path: Path, config_data: dict[str, 'Any'], expected_error: str) -> None:
    """Тест обработки ошибок в конфигурации."""
    config_path = tmp_path / 'config.toml'

    if 'log_dir' not in config_data:
        config_data['log_dir'] = str(tmp_path / 'logs')
        (tmp_path / 'logs').mkdir(parents=True, exist_ok=True)

    if 'report_dir' not in config_data:
        config_data['report_dir'] = str(tmp_path / 'reports')
        (tmp_path / 'reports').mkdir(parents=True, exist_ok=True)

    toml_content = '\n'.join(f'{k} = {repr(v)}' for k, v in config_data.items())
    config_path.write_text(toml_content, encoding='utf-8')

    with pytest.raises(ValueError, match=expected_error):
        ConfigModel.from_toml(config_path)


def test_default_values() -> None:
    """Тест инициализации с настройками по умолчанию."""
    config = ConfigModel()

    assert config.log_dir == DEFAULT_LOG_DIR
    assert config.report_dir == DEFAULT_REPORT_DIR
    assert config.report_size == DEFAULT_REPORT_SIZE
    assert config.error_threshold == DEFAULT_ERROR_THRESHOLD
    assert config.log_file is None
