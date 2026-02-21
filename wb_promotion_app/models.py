from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """
    Модель пользователя системы
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Связь с токенами
    api_tokens = relationship("UserApiToken", back_populates="user", cascade="all, delete-orphan")


class UserApiToken(Base):
    """
    Модель API токена пользователя для Wildberries
    """
    __tablename__ = "user_api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь с пользователем
    user = relationship("User", back_populates="api_tokens")


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