from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON, UniqueConstraint
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


class CampaignStatsHistory(Base):
    """
    История статистики рекламной кампании
    Сохраняется периодически для отслеживания динамики
    """
    __tablename__ = "campaign_stats_history"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, nullable=False, index=True)
    nm_id = Column(Integer, nullable=True, index=True)  # Опционально по товару
    
    # Метрики
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    orders = Column(Integer, default=0)
    atbs = Column(Integer, default=0)  # В корзину
    shks = Column(Integer, default=0)  # Штуки
    canceled = Column(Integer, default=0)  # Отмены
    spend = Column(Float, default=0)  # Затраты
    sum_price = Column(Float, default=0)  # Сумма заказов
    
    # Расчетные метрики
    ctr = Column(Float, default=0)  # CTR %
    cr = Column(Float, default=0)  # CR %
    cpc = Column(Float, default=0)  # CPC ₽
    cpm = Column(Float, default=0)  # CPM ₽
    
    # Период сбора
    period_from = Column(DateTime(timezone=True), nullable=False)
    period_to = Column(DateTime(timezone=True), nullable=False)
    
    # Метаданные
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    is_auto = Column(Boolean, default=True)  # Автоматический сбор или ручной
    
    __table_args__ = (
        UniqueConstraint('campaign_id', 'nm_id', 'period_from', 'period_to', name='uq_campaign_period'),
    )


class AutoRule(Base):
    """
    Правило автоматического управления кампанией
    """
    __tablename__ = "auto_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(Integer, nullable=False, index=True)
    nm_id = Column(Integer, nullable=True)  # Опционально по товару
    
    # Название правила
    name = Column(String(255), nullable=False)
    
    # Условие срабатывания
    condition_type = Column(String(50), nullable=False)  # spend_limit, ctr_low, views_limit, budget_low
    condition_operator = Column(String(10), default=">")  # >, <, >=, <=, =
    condition_value = Column(Float, nullable=False)
    
    # Действие при срабатывании
    action_type = Column(String(50), nullable=False)  # pause_campaign, delete_phrase, reduce_bid
    action_params = Column(JSON, nullable=True)  # Дополнительные параметры действия
    
    # Статус
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связь с пользователем
    user = relationship("User")


class ScheduledTask(Base):
    """
    Расписание периодических задач
    """
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Тип задачи
    task_type = Column(String(50), nullable=False)  # collect_stats, check_rules, calculate_metrics
    
    # Параметры задачи
    campaign_id = Column(Integer, nullable=True, index=True)  # Опционально конкретная кампания
    nm_id = Column(Integer, nullable=True)  # Опционально конкретный товар
    task_params = Column(JSON, nullable=True)  # Дополнительные параметры
    
    # Расписание (cron)
    cron_schedule = Column(String(100), nullable=False)  # Например: "0 */6 * * *" (каждые 6 часов)
    
    # Статус
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связь с пользователем
    user = relationship("User")


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