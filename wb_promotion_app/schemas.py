from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class CampaignInfo(BaseModel):
    """
    Схема для информации о рекламной кампании
    """
    id: int
    name: str
    status: str
    type: str
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None


class SearchClusterBid(BaseModel):
    """
    Схема для ставки поискового кластера
    """
    advert_id: int
    nm_id: int
    norm_query: str
    bid: int


class MinusPhraseRequest(BaseModel):
    """
    Схема для запроса минус-фраз
    """
    advert_id: int
    nm_id: int


class SearchClusterStats(BaseModel):
    """
    Схема для запроса статистики поисковых кластеров
    """
    from_date: date
    to_date: date
    items: List[SearchClusterBid]


class SearchClusterListResponse(BaseModel):
    """
    Схема для ответа со списком поисковых кластеров
    """
    advert_id: int
    nm_id: int
    active: Optional[List[str]]
    excluded: Optional[List[str]]