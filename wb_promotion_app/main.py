from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from api_client import WBPromotionClient
from schemas import (
    CampaignInfo,
    SearchClusterBid,
    SearchClusterStats,
    MinusPhraseRequest as MinusPhraseSchema,
    SearchClusterListResponse
)
from utils import setup_logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="Wildberries Promotion API Manager",
    description="API для управления рекламными кампаниями Wildberries, включая работу с поисковыми кластерами",
    version="1.0.0"
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="./wb_promotion_app/static"), name="static")

# Настройка Jinja2 для шаблонов
templates = Environment(
    loader=FileSystemLoader("./wb_promotion_app/templates"),
    autoescape=True
)

# Инициализация клиента API
token = os.getenv("WB_API_TOKEN")
if not token:
    raise ValueError("Необходимо указать WB_API_TOKEN в переменных окружения")

wb_client = WBPromotionClient(token)


@app.get("/campaigns", response_model=List[CampaignInfo])
async def get_campaigns():
    """
    Получить список рекламных кампаний
    """
    try:
        campaigns = wb_client.get_campaigns()
        return campaigns
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
        result = wb_client.set_minus_phrases(
            request.advert_id, 
            request.nm_id, 
            request.norm_queries
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