"""
TaskIQ задачи для Wildberries Promotion Manager

Задачи:
1. collect_campaign_stats - Сбор статистики кампании
2. check_auto_rules - Проверка правил авто-управления
3. calculate_campaign_metrics - Расчет дополнительных метрик
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from taskiq import Depends

from .taskiq_config import taskiq_broker
from .config import get_db
from .models import CampaignStatsHistory, AutoRule, UserApiToken
from .services.wb_service import WBService
from .services.stats_service import StatsService
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@taskiq_broker.task
async def collect_campaign_stats(
    campaign_id: int,
    nm_id: Optional[int] = None,
    days_back: int = 1,
    user_id: Optional[int] = None
):
    """
    Сбор статистики кампании и сохранение в историю
    
    Args:
        campaign_id: ID кампании
        nm_id: ID товара (опционально)
        days_back: За сколько дней собирать статистику
        user_id: ID пользователя (для получения токена)
    """
    logger.info(f"Starting stats collection for campaign {campaign_id}, nm {nm_id}")
    
    db = next(get_db())
    try:
        # Получаем токен пользователя
        if user_id:
            stmt = select(UserApiToken).where(
                UserApiToken.user_id == user_id,
                UserApiToken.is_active == True
            ).limit(1)
            user_token = db.execute(stmt).scalar_one_or_none()
            if not user_token:
                logger.error(f"No API token found for user {user_id}")
                return {"error": "No API token"}
            token = user_token.token
        else:
            # Пробуем найти любой активный токен
            stmt = select(UserApiToken).where(UserApiToken.is_active == True).limit(1)
            user_token = db.execute(stmt).scalar_one_or_none()
            if not user_token:
                logger.error("No API token found in database")
                return {"error": "No API token"}
            token = user_token.token
            user_id = user_token.user_id
        
        # Создаем WB сервис
        wb_service = WBService(token)
        stats_service = StatsService(wb_service.client)
        
        # Определяем период
        period_to = datetime.now()
        period_from = period_to - timedelta(days=days_back)
        
        # Получаем полную статистику
        full_stats = stats_service.get_full_stats(
            campaign_id=campaign_id,
            from_date=period_from.strftime("%Y-%m-%d"),
            to_date=period_to.strftime("%Y-%m-%d"),
            nm_id=nm_id
        )
        
        # Сохраняем в историю
        stats_record = CampaignStatsHistory(
            campaign_id=campaign_id,
            nm_id=nm_id,
            views=full_stats.get("total_views", 0),
            clicks=full_stats.get("total_clicks", 0),
            orders=full_stats.get("total_orders", 0),
            atbs=full_stats.get("total_atbs", 0),
            shks=full_stats.get("total_shks", 0),
            canceled=full_stats.get("total_canceled", 0),
            spend=full_stats.get("total_spend", 0),
            sum_price=full_stats.get("total_sum_price", 0),
            ctr=full_stats.get("ctr", 0),
            cr=full_stats.get("cr", 0),
            cpc=full_stats.get("cpc", 0),
            cpm=full_stats.get("cpm", 0),
            period_from=period_from,
            period_to=period_to,
            is_auto=True
        )
        
        db.add(stats_record)
        db.commit()
        
        logger.info(
            f"Stats collected for campaign {campaign_id}: "
            f"views={full_stats.get('total_views', 0)}, "
            f"clicks={full_stats.get('total_clicks', 0)}, "
            f"spend={full_stats.get('total_spend', 0)}"
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "nm_id": nm_id,
            "period_from": period_from.isoformat(),
            "period_to": period_to.isoformat(),
            "stats": full_stats
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error collecting stats for campaign {campaign_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@taskiq_broker.task
async def check_auto_rules(user_id: Optional[int] = None):
    """
    Проверка правил автоматического управления кампаниями
    
    Args:
        user_id: ID пользователя (опционально, если None - проверяем все правила)
    """
    logger.info(f"Starting auto rules check for user {user_id}")
    
    db = next(get_db())
    try:
        # Получаем активные правила
        stmt = select(AutoRule).where(AutoRule.is_active == True)
        if user_id:
            stmt = stmt.where(AutoRule.user_id == user_id)
        
        rules = db.execute(stmt).scalars().all()
        
        results = []
        for rule in rules:
            try:
                result = await _check_single_rule(db, rule)
                results.append(result)
                
                # Обновляем время последней проверки
                rule.last_checked_at = datetime.now()
                if result.get("triggered"):
                    rule.last_triggered_at = datetime.now()
                
            except Exception as e:
                logger.exception(f"Error checking rule {rule.id}: {e}")
                results.append({"rule_id": rule.id, "error": str(e)})
        
        db.commit()
        
        triggered_count = sum(1 for r in results if r.get("triggered"))
        logger.info(f"Rules check completed: {triggered_count}/{len(rules)} rules triggered")
        
        return {
            "success": True,
            "total_rules": len(rules),
            "triggered": triggered_count,
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error checking auto rules: {e}")
        return {"error": str(e)}
    finally:
        db.close()


async def _check_single_rule(db: Session, rule: AutoRule) -> dict:
    """
    Проверка одного правила
    
    Возвращает dict с результатом проверки и действием
    """
    result = {
        "rule_id": rule.id,
        "rule_name": rule.name,
        "triggered": False,
        "action_taken": None
    }
    
    # Получаем последнюю статистику для кампании
    stmt = select(CampaignStatsHistory).where(
        CampaignStatsHistory.campaign_id == rule.campaign_id
    ).order_by(CampaignStatsHistory.collected_at.desc()).limit(1)
    
    if rule.nm_id:
        stmt = stmt.where(CampaignStatsHistory.nm_id == rule.nm_id)
    
    latest_stats = db.execute(stmt).scalar_one_or_none()
    
    if not latest_stats:
        result["error"] = "No stats found"
        return result
    
    # Проверяем условие
    condition_met = False
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
    else:
        result["error"] = f"Unknown condition type: {rule.condition_type}"
        return result
    
    # Проверяем оператор
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
    
    if not condition_met:
        return result
    
    # Условие выполнено - выполняем действие
    result["triggered"] = True
    result["current_value"] = current_value
    
    try:
        if rule.action_type == "pause_campaign":
            # Остановка кампании
            result["action_taken"] = await _pause_campaign(db, rule)
            
        elif rule.action_type == "delete_phrase":
            # Удаление фразы
            result["action_taken"] = await _delete_phrase(db, rule)
            
        elif rule.action_type == "reduce_bid":
            # Уменьшение ставки
            result["action_taken"] = await _reduce_bid(db, rule)
            
    except Exception as e:
        result["action_error"] = str(e)
    
    return result


async def _pause_campaign(db: Session, rule: AutoRule) -> dict:
    """Остановка кампании"""
    # TODO: Реализовать через WB API
    logger.info(f"Auto-pause campaign {rule.campaign_id} by rule {rule.id}")
    return {"action": "pause_campaign", "campaign_id": rule.campaign_id}


async def _delete_phrase(db: Session, rule: AutoRule) -> dict:
    """Удаление минус-фразы"""
    # TODO: Реализовать через WB API
    logger.info(f"Auto-delete phrase for campaign {rule.campaign_id} by rule {rule.id}")
    return {"action": "delete_phrase", "campaign_id": rule.campaign_id}


async def _reduce_bid(db: Session, rule: AutoRule) -> dict:
    """Уменьшение ставки"""
    # TODO: Реализовать через WB API
    logger.info(f"Auto-reduce bid for campaign {rule.campaign_id} by rule {rule.id}")
    return {"action": "reduce_bid", "campaign_id": rule.campaign_id}


@taskiq_broker.task
async def calculate_campaign_metrics(
    campaign_id: Optional[int] = None,
    user_id: Optional[int] = None
):
    """
    Расчет дополнительных метрик на основе сохраненной истории
    
    Args:
        campaign_id: ID кампании (опционально, если None - для всех)
        user_id: ID пользователя
    """
    logger.info(f"Starting metrics calculation for campaign {campaign_id}")
    
    db = next(get_db())
    try:
        # Получаем статистику за последние 7 дней
        stmt = select(CampaignStatsHistory).where(
            CampaignStatsHistory.collected_at >= datetime.now() - timedelta(days=7)
        )
        
        if campaign_id:
            stmt = stmt.where(CampaignStatsHistory.campaign_id == campaign_id)
        
        stats_records = db.execute(stmt).scalars().all()
        
        # Агрегируем данные по кампаниям
        campaign_data = {}
        for record in stats_records:
            cid = record.campaign_id
            if cid not in campaign_data:
                campaign_data[cid] = {
                    "total_views": 0,
                    "total_clicks": 0,
                    "total_orders": 0,
                    "total_spend": 0,
                    "days": 0
                }
            
            campaign_data[cid]["total_views"] += record.views
            campaign_data[cid]["total_clicks"] += record.clicks
            campaign_data[cid]["total_orders"] += record.orders
            campaign_data[cid]["total_spend"] += record.spend
            campaign_data[cid]["days"] += 1
        
        # Рассчитываем метрики
        metrics = {}
        for cid, data in campaign_data.items():
            avg_daily_spend = data["total_spend"] / max(data["days"], 1)
            ctr = (data["total_clicks"] / data["total_views"] * 100) if data["total_views"] > 0 else 0
            cr = (data["total_orders"] / data["total_clicks"] * 100) if data["total_clicks"] > 0 else 0
            cpc = (data["total_spend"] / data["total_clicks"]) if data["total_clicks"] > 0 else 0
            
            # Прогноз расхода на месяц
            monthly_forecast = avg_daily_spend * 30
            
            metrics[cid] = {
                "avg_daily_spend": round(avg_daily_spend, 2),
                "ctr": round(ctr, 2),
                "cr": round(cr, 2),
                "cpc": round(cpc, 2),
                "monthly_forecast": round(monthly_forecast, 2),
                "total_spend_7d": round(data["total_spend"], 2),
                "total_clicks_7d": data["total_clicks"],
                "total_orders_7d": data["total_orders"]
            }
        
        logger.info(f"Metrics calculated for {len(metrics)} campaigns")
        
        return {
            "success": True,
            "campaigns_count": len(metrics),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.exception(f"Error calculating metrics: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# ==================== Задачи с расписанием (Labels) ====================

@taskiq_broker.task(schedule="0 */6 * * *")  # Каждые 6 часов
async def scheduled_collect_all_stats():
    """
    Периодический сбор статистики для всех активных кампаний
    Запускается каждые 6 часов
    """
    logger.info("Starting scheduled collection of all stats")
    
    db = next(get_db())
    try:
        # Получаем все активные кампании пользователя
        # Для простоты собираем статистику для первой найденной кампании
        # В реальной реализации нужно получить список кампаний из WB API
        stmt = select(UserApiToken).where(UserApiToken.is_active == True).limit(1)
        user_token = db.execute(stmt).scalar_one_or_none()
        
        if not user_token:
            logger.warning("No active API token found for scheduled stats collection")
            return {"success": False, "error": "No API token"}
        
        # Получаем список кампаний
        wb_service = WBService(user_token.token)
        campaigns = wb_service.get_campaigns()
        
        if not campaigns:
            logger.info("No campaigns found for scheduled stats collection")
            return {"success": True, "message": "No campaigns"}
        
        # Отправляем задачи на сбор статистики для каждой кампании
        tasks_queued = 0
        for campaign in campaigns[:10]:  # Ограничиваем 10 кампаниями
            campaign_id = campaign.get('id')
            if campaign_id:
                await collect_campaign_stats.kiq(
                    campaign_id=campaign_id,
                    days_back=1,
                    user_id=user_token.user_id
                )
                tasks_queued += 1
        
        logger.info(f"Scheduled stats collection: {tasks_queued} tasks queued")
        
        return {
            "success": True,
            "tasks_queued": tasks_queued,
            "campaigns_count": len(campaigns)
        }
        
    except Exception as e:
        logger.exception(f"Error in scheduled stats collection: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@taskiq_broker.task(schedule="0 */2 * * *")  # Каждые 2 часа
async def scheduled_check_rules():
    """
    Периодическая проверка правил авто-управления
    Запускается каждые 2 часа
    """
    logger.info("Starting scheduled rules check")
    
    try:
        # Отправляем задачу на выполнение
        result = await check_auto_rules.kiq()
        
        logger.info("Scheduled rules check queued")
        
        return {
            "success": True,
            "task_id": result.task_id
        }
        
    except Exception as e:
        logger.exception(f"Error in scheduled rules check: {e}")
        return {"error": str(e)}
