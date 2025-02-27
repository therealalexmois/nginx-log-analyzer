"""Модуль вычисления статистики логов.

Этот модуль принимает распарсенные данные (URL, request_time) и вычисляет:
- Общее количество запросов на URL.
- Процентное соотношение количества запросов.
- Суммарное, среднее, максимальное и медианное время запросов.
- Отсортированный список URL по наибольшему `time_sum`.

Структуры:
    StatisticEntry (Dataclass):
        Итоговая структура для хранения рассчитанной статистики.

Функции:
    calculate_statistics:
        Вычисляет статистику по данным логов.

Пример использования:
    >>> parsed_logs = [('/api/data', 0.200), ('/api/data', 0.300), ('/api/info', 0.150)]
    >>> statistics = calculate_statistics(parsed_logs)
    >>> print(statistics[0])  # Первая запись статистики
"""

from dataclasses import dataclass, field
from statistics import median
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.nginx_log_analyzer.log_parser import ParsedLogEntry


class StatisticEntry(TypedDict):
    """Структура записи статистики по URL."""

    url: str
    count: int
    count_perc: float
    time_sum: float
    time_perc: float
    time_avg: float
    time_max: float
    time_med: float


@dataclass
class URLStatistic:
    """Хранит и обрабатывает статистику запросов для конкретного URL."""

    url: str
    count: int = 0
    time_sum: float = 0.0
    times: list[float] = field(default_factory=list)

    def add_request(self, request_time: float) -> None:
        """Добавляет данные о запросе в статистику."""
        self.count += 1
        self.time_sum += request_time
        self.times.append(request_time)

    @property
    def time_max(self) -> float:
        """Возвращает максимальное время запроса."""
        return max(self.times) if self.times else 0.0

    @property
    def time_median(self) -> float:
        """Возвращает медианное время запроса."""
        return median(self.times) if self.times else 0.0

    def compute_metrics(self, total_requests: int, total_time: float) -> StatisticEntry:
        """Вычисляет метрики для данного URL."""
        return StatisticEntry(
            url=self.url,
            count=self.count,
            count_perc=(self.count / total_requests) * 100 if total_requests else 0.0,
            time_sum=self.time_sum,
            time_perc=(self.time_sum / total_time) * 100 if total_time else 0.0,
            time_avg=self.time_sum / self.count if self.count else 0.0,
            time_max=max(self.times) if self.times else 0.0,
            time_med=median(self.times) if self.times else 0.0,
        )


def calculate_statistics(data: 'Sequence[ParsedLogEntry]') -> 'Sequence[StatisticEntry]':
    """Вычисляет статистику по данным логов.

    Args:
        data (Sequence[ParsedLogEntry]): Последовательность с распарсенными данными.

    Returns:
        Sequence[StatisticEntry]: Отсортированный список статистики по URL.
    """
    url_stats: dict[str, URLStatistic] = {}
    total_requests = len(data)
    total_time = sum(entry.request_time for entry in data)

    for entry in data:
        if entry.url not in url_stats:
            url_stats[entry.url] = URLStatistic(url=entry.url)

        url_stats[entry.url].add_request(entry.request_time)

    return tuple(
        sorted(
            (stat.compute_metrics(total_requests, total_time) for stat in url_stats.values()),
            key=lambda x: x['time_sum'],
            reverse=True,
        )
    )
