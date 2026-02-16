from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Campaign:
    """
    Модель для представления рекламной кампании
    """
    id: int
    name: str
    status: str
    type: str
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None


@dataclass
class SearchClusterBidItem:
    """
    Модель для представления ставки поискового кластера
    """
    advert_id: int
    bid: int
    nm_id: int
    norm_query: str


@dataclass
class SearchClusterStatsItem:
    """
    Модель для представления статистики поискового кластера
    """
    advert_id: int
    nm_id: int
    atbs: int
    avg_pos: float
    clicks: int
    cpc: float
    cpm: float
    ctr: float
    norm_query: str
    orders: int
    views: int


@dataclass
class MinusPhraseItem:
    """
    Модель для представления минус-фразы
    """
    advert_id: int
    nm_id: int
    norm_queries: List[str]


@dataclass
class SearchClusterListItem:
    """
    Модель для представления элемента списка поисковых кластеров
    """
    advert_id: int
    nm_id: int
    active: Optional[List[str]]
    excluded: Optional[List[str]]