from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from .api_client import WBPromotionClient
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
)
from .utils import setup_logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="Wildberries Promotion API Manager",
    description="API для управления рекламными кампаниями Wildberries, включая работу с поисковыми кластерами",
    version="1.0.0"
)

# Получаем директорию текущего модуля
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Настройка Jinja2 для шаблонов
templates = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")),
    autoescape=True
)

# Инициализация клиента API
token = os.getenv("WB_API_TOKEN")
if not token:
    raise ValueError("Необходимо указать WB_API_TOKEN в переменных окружения")

wb_client = WBPromotionClient(token)


@app.get("/api/campaigns/list", response_model=List[CampaignInfo])
async def get_campaigns():
    """
    Получить список рекламных кампаний (API)
    """
    try:
        campaigns = wb_client.get_campaigns()
        return campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/count", response_model=CampaignCountResponseSchema)
async def get_campaigns_count():
    """
    Получить список всех рекламных кампаний продавца с их ID.
    Кампании сгруппированы по типу и статусу.
    
    Эндпоинт: GET /adv/v1/promotion/count
    """
    try:
        result = wb_client.get_campaigns_count()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/adverts", response_model=List[PromotionCampaignSchema])
async def get_adverts(
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
    try:
        result = wb_client.get_adverts(ids=ids, statuses=statuses, payment_type=payment_type)
        return result.adverts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/media", response_model=List[MediaCampaignSchema])
async def get_media_campaigns(
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
    try:
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
async def get_media_campaigns_count():
    """
    Получить количество медиакампаний продавца с группировкой по статусам.
    
    Эндпоинт: GET /adv/v1/count
    """
    try:
        result = wb_client.get_media_campaigns_count()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/bids")
async def get_search_cluster_bids(request: List[SearchClusterBid]):
    """
    Получить ставки поисковых кластеров для указанных товаров в кампаниях
    """
    try:
        bids = wb_client.get_search_cluster_bids(request)
        return bids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/set-bids")
async def set_search_cluster_bids(request: List[SearchClusterBid]):
    """
    Установить ставки для поисковых кластеров
    """
    try:
        result = wb_client.set_search_cluster_bids(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/search-clusters/remove-bids")
async def remove_search_cluster_bids(request: List[SearchClusterBid]):
    """
    Удалить ставки с поисковых кластеров
    """
    try:
        result = wb_client.remove_search_cluster_bids(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/stats")
async def get_search_cluster_stats(request: SearchClusterStats):
    """
    Получить статистику по поисковым кластерам за указанный период
    """
    try:
        stats = wb_client.get_search_cluster_stats(
            request.from_date, 
            request.to_date, 
            request.items
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/minus-phrases")
async def get_minus_phrases(request: List[MinusPhraseSchema]):
    """
    Получить список минус-фраз для товаров в кампаниях
    """
    try:
        minus_phrases = wb_client.get_minus_phrases(request)
        return minus_phrases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/set-minus-phrases")
async def set_minus_phrases(request: MinusPhraseSchema):
    """
    Установить минус-фразы для товара в кампании
    """
    try:
        # Используем norm_queries или minus_phrases
        phrases = request.norm_queries or request.minus_phrases or []
        result = wb_client.set_minus_phrases(
            request.advert_id,
            request.nm_id,
            phrases
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-clusters/list")
async def get_search_cluster_list(request: List[MinusPhraseSchema]):
    """
    Получить списки активных и неактивных поисковых кластеров
    """
    try:
        cluster_list = wb_client.get_search_cluster_list(request)
        return cluster_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stats/normquery", response_model=StatsResponse)
async def get_normquery_stats(request: StatsRequest):
    """
    Получить статистику поисковых кластеров (ключевых фраз) за период
    """
    try:
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
async def get_full_stats(request: FullStatsRequest):
    """
    Получить полную статистику по кампаниям за период
    """
    try:
        data = wb_client.get_full_stats(
            ids=request.ids,
            from_date=request.from_date.isoformat(),
            to_date=request.to_date.isoformat()
        )
        
        # Преобразуем ответ API в нашу схему
        campaigns = []
        if "advert" in data:
            for camp in data["advert"]:
                items = []
                total_views = 0
                total_clicks = 0
                total_orders = 0
                total_revenue = 0
                
                if "nmStats" in camp:
                    for nm in camp["nmStats"]:
                        nm_total_views = sum(d.get("views", 0) for d in nm.get("stats", []))
                        nm_total_clicks = sum(d.get("clicks", 0) for d in nm.get("stats", []))
                        nm_total_orders = sum(d.get("orders", 0) for d in nm.get("stats", []))
                        nm_total_revenue = sum(d.get("revenue", 0) for d in nm.get("stats", []))
                        
                        items.append(FullStatsItem(
                            nm_id=nm.get("nmId", 0),
                            subject=nm.get("subjectName", ""),
                            total_views=nm_total_views,
                            total_clicks=nm_total_clicks,
                            total_orders=nm_total_orders,
                            total_revenue=nm_total_revenue
                        ))
                        total_views += nm_total_views
                        total_clicks += nm_total_clicks
                        total_orders += nm_total_orders
                        total_revenue += nm_total_revenue
                
                campaigns.append(FullStatsCampaign(
                    id=camp.get("advertId", 0),
                    name=camp.get("name", ""),
                    items=items,
                    total_views=total_views,
                    total_clicks=total_clicks,
                    total_orders=total_orders,
                    total_revenue=total_revenue
                ))
        
        return FullStatsResponse(campaigns=campaigns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Главная страница веб-интерфейса
    """
    template = templates.get_template("index.html")
    return template.render(request=request)


@app.get("/phrases", response_class=HTMLResponse)
async def phrases_page(request: Request):
    """
    Страница управления минус-фразами
    """
    template = templates.get_template("phrases.html")
    return template.render(request=request)


@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    """
    Страница просмотра всех рекламных кампаний
    """
    template = templates.get_template("campaigns.html")
    return template.render(request=request)


@app.get("/campaign/{campaign_id}", response_class=HTMLResponse)
async def campaign_detail_page(request: Request, campaign_id: int):
    """
    Страница настройки кампании (минус-слова)
    """
    template = templates.get_template("campaign-detail.html")
    return template.render(request=request, campaign_id=campaign_id)