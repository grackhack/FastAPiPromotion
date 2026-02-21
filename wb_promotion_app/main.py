from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from .api_client import WBPromotionClient, RateLimitError
from .schemas import (
    CampaignInfo,
    SearchClusterBid,
    SearchClusterStats,
    MinusPhraseRequest as MinusPhraseSchema,
    SearchClusterListResponse,
    CampaignCountResponseSchema,
    PromotionAdvertsResponseSchema,
    PromotionCampaignSchema,
    MediaCampaignSchema,
    MediaCampaignCountResponseSchema,
    GetAdvertsRequestSchema,
    GetMediaCampaignsRequestSchema,
    StatsRequest,
    StatsResponse,
    StatsItemResponse,
    StatsPhrase,
    FullStatsRequest,
    FullStatsResponse,
    FullStatsItem,
    FullStatsCampaign,
    FullStatsDay,
    FullStatsApp,
    FullStatsNM,
)
from .utils import setup_logging
from .dependencies import CurrentUser, get_token_from_header
from .config import get_db
from .users import router as users_router

# Загрузка переменных окружения
load_dotenv()

# Режим отладки
DEBUG = os.getenv("APP_DEBUG", "False").lower() == "true"

# Настройка логирования
setup_logging("DEBUG" if DEBUG else os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="Wildberries Promotion API Manager",
    description="API для управления рекламными кампаниями Wildberries, включая работу с поисковыми кластерами",
    debug=DEBUG  # Включает отладочную информацию
)

# Получаем директорию текущего модуля
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Middleware для логирования ошибок
@app.middleware("http")
async def log_errors(request: Request, call_next):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            logger.error(f"500 error for {request.url.path}")
        return response
    except Exception as e:
        logger.exception(f"Exception in {request.url.path}: {str(e)}")
        raise

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Настройка Jinja2 для шаблонов
templates = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")),
    autoescape=True
)

# Экспортируем templates для использования в других модулях
__all__ = ["app", "templates"]

# Подключение роутера пользователей
app.include_router(users_router, prefix="/api")

# Подключение веб-роутов аутентификации (страницы и API)
from .web_auth import router as web_auth_router
app.include_router(web_auth_router)  # Без префикса для веб-страниц

# Подключение новых API endpoints (без токенов - берут из сессии)
from .api.campaigns import router as api_campaigns_router
app.include_router(api_campaigns_router)

# Подключение новых Web endpoints (SSR) - должны быть ПОСЛЕ api роутов
from .web.campaigns import router as web_campaigns_router
app.include_router(web_campaigns_router)

# Подключение Web endpoints для статистики
# from .web.stats import router as web_stats_router
# app.include_router(web_stats_router)


# Старые API endpoints (для обратной совместимости, будут удалены)
def get_wb_client(token: str) -> WBPromotionClient:
    """Создать клиент API для токена пользователя"""
    return WBPromotionClient(token)


