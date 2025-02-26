import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from src.nginx_log_analyzer.cli import CLIArgs, parse_args

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_parse_args_no_arguments(monkeypatch: 'MonkeyPatch') -> None:
    """Тест: запуск без аргументов должен вернуть CLIArgs с config=None."""
    monkeypatch.setattr(sys, 'argv', ['nginx_log_analyzer'])

    args = parse_args()

    assert isinstance(args, CLIArgs)
    assert args.config is None


def test_parse_args_with_config(monkeypatch: 'MonkeyPatch', tmp_path: Path) -> None:
    """Тест: передача --config с существующим файлом."""
    config_file = tmp_path / 'config.toml'
    config_file.touch()

    monkeypatch.setattr(sys, 'argv', ['nginx_log_analyzer', '--config', str(config_file)])

    args = parse_args()

    assert isinstance(args, CLIArgs)
    assert args.config == config_file


def test_parse_args_with_nonexistent_config(monkeypatch: 'MonkeyPatch') -> None:
    """Тест: передача --config с несуществующим файлом должна просто передать путь."""
    fake_path = Path('/non/existing/config.toml')

    monkeypatch.setattr(sys, 'argv', ['nginx_log_analyzer', '--config', str(fake_path)])

    args = parse_args()

    assert isinstance(args, CLIArgs)
    assert args.config == fake_path


def test_parse_args_invalid_argument(monkeypatch: 'MonkeyPatch') -> None:
    """Тест: передача несуществующего аргумента должна вызывать SystemExit."""
    monkeypatch.setattr(sys, 'argv', ['nginx_log_analyzer', '--invalid'])

    with pytest.raises(SystemExit):
        parse_args()
