"""
API endpoints для управления периодическими задачами и авто-правилами
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from ..config import get_db
from ..models import ScheduledTask, AutoRule, CampaignStatsHistory, User, UserApiToken
from ..auth import get_current_user_from_session
from ..tasks import collect_campaign_stats, check_auto_rules, calculate_campaign_metrics
from ..services.wb_service import WBService

router = APIRouter(prefix="/api/tasks", tags=["Scheduled Tasks"])


# ==================== Pydantic схемы ====================

class ScheduledTaskCreate(BaseModel):
    task_type: str = Field(..., description="Тип задачи: collect_stats, check_rules, calculate_metrics")
    campaign_id: Optional[int] = None
    nm_id: Optional[int] = None
    cron_schedule: str = Field(..., description="Cron расписание (например: 0 */6 * * *)")
    task_params: Optional[dict] = None


class ScheduledTaskResponse(BaseModel):
    id: int
    user_id: int
    task_type: str
    campaign_id: Optional[int]
    nm_id: Optional[int]
    cron_schedule: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AutoRuleCreate(BaseModel):
    name: str
    campaign_id: int
    nm_id: Optional[int] = None
    condition_type: str = Field(..., description="spend_limit, ctr_low, views_limit, clicks_limit, cpc_high")
    condition_operator: str = Field(default=">", description=">, <, >=, <=, =")
    condition_value: float
    action_type: str = Field(..., description="pause_campaign, delete_phrase, reduce_bid")
    action_params: Optional[dict] = None


class AutoRuleResponse(BaseModel):
    id: int
    user_id: int
    campaign_id: int
    nm_id: Optional[int]
    name: str
    condition_type: str
    condition_operator: str
    condition_value: float
    action_type: str
    action_params: Optional[dict]
    is_active: bool
    last_checked_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class StatsHistoryResponse(BaseModel):
    id: int
    campaign_id: int
    nm_id: Optional[int]
    views: int
    clicks: int
    orders: int
    spend: float
    ctr: float
    cr: float
    cpc: float
    period_from: datetime
    period_to: datetime
    collected_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Scheduled Tasks ====================

@router.get("/scheduled", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Список всех расписаний пользователя"""
    stmt = select(ScheduledTask).where(ScheduledTask.user_id == user.id)
    tasks = db.execute(stmt).scalars().all()
    return tasks