@app.get("/api/campaigns/list", response_model=List[CampaignInfo])
async def get_campaigns(token: str = Depends(get_token_from_header)):
    """
    Получить список рекламных кампаний (API)
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        campaigns = wb_client.get_campaigns()
        return campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/count", response_model=CampaignCountResponseSchema)
async def get_campaigns_count(token: str = Depends(get_token_from_header)):
    """
    Получить список всех рекламных кампаний продавца с их ID.
    Кампании сгруппированы по типу и статусу.

    Эндпоинт: GET /adv/v1/promotion/count
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        result = wb_client.get_campaigns_count()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/adverts", response_model=List[PromotionCampaignSchema])
async def get_adverts(
    token: str = Depends(get_token_from_header),
    ids: Optional[str] = None,
    statuses: Optional[str] = None,
    payment_type: Optional[str] = None
):
    """
    Получить подробную информацию о рекламных кампаниях с единой или ручной ставкой.

    Эндпоинт: GET /api/advert/v2/adverts

    Параметры:
        ids - ID кампаний через запятую (максимум 50)
        statuses - Статусы кампаний через запятую (-1, 4, 7, 8, 9, 11)
        payment_type - Тип оплаты: cpm или cpc
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        result = wb_client.get_adverts(ids=ids, statuses=statuses, payment_type=payment_type)
        return result.adverts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/media", response_model=List[MediaCampaignSchema])
async def get_media_campaigns(
    token: str = Depends(get_token_from_header),
    status: Optional[int] = None,
    type: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order: Optional[str] = None,
    direction: Optional[str] = None
):
    """
    Получить список всех медиакампаний продавца по типам и статусам.

    Эндпоинт: GET /adv/v1/adverts

    Параметры:
        status - Статус медиакампании (1-11)
        type - Тип медиакампании: 1 — размещение по дням, 2 — по просмотрам
        limit - Количество кампаний в ответе
        offset - Смещение относительно первой кампании
        order - Порядок сортировки: create или id
        direction - Направление: desc или asc
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        result = wb_client.get_media_campaigns(
            status=status,
            type=type,
            limit=limit,
            offset=offset,
            order=order,
            direction=direction
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/media/count", response_model=MediaCampaignCountResponseSchema)
async def get_media_campaigns_count(token: str = Depends(get_token_from_header)):
    """
    Получить количество медиакампаний продавца с группировкой по статусам.

    Эндпоинт: GET /adv/v1/count
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        result = wb_client.get_media_campaigns_count()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/bids")
async def get_search_cluster_bids(request: List[SearchClusterBid], token: str = Depends(get_token_from_header)):
    """
    Получить ставки поисковых кластеров для указанных товаров в кампаниях
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        bids = wb_client.get_search_cluster_bids(request)
        return bids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/set-bids")
async def set_search_cluster_bids(request: List[SearchClusterBid], token: str = Depends(get_token_from_header)):
    """
    Установить ставки для поисковых кластеров
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        result = wb_client.set_search_cluster_bids(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/search-clusters/remove-bids")
async def remove_search_cluster_bids(request: List[SearchClusterBid], token: str = Depends(get_token_from_header)):
    """
    Удалить ставки с поисковых кластеров
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        result = wb_client.remove_search_cluster_bids(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/stats")
async def get_search_cluster_stats(request: SearchClusterStats, token: str = Depends(get_token_from_header)):
    """
    Получить статистику по поисковым кластерам за указанный период
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        stats = wb_client.get_search_cluster_stats(
            request.from_date,
            request.to_date,
            request.items
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/minus-phrases")
async def get_minus_phrases(request: List[MinusPhraseSchema], token: str = Depends(get_token_from_header)):
    """
    Получить список минус-фраз для товаров в кампаниях
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        minus_phrases = wb_client.get_minus_phrases(request)
        return minus_phrases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/set-minus-phrases")
async def set_minus_phrases(request: MinusPhraseSchema, token: str = Depends(get_token_from_header)):
    """
    Установить минус-фразы для товара в кампании
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        # Используем norm_queries или minus_phrases
        phrases = request.norm_queries or request.minus_phrases or []
        wb_client = get_wb_client(token)
        result = wb_client.set_minus_phrases(
            request.advert_id,
            request.nm_id,
            phrases
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/list")
async def get_search_cluster_list(request: List[MinusPhraseSchema], token: str = Depends(get_token_from_header)):
    """
    Получить списки активных и неактивных поисковых кластеров
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        cluster_list = wb_client.get_search_cluster_list(request)
        return cluster_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stats/normquery", response_model=StatsResponse)
async def get_normquery_stats(request: StatsRequest, token: str = Depends(get_token_from_header)):
    """
    Получить статистику поисковых кластеров (ключевых фраз) за период
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        items = [{"advert_id": item.advert_id, "nm_id": item.nm_id} for item in request.items]
        data = wb_client.get_normquery_stats(
            from_date=request.from_date.isoformat(),
            to_date=request.to_date.isoformat(),
            items=items
        )

        print(f"API Response: {data}")  # Логирование для отладки

        # Преобразуем ответ API в нашу схему
        # API возвращает: {"stats": [{"advert_id": X, "nm_id": Y, "stats": [...]}]}
        result_items = []
        stats_list = data.get("stats") or []

        if stats_list:
            for item in stats_list:
                phrases = []
                # Вложенный массив stats содержит фразы
                phrase_list = item.get("stats") or []
                if phrase_list:
                    for nq in phrase_list:
                        phrases.append(StatsPhrase(
                            norm_query=nq.get("norm_query", ""),
                            views=nq.get("views", 0),
                            clicks=nq.get("clicks", 0),
                            orders=nq.get("orders", 0),
                            ctr=nq.get("ctr", 0),
                            cpc=nq.get("cpc", 0),
                            cpm=nq.get("cpm", 0),
                            avg_pos=nq.get("avg_pos", 0),
                            atbs=nq.get("atbs", 0),
                            revenue=nq.get("revenue", 0),
                            spend=nq.get("spend", 0)
                        ))

                result_items.append(StatsItemResponse(
                    advert_id=item.get("advert_id", 0),
                    nm_id=item.get("nm_id", 0),
                    phrases=phrases
                ))

        return StatsResponse(items=result_items)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stats/full", response_model=FullStatsResponse)
async def get_full_stats(request: FullStatsRequest, token: str = Depends(get_token_from_header)):
    """
    Получить полную статистику по кампаниям за период
    """
    if not token:
        raise HTTPException(status_code=401, detail="Требуется X-API-Token заголовок")
    try:
        wb_client = get_wb_client(token)
        data = wb_client.get_full_stats(
            ids=request.ids,
            from_date=request.from_date.isoformat(),
            to_date=request.to_date.isoformat()
        )

        # Преобразуем ответ API в нашу схему
        # API возвращает массив кампаний напрямую
        campaigns = []

        for camp in data:
            # Собираем уникальные nmId из всех дней и приложений для агрегации
            nm_stats = {}
            
            # Преобразуем дни
            days_parsed = []
            if "days" in camp:
                for day in camp["days"]:
                    apps_parsed = []
                    if "apps" in day:
                        for app in day["apps"]:
                            nms_parsed = []
                            if "nms" in app:
                                for nm in app["nms"]:
                                    nm_obj = FullStatsNM(
                                        nm_id=nm.get("nmId", 0),
                                        name=nm.get("name", ""),
                                        atbs=nm.get("atbs", 0),
                                        canceled=nm.get("canceled", 0),
                                        clicks=nm.get("clicks", 0),
                                        cpc=nm.get("cpc", 0),
                                        cr=nm.get("cr", 0),
                                        ctr=nm.get("ctr", 0),
                                        orders=nm.get("orders", 0),
                                        shks=nm.get("shks", 0),
                                        sum=nm.get("sum", 0),
                                        sum_price=nm.get("sum_price", 0),
                                        views=nm.get("views", 0)
                                    )
                                    nms_parsed.append(nm_obj)
                                    
                                    # Агрегация по nmId
                                    nm_id = nm.get("nmId", 0)
                                    if nm_id not in nm_stats:
                                        nm_stats[nm_id] = {
                                            "views": 0,
                                            "clicks": 0,
                                            "orders": 0,
                                            "revenue": 0,
                                            "cpc": 0,
                                            "cr": 0,
                                            "ctr": 0,
                                            "name": nm.get("name", "")
                                        }
                                    nm_stats[nm_id]["views"] += nm.get("views", 0)
                                    nm_stats[nm_id]["clicks"] += nm.get("clicks", 0)
                                    nm_stats[nm_id]["orders"] += nm.get("orders", 0)
                                    nm_stats[nm_id]["revenue"] += nm.get("sum", 0)
                                    nm_stats[nm_id]["cpc"] += nm.get("cpc", 0)
                                    nm_stats[nm_id]["cr"] += nm.get("cr", 0)
                                    nm_stats[nm_id]["ctr"] += nm.get("ctr", 0)
                            
                            app_obj = FullStatsApp(
                                app_type=app.get("appType", 0),
                                atbs=app.get("atbs", 0),
                                canceled=app.get("canceled", 0),
                                clicks=app.get("clicks", 0),
                                cpc=app.get("cpc", 0),
                                cr=app.get("cr", 0),
                                ctr=app.get("ctr", 0),
                                orders=app.get("orders", 0),
                                shks=app.get("shks", 0),
                                sum=app.get("sum", 0),
                                sum_price=app.get("sum_price", 0),
                                views=app.get("views", 0),
                                nms=nms_parsed
                            )
                            apps_parsed.append(app_obj)
                    
                    day_obj = FullStatsDay(
                        date=datetime.fromisoformat(day["date"].replace("Z", "+00:00")) if day.get("date") else datetime.now(),
                        atbs=day.get("atbs", 0),
                        canceled=day.get("canceled", 0),
                        clicks=day.get("clicks", 0),
                        cpc=day.get("cpc", 0),
                        cr=day.get("cr", 0),
                        ctr=day.get("ctr", 0),
                        orders=day.get("orders", 0),
                        shks=day.get("shks", 0),
                        sum=day.get("sum", 0),
                        sum_price=day.get("sum_price", 0),
                        views=day.get("views", 0),
                        apps=apps_parsed
                    )
                    days_parsed.append(day_obj)
            
            # Преобразуем агрегированные данные по товарам в список items
            items = []
            for nm_id, stats in nm_stats.items():
                items.append(FullStatsItem(
                    nm_id=nm_id,
                    subject=stats["name"],
                    total_views=stats["views"],
                    total_clicks=stats["clicks"],
                    total_orders=stats["orders"],
                    total_revenue=stats["revenue"],
                    total_cpc=round(stats["cpc"] / max(stats["views"], 1), 2) if stats["views"] > 0 else 0,
                    total_cr=round(stats["orders"] / max(stats["clicks"], 1) * 100, 2) if stats["clicks"] > 0 else 0,
                    total_ctr=round(stats["clicks"] / max(stats["views"], 1) * 100, 2) if stats["views"] > 0 else 0
                ))

            # Создаём объект кампании
            campaign = FullStatsCampaign(
                id=camp.get("advertId", 0),
                name=f"Кампания {camp.get('advertId', 0)}",
                items=items,
                days=days_parsed,
                total_views=camp.get("views", 0),
                total_clicks=camp.get("clicks", 0),
                total_orders=camp.get("orders", 0),
                total_revenue=camp.get("sum", 0),
                total_atbs=camp.get("atbs", 0),
                total_canceled=camp.get("canceled", 0),
                total_shks=camp.get("shks", 0),
                total_sum_price=camp.get("sum_price", 0),
                avg_cpc=camp.get("cpc", 0),
                avg_cr=camp.get("cr", 0),
                avg_ctr=camp.get("ctr", 0)
            )
            campaigns.append(campaign)

        return FullStatsResponse(campaigns=campaigns)
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse, response_model=None)
async def read_root(request: Request):
    """
    Главная страница веб-интерфейса
    """
    template = templates.get_template("index.html")
    return template.render(request=request)


@app.get("/phrases", response_class=HTMLResponse, response_model=None)
async def phrases_page(request: Request):
    """
    Страница управления минус-фразами
    """
    template = templates.get_template("phrases.html")
    return template.render(request=request)


@app.get("/campaigns", response_class=HTMLResponse, response_model=None)
async def campaigns_page(request: Request):
    """
    Страница просмотра всех рекламных кампаний
    """
    template = templates.get_template("campaigns.html")
    return template.render(request=request)


@app.get("/campaign/{campaign_id}", response_class=HTMLResponse, response_model=None)
async def campaign_detail_page(request: Request, campaign_id: int):
    """
    Страница настройки кампании (минус-слова)
    """
    template = templates.get_template("campaign-detail.html")
    return template.render(request=request, campaign_id=campaign_id)