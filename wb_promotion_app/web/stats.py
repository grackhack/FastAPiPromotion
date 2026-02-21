"""
Web роуты для страниц статистики
SSR рендеринг страниц
"""
from typing import Any
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..config import get_db
from ..auth import get_current_user_from_session, get_user_api_token
from ..api_client import WBPromotionClient
from ..services.stats_service import StatsService


router = APIRouter(tags=["Web Stats"])


async def get_wb_client_for_user(request: Request, db: Session = Depends(get_db)) -> Any:
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


@router.get("/stats/campaign/{campaign_id}")
async def campaign_stats_page(
    request: Request,
    campaign_id: int,
    wb_client: Any = Depends(get_wb_client_for_user)
):
    """Страница статистики рекламной кампании"""
    from ..main import templates

    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if not from_date or not to_date:
        to = datetime.now()
        from_date = (to - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = to.strftime("%Y-%m-%d")

    stats_service = StatsService(wb_client)

    try:
        stats = stats_service.get_campaign_stats(campaign_id, from_date, to_date)
        norm_stats = stats_service.get_norm_query_stats(
            campaign_id, nm_id=0, from_date=from_date, to_date=to_date
        )
        campaigns = wb_client.get_campaigns()
        campaign = next((c for c in campaigns if c.id == campaign_id), None)

        if not campaign:
            raise HTTPException(status_code=404, detail="Кампания не найдена")

    except Exception as e:
        return HTMLResponse(f"Ошибка: {str(e)}", status_code=500)

    template = templates.get_template("stats-campaign.html")
    return HTMLResponse(template.render(
        request=request,
        campaign=campaign,
        stats=stats,
        queries=norm_stats.get("queries", [])[:20],
        from_date=from_date,
        to_date=to_date
    ))


@router.get("/campaigns/{campaign_id}/minus-phrases")
async def minus_phrases_page(
    request: Request,
    campaign_id: int,
    wb_client: Any = Depends(get_wb_client_for_user)
):
    """Страница управления минус-фразами кампании"""
    from ..main import templates

    try:
        campaigns = wb_client.get_campaigns()
        campaign = next((c for c in campaigns if c.id == campaign_id), None)

        if not campaign:
            raise HTTPException(status_code=404, detail="Кампания не найдена")

        adverts = wb_client.get_adverts(ids=str(campaign_id))

        nm_list = []
        if adverts and hasattr(adverts, 'adverts') and adverts.adverts:
            for advert in adverts.adverts:
                nm_id = getattr(advert, 'nm_id', None)
                if nm_id:
                    minus_request = [{"advert_id": campaign_id, "nm_id": nm_id}]
                    minus_data = wb_client.get_minus_phrases(minus_request)

                    nm_list.append({
                        "nm_id": nm_id,
                        "minus_phrases": minus_data.items if hasattr(minus_data, 'items') else []
                    })

    except Exception as e:
        return HTMLResponse(f"Ошибка: {str(e)}", status_code=500)

    template = templates.get_template("minus-phrases.html")
    return HTMLResponse(template.render(
        request=request,
        campaign=campaign,
        nm_list=nm_list
    ))
