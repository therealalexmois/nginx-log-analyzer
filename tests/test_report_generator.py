import json
from typing import TYPE_CHECKING

import pytest

from src.nginx_log_analyzer.report_generator import generate_report
from src.nginx_log_analyzer.stats_calculator import StatisticEntry

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


def test_generate_report_creates_file(tmp_path: 'Path') -> None:
    """Проверяет генерацию HTML-отчета и его содержимое."""
    test_report_name = 'test_report.html'
    expected_url = '/api/test'
    expected_count = 10
    expected_count_perc = 20.0
    expected_time_sum = 5.5
    expected_time_perc = 25.0
    expected_time_avg = 0.55
    expected_time_max = 1.2
    expected_time_median = 0.6

    report_data = [
        StatisticEntry(
            url=expected_url,
            count=expected_count,
            count_perc=expected_count_perc,
            time_sum=expected_time_sum,
            time_perc=expected_time_perc,
            time_avg=expected_time_avg,
            time_max=expected_time_max,
            time_med=expected_time_median,
        )
    ]

    report_path = tmp_path / test_report_name

    report_template_path = tmp_path / 'test_report_template.html'
    report_template_path.write_text('<html><body>$table_json</body></html>', encoding='utf-8')

    generate_report(report_data, report_path, report_template_path)

    assert report_path.exists()
    generated_content = report_path.read_text(encoding='utf-8')

    expected_json = json.dumps(report_data, ensure_ascii=False, indent=2)
    assert f'<html><body>{expected_json}</body></html>' == generated_content


def test_generate_report_logs_error_if_template_missing(mocker: 'MockerFixture', tmp_path: 'Path') -> None:
    """Проверяет, что если шаблон `report.html` отсутствует, вызывается `logger.error`."""
    test_report_name = 'missing_template_report.html'
    report_path = tmp_path / test_report_name

    missing_template_path = tmp_path / 'missing_template.html'

    error_log_mock = mocker.patch('src.nginx_log_analyzer.report_generator.logger.error')

    with pytest.raises(FileNotFoundError, match=f'Шаблон отчета отсутствует: {missing_template_path}'):
        generate_report([], report_path, missing_template_path)

    error_log_mock.assert_called_once_with(
        'Шаблон отчета не найден',
        path=str(missing_template_path),
    )

    assert not report_path.exists()
