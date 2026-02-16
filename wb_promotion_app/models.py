from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


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


# ==================== Модели для обычных кампаний ====================

@dataclass
class AdvertListItem:
    """
    Элемент списка рекламных кампаний (ID и дата изменения)
    """
    advertId: int
    changeTime: datetime


@dataclass
class CampaignGroup:
    """
    Группа кампаний по типу и статусу
    """
    type: int
    status: int
    count: int
    advert_list: List[AdvertListItem]


@dataclass
class CampaignCountResponse:
    """
    Ответ эндпоинта /adv/v1/promotion/count
    """
    adverts: List[CampaignGroup]
    all: int


@dataclass
class BidSettings:
    """
    Настройки ставок для кампании
    """
    recommendations: int
    search: int


@dataclass
class Placements:
    """
    Настройки размещений кампании
    """
    recommendations: bool
    search: bool


@dataclass
class NMSettingItem:
    """
    Настройки для конкретного товара (НМ) в кампании
    """
    bids_kopecks: BidSettings
    nm_id: int
    subject: Dict[str, Any]


@dataclass
class CampaignSettings:
    """
    Настройки кампании
    """
    name: str
    payment_type: str
    placements: Placements


@dataclass
class CampaignTimestamps:
    """
    Временные метки кампании
    """
    created: datetime
    deleted: Optional[datetime] = None
    started: Optional[datetime] = None
    updated: Optional[datetime] = None


@dataclass
class PromotionCampaign:
    """
    Подробная информация о кампании продвижения
    """
    bid_type: str
    id: int
    nm_settings: List[NMSettingItem]
    settings: CampaignSettings
    status: int
    timestamps: CampaignTimestamps


@dataclass
class PromotionAdvertsResponse:
    """
    Ответ эндпоинта /api/advert/v2/adverts
    """
    adverts: List[PromotionCampaign]


# ==================== Модели для медиакампаний ====================

@dataclass
class MediaCampaign:
    """
    Медиакампания
    """
    advertId: int
    name: str
    brand: str
    type: int
    status: int
    createTime: datetime


@dataclass
class MediaCampaignCountItem:
    """
    Элемент подсчета медиакампаний
    """
    type: int
    status: int
    count: int


@dataclass
class MediaCampaignCountResponse:
    """
    Ответ эндпоинта /adv/v1/count
    """
    all: int
    adverts: List[MediaCampaignCountItem]


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