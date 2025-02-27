from statistics import median

from src.nginx_log_analyzer.log_parser import ParsedLogEntry
from src.nginx_log_analyzer.stats_calculator import calculate_statistics, URLStatistic


def test_url_statistic_operations() -> None:
    """Тест: проверка работы URLStatistic."""
    request_time_1 = 0.2
    request_time_2 = 0.3
    request_time_3 = 0.5
    expected_count = 3
    expected_time_sum = request_time_1 + request_time_2 + request_time_3
    expected_time_max = max(request_time_1, request_time_2, request_time_3)
    expected_time_median = median([request_time_1, request_time_2, request_time_3])

    stat = URLStatistic(url='/api/test')

    stat.add_request(request_time_1)
    stat.add_request(0.3)
    stat.add_request(0.5)

    assert stat.count == expected_count
    assert stat.time_sum == expected_time_sum
    assert stat.time_max == expected_time_max
    assert stat.time_median == expected_time_median


def test_calculate_statistics_basic() -> None:
    """Тест: стандартная обработка нескольких URL."""
    expected_unique_urls = 2
    expected_time_sum_api_data = 0.5  # 0.2 + 0.3
    expected_time_sum_api_info = 0.5  # 0.15 + 0.25 + 0.1

    parsed_data = [
        ParsedLogEntry(url='/api/data', request_time=0.200),
        ParsedLogEntry(url='/api/data', request_time=0.300),
        ParsedLogEntry(url='/api/info', request_time=0.150),
        ParsedLogEntry(url='/api/info', request_time=0.250),
        ParsedLogEntry(url='/api/info', request_time=0.100),
    ]

    result = calculate_statistics(parsed_data)

    assert isinstance(result, tuple)
    assert len(result) == expected_unique_urls
    assert result[0]['url'] == '/api/data'  # Наибольший `time_sum`
    assert result[0]['time_sum'] == expected_time_sum_api_data
    assert result[1]['url'] == '/api/info'
    assert result[1]['time_sum'] == expected_time_sum_api_info


def test_calculate_statistics_single_url() -> None:
    """Тест: все запросы идут на один URL."""
    expected_unique_urls = 1
    expected_count = 3  # Количество запросов всего
    expected_time_avg = 1.5  # (1.0 + 1.5 + 2.0) / 3
    expected_time_max = 2.0
    expected_time_median = 1.5  # Результат медианы от [1.0, 1.5, 2.0]

    parsed_data = [
        ParsedLogEntry(url='/home', request_time=1.0),
        ParsedLogEntry(url='/home', request_time=1.5),
        ParsedLogEntry(url='/home', request_time=2.0),
    ]

    result = calculate_statistics(parsed_data)

    assert len(result) == expected_unique_urls
    assert result[0]['url'] == '/home'
    assert result[0]['count'] == expected_count
    assert result[0]['time_avg'] == expected_time_avg
    assert result[0]['time_max'] == expected_time_max
    assert result[0]['time_med'] == expected_time_median


def test_calculate_statistics_empty_input() -> None:
    """Тест: обработка пустого списка."""
    parsed_data: list[ParsedLogEntry] = []

    result = calculate_statistics(parsed_data)

    assert isinstance(result, tuple)
    assert len(result) == 0


def test_calculate_statistics_zero_times() -> None:
    """Тест: все request_time равны нулю."""
    parsed_data = [
        ParsedLogEntry(url='/zero', request_time=0.0),
        ParsedLogEntry(url='/zero', request_time=0.0),
        ParsedLogEntry(url='/zero', request_time=0.0),
    ]

    result = calculate_statistics(parsed_data)

    assert len(result) == 1
    assert result[0]['time_sum'] == 0.0
    assert result[0]['time_avg'] == 0.0
    assert result[0]['time_med'] == 0.0
    assert result[0]['time_max'] == 0.0


def test_calculate_statistics_large_numbers() -> None:
    """Тест: обработка больших значений request_time."""
    expected_unique_urls = 1
    expected_time_sum = 6_000_000.0  # 1M + 2M + 3M
    expected_time_avg = 2_000_000.0  # (1M + 2M + 3M) / 3
    expected_time_max = 3_000_000.0
    expected_time_median = 2_000_000.0  # Результат медианы от [1M, 2M, 3M]

    parsed_data = [
        ParsedLogEntry(url='/heavy', request_time=1_000_000.0),
        ParsedLogEntry(url='/heavy', request_time=2_000_000.0),
        ParsedLogEntry(url='/heavy', request_time=3_000_000.0),
    ]

    result = calculate_statistics(parsed_data)

    assert len(result) == expected_unique_urls
    assert result[0]['time_sum'] == expected_time_sum
    assert result[0]['time_avg'] == expected_time_avg
    assert result[0]['time_max'] == expected_time_max
    assert result[0]['time_med'] == expected_time_median
