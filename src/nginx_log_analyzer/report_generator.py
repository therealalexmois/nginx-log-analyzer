"""Генератор HTML-отчетов.

Этот модуль принимает статистические данные и формирует HTML-отчет.

Функции:
    generate_report: Генерирует HTML-отчет и сохраняет его в файл.
"""

import json
import string
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.nginx_log_analyzer.stats_calculator import StatisticEntry

log = structlog.get_logger()

REPORT_TEMPLATE_PATH = Path().absolute().joinpath('report.html')


def generate_report(data: 'Sequence[StatisticEntry]', report_path: Path) -> None:
    """Генерирует HTML-отчет и сохраняет его в файл.

    Args:
        data (Sequence[StatisticEntry]): Список объектов `StatisticEntry` со статистикой.
        report_path (Path): Путь для сохранения отчета.
    """
    if not REPORT_TEMPLATE_PATH.exists():
        log.error('Шаблон отчета не найден', path=str(REPORT_TEMPLATE_PATH))
        raise FileNotFoundError(f'Шаблон отчета отсутствует: {REPORT_TEMPLATE_PATH}')

    # Читаем HTML-шаблон
    template_content = REPORT_TEMPLATE_PATH.read_text(encoding='utf-8')

    # Формируем JSON для вставки в отчет
    table_json = json.dumps(data, ensure_ascii=False, indent=2)

    # Используем string.Template для безопасного подстановки данных
    template = string.Template(template_content)
    report_html = template.safe_substitute(table_json=table_json)

    # Сохраняем отчет
    report_path.write_text(report_html, encoding='utf-8')
    log.info('Отчет успешно сохранен', report_path=str(report_path))
