"""
Web endpoints для кампаний (SSR)
Загружают данные на бэкенде и рендерят шаблоны
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional

from ..core.dependencies import require_auth, get_wb_client, get_current_user
from ..models import User
from ..services.wb_service import WBService

router = APIRouter(tags=["Web"])


@router.get("/", response_class=HTMLResponse)
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
            media_campaigns = wb.get_media_campaigns()
        except Exception as e:
            error = str(e)

    template = templates.get_template("index.html")
    return template.render(
        request=request,
        user=user,
        is_authenticated=user is not None,
        campaigns=campaigns,
        media_campaigns=media_campaigns,
        error=error
    )


@router.get("/campaigns", response_class=HTMLResponse)
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


@router.get("/campaign/{campaign_id}", response_class=HTMLResponse)
async def campaign_detail_page(
    request: Request,
    campaign_id: int,
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    """Страница кампании"""
    from ..main import templates

    campaign = None
    error = None

    try:
        campaigns = wb.get_campaigns(ids=str(campaign_id))
        campaign = campaigns[0] if campaigns else None

        if not campaign:
            error = "Кампания не найдена"
    except Exception as e:
        error = str(e)

    template = templates.get_template("campaign-detail.html")
    return template.render(
        request=request,
        user=user,
        campaign=campaign,
        campaign_id=campaign_id,
        error=error
    )
