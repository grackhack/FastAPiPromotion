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
    from ..services.wb_service import WBService
    from ..auth import get_current_user_from_session

    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if not from_date or not to_date:
        to = datetime.now()
        from_date = (to - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = to.strftime("%Y-%m-%d")

    stats_service = StatsService(wb_client)
    wb_service = WBService(wb_client)

    try:
        # Получаем nm_id из кампании через get_adverts
        adverts = wb_client.get_adverts(ids=str(campaign_id))

        nm_ids = []
        if adverts and hasattr(adverts, 'adverts') and adverts.adverts:
            advert = adverts.adverts[0]
            if advert.nm_settings:
                nm_ids = [nm.nm_id for nm in advert.nm_settings]

        # Получаем статистику для первого nm_id
        nm_id = nm_ids[0] if nm_ids else 0
        stats = stats_service.get_campaign_stats(campaign_id, from_date, to_date, nm_id=nm_id)
        norm_stats = stats_service.get_norm_query_stats(
            campaign_id, nm_id=nm_id, from_date=from_date, to_date=to_date
        )

        # Получаем все минус-фразы для всех товаров кампании
        all_minus_phrases = set()
        for nid in nm_ids:
            phrases = wb_service.get_minus_phrases(campaign_id, nid)
            all_minus_phrases.update(phrases)

        # Получаем информацию о кампании для отображения
        campaigns = wb_client.get_campaigns()
        campaign = next((c for c in campaigns if c.get('id') == campaign_id), None)

        # Получаем текущего пользователя
        user = await get_current_user_from_session(request)

    except Exception as e:
        return HTMLResponse(f"Ошибка: {str(e)}", status_code=500)

    template = templates.get_template("stats-campaign.html")
    return HTMLResponse(template.render(
        request=request,
        user=user,
        is_authenticated=user is not None,
        current_page='stats',
        campaign=campaign,
        stats=stats,
        queries=norm_stats.get("queries", [])[:20],
        from_date=from_date,
        to_date=to_date,
        minus_phrases=list(all_minus_phrases),
        campaign_id=campaign_id,
        nm_id=nm_id
    ))


@router.get("/campaigns/{campaign_id}/minus-phrases")
async def minus_phrases_page(
    request: Request,
    campaign_id: int,
    wb_client: Any = Depends(get_wb_client_for_user)
):
    """Страница управления минус-фразами кампании"""
    from ..main import templates
    from ..services.wb_service import WBService
    from ..auth import get_current_user_from_session

    try:
        # Получаем данные о кампании напрямую из API
        adverts = wb_client.get_adverts(ids=str(campaign_id))

        # Создаём WBService для работы с методами
        wb_service = WBService(wb_client)

        nm_list = []
        if adverts and hasattr(adverts, 'adverts') and adverts.adverts:
            advert = adverts.adverts[0]
            # Получаем все nm_id из кампании
            for nm_setting in advert.nm_settings:
                nm_id = nm_setting.nm_id

                # Получаем минус-фразы через WBService
                phrases = wb_service.get_minus_phrases(campaign_id, nm_id)

                nm_list.append({
                    "nm_id": nm_id,
                    "minus_phrases": phrases
                })

        # Получаем текущего пользователя
        user = await get_current_user_from_session(request)

    except Exception as e:
        return HTMLResponse(f"Ошибка: {str(e)}", status_code=500)

    template = templates.get_template("minus-phrases.html")
    return HTMLResponse(template.render(
        request=request,
        user=user,
        is_authenticated=user is not None,
        current_page='minus_phrases',
        campaign={"id": campaign_id},
        nm_list=nm_list
    ))