@router.post("/scheduled", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Создать новое расписание"""
    task = ScheduledTask(
        user_id=user.id,
        task_type=task_data.task_type,
        campaign_id=task_data.campaign_id,
        nm_id=task_data.nm_id,
        cron_schedule=task_data.cron_schedule,
        task_params=task_data.task_params,
        is_active=True
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.patch("/scheduled/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: int,
    is_active: bool = None,
    cron_schedule: str = None,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Обновить расписание"""
    stmt = select(ScheduledTask).where(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == user.id
    )
    task = db.execute(stmt).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if is_active is not None:
        task.is_active = is_active
    
    if cron_schedule:
        task.cron_schedule = cron_schedule
    
    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/scheduled/{task_id}")
async def delete_scheduled_task(
    task_id: int,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Удалить расписание"""
    stmt = select(ScheduledTask).where(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == user.id
    )
    task = db.execute(stmt).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    return {"success": True}


# ==================== Auto Rules ====================

@router.get("/rules", response_model=List[AutoRuleResponse])
async def list_auto_rules(
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Список всех правил авто-управления пользователя"""
    stmt = select(AutoRule).where(AutoRule.user_id == user.id)
    rules = db.execute(stmt).scalars().all()
    return rules


@router.post("/rules", response_model=AutoRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_auto_rule(
    rule_data: AutoRuleCreate,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Создать новое правило авто-управления"""
    rule = AutoRule(
        user_id=user.id,
        campaign_id=rule_data.campaign_id,
        nm_id=rule_data.nm_id,
        name=rule_data.name,
        condition_type=rule_data.condition_type,
        condition_operator=rule_data.condition_operator,
        condition_value=rule_data.condition_value,
        action_type=rule_data.action_type,
        action_params=rule_data.action_params,
        is_active=True
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.patch("/rules/{rule_id}", response_model=AutoRuleResponse)
async def update_auto_rule(
    rule_id: int,
    is_active: bool = None,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Обновить правило"""
    stmt = select(AutoRule).where(
        AutoRule.id == rule_id,
        AutoRule.user_id == user.id
    )
    rule = db.execute(stmt).scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    if is_active is not None:
        rule.is_active = is_active
    
    rule.updated_at = datetime.now()
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/rules/{rule_id}")
async def delete_auto_rule(
    rule_id: int,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Удалить правило"""
    stmt = select(AutoRule).where(
        AutoRule.id == rule_id,
        AutoRule.user_id == user.id
    )
    rule = db.execute(stmt).scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    
    return {"success": True}


@router.post("/rules/{rule_id}/test")
async def test_auto_rule(
    rule_id: int,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Протестировать правило (проверить без выполнения действия)"""
    stmt = select(AutoRule).where(
        AutoRule.id == rule_id,
        AutoRule.user_id == user.id
    )
    rule = db.execute(stmt).scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Получаем последнюю статистику
    stats_stmt = select(CampaignStatsHistory).where(
        CampaignStatsHistory.campaign_id == rule.campaign_id
    ).order_by(CampaignStatsHistory.collected_at.desc()).limit(1)
    
    if rule.nm_id:
        stats_stmt = stats_stmt.where(CampaignStatsHistory.nm_id == rule.nm_id)
    
    latest_stats = db.execute(stats_stmt).scalar_one_or_none()
    
    if not latest_stats:
        return {
            "rule_id": rule_id,
            "triggered": False,
            "message": "No statistics found for this campaign"
        }
    
    # Проверяем условие
    current_value = None
    if rule.condition_type == "spend_limit":
        current_value = latest_stats.spend
    elif rule.condition_type == "ctr_low":
        current_value = latest_stats.ctr
    elif rule.condition_type == "views_limit":
        current_value = latest_stats.views
    elif rule.condition_type == "clicks_limit":
        current_value = latest_stats.clicks
    elif rule.condition_type == "cpc_high":
        current_value = latest_stats.cpc
    
    condition_met = False
    if rule.condition_operator == ">":
        condition_met = current_value > rule.condition_value
    elif rule.condition_operator == "<":
        condition_met = current_value < rule.condition_value
    elif rule.condition_operator == ">=":
        condition_met = current_value >= rule.condition_value
    elif rule.condition_operator == "<=":
        condition_met = current_value <= rule.condition_value
    elif rule.condition_operator == "=":
        condition_met = current_value == rule.condition_value
    
    return {
        "rule_id": rule_id,
        "rule_name": rule.name,
        "condition": f"{rule.condition_type} {rule.condition_operator} {rule.condition_value}",
        "current_value": current_value,
        "triggered": condition_met,
        "action_would_be": rule.action_type if condition_met else None
    }


# ==================== Stats History ====================

@router.get("/stats-history", response_model=List[StatsHistoryResponse])
async def list_stats_history(
    campaign_id: Optional[int] = None,
    days: int = 7,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """История статистики кампаний"""
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    stmt = select(CampaignStatsHistory).where(
        CampaignStatsHistory.collected_at >= cutoff_date
    )
    
    if campaign_id:
        stmt = stmt.where(CampaignStatsHistory.campaign_id == campaign_id)
    
    # Для пользователя - фильтруем по его кампаниям
    # (в реальной реализации нужно связать кампании с пользователем)
    
    stmt = stmt.order_by(CampaignStatsHistory.collected_at.desc())
    records = db.execute(stmt).scalars().all()
    
    return records


# ==================== Manual Task Triggers ====================

@router.post("/collect-stats")
async def trigger_stats_collection(
    campaign_id: int,
    nm_id: Optional[int] = None,
    days_back: int = 1,
    user: User = Depends(get_current_user_from_session)
):
    """Вручную запустить сбор статистики"""
    task = await collect_campaign_stats.kiq(
        campaign_id=campaign_id,
        nm_id=nm_id,
        days_back=days_back,
        user_id=user.id
    )
    
    return {
        "success": True,
        "task_id": task.task_id,
        "message": "Stats collection task queued"
    }


@router.post("/check-rules")
async def trigger_rules_check(
    user: User = Depends(get_current_user_from_session)
):
    """Вручную запустить проверку правил"""
    task = await check_auto_rules.kiq(user_id=user.id)
    
    return {
        "success": True,
        "task_id": task.task_id,
        "message": "Rules check task queued"
    }


@router.post("/calculate-metrics")
async def trigger_metrics_calculation(
    campaign_id: Optional[int] = None,
    user: User = Depends(get_current_user_from_session)
):
    """Вручную запустить расчет метрик"""
    task = await calculate_campaign_metrics.kiq(
        campaign_id=campaign_id,
        user_id=user.id
    )
    
    return {
        "success": True,
        "task_id": task.task_id,
        "message": "Metrics calculation task queued"
    }


# ==================== Phrase Daily Stats ====================

@router.get("/phrase-daily-stats")
async def get_phrase_daily_stats(
    campaign_id: int,
    nm_id: int,
    from_date: str,
    to_date: str,
    user: User = Depends(get_current_user_from_session),
    db: Session = Depends(get_db)
):
    """Получить статистику по фразам по дням"""
    try:
        # Получаем токен пользователя
        stmt = select(UserApiToken).where(
            UserApiToken.user_id == user.id,
            UserApiToken.is_active == True
        ).limit(1)
        user_token = db.execute(stmt).scalar_one_or_none()
        
        if not user_token:
            raise HTTPException(status_code=400, detail="No API token found")
        
        # Получаем статистику
        wb_service = WBService(user_token.token)
        stats = wb_service.get_normquery_daily_stats(
            advert_id=campaign_id,
            nm_id=nm_id,
            from_date=from_date,
            to_date=to_date
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
