from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime


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


# ==================== Схемы для обычных кампаний ====================

class AdvertListItemSchema(BaseModel):
    """
    Элемент списка рекламных кампаний (ID и дата изменения)
    """
    advertId: int
    changeTime: datetime


class CampaignGroupSchema(BaseModel):
    """
    Группа кампаний по типу и статусу
    """
    type: int
    status: int
    count: int
    advert_list: List[AdvertListItemSchema]


class CampaignCountResponseSchema(BaseModel):
    """
    Ответ эндпоинта /adv/v1/promotion/count
    """
    adverts: List[CampaignGroupSchema]
    all: int


class BidSettingsSchema(BaseModel):
    """
    Настройки ставок для кампании
    """
    recommendations: int
    search: int


class SubjectSchema(BaseModel):
    """
    Информация о предмете/категории
    """
    id: int
    name: str


class NMSettingItemSchema(BaseModel):
    """
    Настройки для конкретного товара (НМ) в кампании
    """
    bids_kopecks: BidSettingsSchema
    nm_id: int
    subject: SubjectSchema


class PlacementsSchema(BaseModel):
    """
    Настройки размещений кампании
    """
    recommendations: bool
    search: bool


class CampaignSettingsSchema(BaseModel):
    """
    Настройки кампании
    """
    name: str
    payment_type: str
    placements: PlacementsSchema


class CampaignTimestampsSchema(BaseModel):
    """
    Временные метки кампании
    """
    created: datetime
    deleted: Optional[datetime] = None
    started: Optional[datetime] = None
    updated: Optional[datetime] = None


class PromotionCampaignSchema(BaseModel):
    """
    Подробная информация о кампании продвижения
    """
    bid_type: str
    id: int
    nm_settings: List[NMSettingItemSchema]
    settings: CampaignSettingsSchema
    status: int
    timestamps: CampaignTimestampsSchema


class PromotionAdvertsResponseSchema(BaseModel):
    """
    Ответ эндпоинта /api/advert/v2/adverts
    """
    adverts: List[PromotionCampaignSchema]


# ==================== Схемы для медиакампаний ====================

class MediaCampaignSchema(BaseModel):
    """
    Медиакампания
    """
    advertId: int
    name: str
    brand: str
    type: int
    status: int
    createTime: datetime


class MediaCampaignCountItemSchema(BaseModel):
    """
    Элемент подсчета медиакампаний
    """
    type: int
    status: int
    count: int


class MediaCampaignCountResponseSchema(BaseModel):
    """
    Ответ эндпоинта /adv/v1/count
    """
    all: int
    adverts: List[MediaCampaignCountItemSchema]


# ==================== Схемы для запросов ====================

class GetAdvertsRequestSchema(BaseModel):
    """
    Схема для запроса информации о кампаниях
    """
    ids: Optional[str] = Field(None, description="ID кампаний через запятую (максимум 50)")
    statuses: Optional[str] = Field(None, description="Статусы кампаний через запятую")
    payment_type: Optional[str] = Field(None, description="Тип оплаты: cpm или cpc")


class GetMediaCampaignsRequestSchema(BaseModel):
    """
    Схема для запроса медиакампаний
    """
    status: Optional[int] = Field(None, description="Статус медиакампании (1-11)")
    type: Optional[int] = Field(None, description="Тип медиакампании: 1 — размещение по дням, 2 — по просмотрам")
    limit: Optional[int] = Field(None, description="Количество кампаний в ответе")
    offset: Optional[int] = Field(None, description="Смещение относительно первой кампании")
    order: Optional[str] = Field(None, description="Порядок сортировки: create или id")
    direction: Optional[str] = Field(None, description="Направление: desc или asc")


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
    minus_phrases: Optional[List[str]] = None
    norm_queries: Optional[List[str]] = None


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


# ==================== Схемы для статистики ====================

class StatsItemRequest(BaseModel):
    """
    Элемент запроса статистики для товара
    """
    advert_id: int
    nm_id: int


class StatsRequest(BaseModel):
    """
    Запрос статистики поисковых кластеров
    """
    from_date: date = Field(..., description="Дата начала периода (YYYY-MM-DD)")
    to_date: date = Field(..., description="Дата окончания периода (YYYY-MM-DD)")
    items: List[StatsItemRequest] = Field(..., description="Список товаров для статистики")


class StatsPhrase(BaseModel):
    """
    Статистика по поисковой фразе
    """
    norm_query: str = Field(..., description="Поисковая фраза")
    views: int = Field(0, description="Просмотры")
    clicks: int = Field(0, description="Клики")
    orders: int = Field(0, description="Заказы")
    ctr: float = Field(0, description="CTR (%)")
    cpc: float = Field(0, description="CPC (руб)")
    cpm: float = Field(0, description="CPM (руб)")
    avg_pos: float = Field(0, description="Средняя позиция")
    atbs: int = Field(0, description="Добавления в корзину")
    revenue: float = Field(0, description="Выручка (руб)")
    spend: float = Field(0, description="Затраты (руб)")


class StatsItemResponse(BaseModel):
    """
    Статистика по товару
    """
    advert_id: int
    nm_id: int
    phrases: List[StatsPhrase] = Field(default_factory=list, description="Статистика по фразам")


class StatsResponse(BaseModel):
    """
    Ответ со статистикой
    """
    items: List[StatsItemResponse] = Field(default_factory=list)


class FullStatsRequest(BaseModel):
    """
    Запрос полной статистики кампании
    """
    ids: List[int] = Field(..., description="ID кампаний (максимум 50)")
    from_date: date = Field(..., description="Дата начала периода")
    to_date: date = Field(..., description="Дата окончания периода")


class FullStatsDay(BaseModel):
    """
    Статистика за день
    """
    date: date
    views: int = 0
    clicks: int = 0
    orders: int = 0
    revenue: float = 0
    ctr: float = 0
    cpc: float = 0


class FullStatsItem(BaseModel):
    """
    Статистика по товару в кампании
    """
    nm_id: int
    subject: str = ""
    days: List[FullStatsDay] = Field(default_factory=list)
    total_views: int = 0
    total_clicks: int = 0
    total_orders: int = 0
    total_revenue: float = 0


class FullStatsCampaign(BaseModel):
    """
    Статистика по кампании
    """
    id: int
    name: str
    items: List[FullStatsItem] = Field(default_factory=list)
    total_views: int = 0
    total_clicks: int = 0
    total_orders: int = 0
    total_revenue: float = 0


class FullStatsResponse(BaseModel):
    """
    Ответ с полной статистикой
    """
    campaigns: List[FullStatsCampaign] = Field(default_factory=list)