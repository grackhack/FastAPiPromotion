"""
API endpoints для кампаний
Все endpoints требуют авторизации и токена
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import date

from ..core.dependencies import require_auth, get_wb_client
from ..models import User
from ..services.wb_service import WBService

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/campaigns")
async def get_campaigns(
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client),
    ids: Optional[str] = Query(None, description="ID кампаний через запятую")
):
    """Получить список кампаний"""
    return wb.get_campaigns(ids=ids)


@router.get("/campaigns/media")
async def get_media_campaigns(
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client),
    status: Optional[int] = Query(None),
    type: Optional[int] = Query(None)
):
    """Получить список медиакампаний"""
    return wb.get_media_campaigns(status=status, type=type)


@router.post("/stats/normquery")
async def get_stats(
    from_date: date,
    to_date: date,
    items: List[dict],
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    """Получить статистику по фразам"""
    return wb.get_stats(from_date=from_date, to_date=to_date, items=items)


@router.post("/stats/full")
async def get_full_stats(
    ids: List[int],
    from_date: date,
    to_date: date,
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    """Получить полную статистику по кампаниям"""
    return wb.get_full_stats(ids=ids, from_date=from_date, to_date=to_date)


@router.post("/search-clusters/minus-phrases")
async def get_minus_phrases(
    items: List[dict],
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    """Получить минус-фразы для товаров"""
    try:
        results = []
        for item in items:
            phrases = wb.get_minus_phrases(
                advert_id=item["advert_id"],
                nm_id=item["nm_id"]
            )
            results.append({
                "advert_id": item["advert_id"],
                "nm_id": item["nm_id"],
                "norm_queries": phrases
            })
        return {"items": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-clusters/set-minus-phrases")
async def set_minus_phrases(
    advert_id: int,
    nm_id: int,
    norm_queries: List[str],
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    """Установить минус-фразы для товара"""
    try:
        return wb.set_minus_phrases(advert_id, nm_id, norm_queries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-clusters/list")
async def get_search_clusters(
    items: List[dict],
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    """Получить активные и неактивные кластеры"""
    try:
        results = []
        for item in items:
            clusters = wb.get_search_clusters(
                advert_id=item["advert_id"],
                nm_id=item["nm_id"]
            )
            results.append({
                "advert_id": item["advert_id"],
                "nm_id": item["nm_id"],
                **clusters
            })
        return {"items": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
