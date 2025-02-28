"""Генератор HTML-отчетов.

Этот модуль принимает статистические данные и формирует HTML-отчет.

Функции:
    generate_report: Генерирует HTML-отчет и сохраняет его в файл.
"""

import json
import string
from pathlib import Path
from typing import TYPE_CHECKING

from src.nginx_log_analyzer.logger import logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.nginx_log_analyzer.stats_calculator import StatisticEntry


REPORT_TEMPLATE_PATH = Path().absolute().joinpath('report.html')


def generate_report(data: 'Sequence[StatisticEntry]', report_path: Path, template_path: Path) -> None:
    """Генерирует HTML-отчет и сохраняет его в файл.

    Args:
        data: Список объектов `StatisticEntry` со статистикой.
        report_path: Путь для сохранения отчета.
        template_path: Путь к HTML-шаблону отчета.
    """
    if not template_path.exists():
        logger.error('Шаблон отчета не найден', path=str(template_path))
        raise FileNotFoundError(f'Шаблон отчета отсутствует: {template_path}')

    # Читаем HTML-шаблон
    template_content = template_path.read_text(encoding='utf-8')

    # Формируем JSON для вставки в отчет
    table_json = json.dumps(data, ensure_ascii=False, indent=2)

    # Используем string.Template для безопасного подстановки данных
    template = string.Template(template_content)
    report_html = template.safe_substitute(table_json=table_json)

    # Сохраняем отчет
    report_path.write_text(report_html, encoding='utf-8')
    logger.info('Отчет успешно сохранен', report_path=str(report_path))
