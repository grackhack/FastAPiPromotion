"""
Web роуты для страниц статистики
SSR рендеринг страниц
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import get_db
from ..models import User, UserApiToken
from ..auth import get_current_user_from_session, get_user_api_token
from ..api_client import WBPromotionClient
from ..services.stats_service import StatsService


router = APIRouter(tags=["Web Stats"])


async def get_wb_client_for_user(request: Request, db: Session) -> WBPromotionClient:
    """Получить WB клиент для текущего пользователя"""
    user = await get_current_user_from_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    token = get_user_api_token(db, user.id)
    if not token:
        raise HTTPException(
            status_code=403, 
            detail="Необходимо добавить WB API токен в личном кабинете"
        )
    
    return WBPromotionClient(token)


@router.get("/stats/campaign/{campaign_id}", response_class=HTMLResponse)
async def campaign_stats_page(
    request: Request,
    campaign_id: int,
    db: Session = Depends(get_db),
    wb_client: WBPromotionClient = Depends(get_wb_client_for_user)
):
    """
    Страница статистики рекламной кампании
    """
    from . import main
    
    # Получаем параметры из query string
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    
    # Даты по умолчанию - последние 7 дней
    if not from_date or not to_date:
        from datetime import datetime, timedelta
        to = datetime.now()
        from_date = (to - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = to.strftime("%Y-%m-%d")
    
    # Получаем статистику
    stats_service = StatsService(wb_client)
    
    try:
        # Общая статистика
        stats = stats_service.get_campaign_stats(campaign_id, from_date, to_date)
        
        # Статистика по запросам (для топ запросов)
        norm_stats = stats_service.get_norm_query_stats(
            campaign_id, 
            nm_id=0,  # Все товары
            from_date=from_date,
            to_date=to_date
        )
        
        # Получаем информацию о кампании
        campaigns = wb_client.get_campaigns()
        campaign = next((c for c in campaigns if c.id == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Кампания не найдена")
        
    except Exception as e:
        return main.templates.get_template("error.html").render(
            request=request,
            error_message=f"Ошибка загрузки статистики: {str(e)}"
        )
    
    return main.templates.get_template("stats-campaign.html").render(
        request=request,
        campaign=campaign,
        stats=stats,
        queries=norm_stats.get("queries", [])[:20],  # Топ 20 запросов
        from_date=from_date,
        to_date=to_date
    )


@router.get("/stats/campaign/{campaign_id}/nm/{nm_id}", response_class=HTMLResponse)
async def nm_stats_page(
    request: Request,
    campaign_id: int,
    nm_id: int,
    db: Session = Depends(get_db),
    wb_client: WBPromotionClient = Depends(get_wb_client_for_user)
):
    """
    Страница статистики по конкретному товару (NM)
    """
    from . import main
    
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    
    if not from_date or not to_date:
        from datetime import datetime, timedelta
        to = datetime.now()
        from_date = (to - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = to.strftime("%Y-%m-%d")
    
    stats_service = StatsService(wb_client)
    
    try:
        stats = stats_service.get_campaign_stats(campaign_id, from_date, to_date, nm_id)
        norm_stats = stats_service.get_norm_query_stats(
            campaign_id, nm_id, from_date, to_date
        )
        
        campaigns = wb_client.get_campaigns()
        campaign = next((c for c in campaigns if c.id == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Кампания не найдена")
            
    except Exception as e:
        return main.templates.get_template("error.html").render(
            request=request,
            error_message=f"Ошибка загрузки статистики: {str(e)}"
        )
    
    return main.templates.get_template("stats-nm.html").render(
        request=request,
        campaign=campaign,
        nm_id=nm_id,
        stats=stats,
        queries=norm_stats.get("queries", [])[:50],
        from_date=from_date,
        to_date=to_date
    )


@router.get("/campaigns/{campaign_id}/minus-phrases", response_class=HTMLResponse)
async def minus_phrases_page(
    request: Request,
    campaign_id: int,
    db: Session = Depends(get_db),
    wb_client: WBPromotionClient = Depends(get_wb_client_for_user)
):
    """
    Страница управления минус-фразами кампании
    """
    from . import main
    
    try:
        # Получаем список кампаний для навигации
        campaigns = wb_client.get_campaigns()
        campaign = next((c for c in campaigns if c.id == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Кампания не найдена")
        
        # Получаем список товаров в кампании
        adverts = wb_client.get_adverts(ids=str(campaign_id))
        
        # Получаем минус-фразы для товаров
        nm_list = []
        if adverts and hasattr(adverts, 'adverts') and adverts.adverts:
            for advert in adverts.adverts:
                nm_id = getattr(advert, 'nm_id', None)
                if nm_id:
                    # Получаем минус-фразы для товара
                    minus_request = [{
                        "advert_id": campaign_id,
                        "nm_id": nm_id
                    }]
                    minus_data = wb_client.get_minus_phrases(minus_request)
                    
                    nm_list.append({
                        "nm_id": nm_id,
                        "minus_phrases": minus_data.items if hasattr(minus_data, 'items') else []
                    })
        
    except Exception as e:
        return main.templates.get_template("error.html").render(
            request=request,
            error_message=f"Ошибка загрузки: {str(e)}"
        )
    
    return main.templates.get_template("minus-phrases.html").render(
        request=request,
        campaign=campaign,
        nm_list=nm_list
    )
