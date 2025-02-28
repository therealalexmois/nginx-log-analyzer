"""Главный модуль Nginx Log Analyzer.

Этот модуль выполняет основные шаги:
1. Загружает конфигурацию.
2. Ищет последний доступный лог-файл.
3. Парсит логи, вычисляет статистику и создает отчет.
4. Обрабатывает возможные ошибки и логирует выполнение.

Использование:
    python -m src/nginx_log_analyzer/mainy --config=config.json
"""

import sys
from contextlib import closing

from src.nginx_log_analyzer.cli import parse_args
from src.nginx_log_analyzer.config import ConfigModel
from src.nginx_log_analyzer.log_parser import find_latest_log, LogParsingError, parse_log, unzip_if_needed
from src.nginx_log_analyzer.logger import logger
from src.nginx_log_analyzer.report_generator import generate_report
from src.nginx_log_analyzer.stats_calculator import calculate_statistics


def main() -> None:
    """Основной процесс выполнения лог-анализатора."""
    args = parse_args()

    # 1. Загружаем конфигурацию
    try:
        config = ConfigModel.from_toml(args.config) if args.config else ConfigModel()
    except FileNotFoundError as e:
        logger.error('Ошибка: Файл конфигурации не найден', path=args.config, error=str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error('Ошибка: Некорректный формат файла конфигурации', error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error('Неизвестная ошибка при загрузке конфигурации', error=str(e))
        sys.exit(1)

    logger.info('Конфигурация загружена', config=config)

    # 2. Ищем последний доступный лог-файл
    logger.info('Поиск последнего лог-файла', log_dir=str(config.log_dir))
    log_metadata = find_latest_log(config.log_dir)

    if not log_metadata:
        logger.warning('Нет доступных лог-файлов для анализа')
        sys.exit(0)

    logger.info('Обнаружен лог-файл', file=str(log_metadata.path), file_type=log_metadata.file_type.value)

    # 3. Определяем путь сохранения отчета
    report_filename = f'report-{log_metadata.date.strftime("%Y.%m.%d")}.html'
    report_path = config.report_dir / report_filename

    # Проверяем, существует ли уже отчет
    if report_path.exists():
        logger.info('Отчет уже существует, повторная генерация не требуется', report_path=str(report_path))
        sys.exit(0)

    # 4. Открываем лог-файл и анализируем его
    try:
        with closing(unzip_if_needed(log_metadata.path)) as log_file:
            parsed_entries = list(parse_log(log_file, error_threshold=config.error_threshold))

        if not parsed_entries:
            logger.warning('Файл журнала пуст, отчет не будет создан')
            sys.exit(0)

        logger.info(f'Успешно обработано {len(parsed_entries)} записей')

        # 5. Рассчитываем статистику
        statistics = calculate_statistics(parsed_entries)

        # 6. Ограничиваем размер отчета
        report_data = statistics[: config.report_size]

        # 7. Генерируем отчет
        generate_report(report_data, report_path)
        logger.info('Отчет успешно создан', report_path=str(report_path), report_name=report_filename)

    except LogParsingError as e:
        logger.error('Ошибка парсинга логов', error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error('Неизвестная ошибка при разборе логов', error=str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
