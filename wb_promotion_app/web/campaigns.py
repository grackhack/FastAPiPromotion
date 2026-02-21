"""
Web endpoints для кампаний (SSR)
Загружают данные на бэкенде и рендерят шаблоны
"""
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional

from ..core.dependencies import require_auth, get_wb_client, get_current_user, get_wb_client_optional
from ..models import User
from ..services.wb_service import WBService

# Кастомный JSON encoder для datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        from datetime import datetime, date
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

router = APIRouter(tags=["Web"])


@router.get("/", response_class=HTMLResponse, response_model=None)
async def campaigns_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    wb: Optional[WBService] = Depends(get_wb_client)
):
    """Главная страница - список кампаний"""
    from ..main import templates

    campaigns = []
    media_campaigns = []
    error = None

    # Если пользователь авторизован и есть токен - загружаем кампании
    if user and wb:
        try:
            campaigns = wb.get_campaigns()
        except Exception as e:
            error = f"Кампании: {str(e)}"
        
        try:
            media_campaigns = wb.get_media_campaigns()
        except Exception as e:
            # Медиакампании могут быть недоступны - не показываем ошибку
            media_campaigns = []
            # Логируем ошибку но не показываем пользователю
            import logging
            logging.warning(f"Media campaigns unavailable: {str(e)}")

    template = templates.get_template("index.html")
    return template.render(
        request=request,
        user=user,
        is_authenticated=user is not None,
        campaigns_json=json.dumps(campaigns, cls=DateTimeEncoder) if campaigns else '[]',
        media_campaigns_json=json.dumps(media_campaigns, cls=DateTimeEncoder) if media_campaigns else '[]',
        error=error
    )


@router.get("/campaigns", response_class=HTMLResponse, response_model=None)
async def all_campaigns_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    wb: Optional[WBService] = Depends(get_wb_client)
):
    """Страница всех кампаний"""
    from ..main import templates

    campaigns = []
    media_campaigns = []
    error = None

    if user and wb:
        try:
            campaigns = wb.get_campaigns()
            media_campaigns = wb.get_media_campaigns()
        except Exception as e:
            error = str(e)

    template = templates.get_template("campaigns.html")
    return template.render(
        request=request,
        user=user,
        is_authenticated=user is not None,
        campaigns=campaigns,
        media_campaigns=media_campaigns,
        error=error
    )


@router.get("/campaign/{campaign_id}", response_class=HTMLResponse, response_model=None)
async def campaign_detail_page(
    request: Request,
    campaign_id: int,
    user: Optional[User] = Depends(get_current_user),
    wb: Optional[WBService] = Depends(get_wb_client_optional)
):
    """Страница кампании"""
    from ..main import templates, DEBUG
    import logging
    
    logger = logging.getLogger(__name__)
    
    campaign = None
    error = None
    debug_info = {}

    # Если нет авторизации или токена - показываем ошибку
    if not user or not wb:
        error = "Необходимо войти и добавить WB API токен"
        debug_info = {
            "user": user is not None,
            "wb": wb is not None,
            "user_id": user.id if user else None,
            "campaign_id": campaign_id
        }
        logger.warning(f"Campaign {campaign_id}: user={user is not None}, wb={wb is not None}")
    else:
        try:
            logger.info(f"Campaign {campaign_id}: Загрузка кампании...")
            campaigns = wb.get_campaigns(ids=str(campaign_id))
            logger.info(f"Campaign {campaign_id}: Найдено кампаний: {len(campaigns)}")
            
            debug_info = {
                "user_id": user.id,
                "campaign_id": campaign_id,
                "campaigns_found": len(campaigns),
                "campaign_ids": [c.get("id") for c in campaigns] if campaigns else []
            }
            
            campaign = campaigns[0] if campaigns else None

            if not campaign:
                error = "Кампания не найдена"
                logger.warning(f"Campaign {campaign_id}: Кампания не найдена")
        except Exception as e:
            error = str(e)
            debug_info = {
                "user_id": user.id,
                "campaign_id": campaign_id,
                "exception": str(e),
                "exception_type": type(e).__name__
            }
            logger.exception(f"Campaign {campaign_id} error: {e}")

    template = templates.get_template("campaign-detail.html")
    return template.render(
        request=request,
        user=user,
        campaign_json=json.dumps(campaign, cls=DateTimeEncoder) if campaign else '{}',
        campaign_id=campaign_id,
        campaign_data=campaign if campaign else {},
        error=error,
        debug_info=debug_info if DEBUG else None
    )
