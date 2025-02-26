"""Модуль обработки аргументов командной строки для Nginx Log Analyzer.

Этот модуль обеспечивает разбор аргументов, передаваемых через командную строку,
и предоставляет их в виде структурированного объекта.

Использование:
    python -m src.nginx_log_analyzer.main --config=config.json

Структуры:
    CLIArgs (Dataclass):
        Представляет разобранные аргументы командной строки.

Функции:
    parse_args: Разбирает аргументы командной строки и возвращает их в виде объекта CLIArgs.

Пример использования:
    >>> args = parse_args()
    >>> print(args.config)  # None или Path('config.json')
"""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CLIArgs:
    """Аргументы командной строки для лог-анализатора."""

    config: Path | None


def parse_args() -> CLIArgs:
    """Разбирает аргументы командной строки.

    Returns:
        CLIArgs: Объект с разобранными аргументами.
    """
    parser = argparse.ArgumentParser(description='Nginx Log Analyzer')
    parser.add_argument('--config', type=Path, help='Путь к файлу конфигурации')

    args = parser.parse_args()
    return CLIArgs(config=args.config)
