"""
Тесты для Wildberries Promotion API Manager
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from wb_promotion_app.main import app
from wb_promotion_app.api_client import WBPromotionClient

client = TestClient(app)

# Мокируем ответы API для тестирования
mock_campaigns_response = [
    {
        "id": 123456,
        "name": "Тестовая кампания",
        "status": "active",
        "type": "search"
    }
]

mock_search_cluster_bids_response = {
    "bids": [
        {
            "advert_id": 123456,
            "bid": 700,
            "nm_id": 983512347,
            "norm_query": "Фраза 1"
        }
    ]
}

mock_search_cluster_stats_response = {
    "stats": [
        {
            "advert_id": 123456,
            "nm_id": 983512347,
            "stats": [
                {
                    "atbs": 68,
                    "avg_pos": 3.6,
                    "clicks": 2090,
                    "cpc": 471,
                    "cpm": 813,
                    "ctr": 107.23,
                    "norm_query": "Фраза 1",
                    "orders": 19,
                    "views": 1949
                }
            ]
        }
    ]
}


def test_root_endpoint():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Wildberries Promotion API Manager"}


def test_campaigns_list_requires_token():
    """Тест что /api/campaigns/list требует токен"""
    response = client.get("/api/campaigns/list")
    assert response.status_code == 401
    assert "X-API-Token" in response.json()["detail"]


@patch.object(WBPromotionClient, 'get_campaigns')
def test_campaigns_list_with_token(mock_get_campaigns):
    """Тест получения списка кампаний с токеном"""
    mock_get_campaigns.return_value = mock_campaigns_response

    response = client.get(
        "/api/campaigns/list",
        headers={"X-API-Token": "test_token"}
    )
    assert response.status_code == 200
    assert response.json() == mock_campaigns_response


@patch.object(WBPromotionClient, 'get_campaigns')
def test_get_campaigns(mock_get_campaigns):
    """Тест получения списка кампаний"""
    mock_get_campaigns.return_value = mock_campaigns_response

    response = client.get("/api/campaigns/list")
    assert response.status_code == 200
    assert response.json() == mock_campaigns_response


@patch.object(WBPromotionClient, 'get_search_cluster_bids')
def test_get_search_cluster_bids(mock_get_bids):
    """Тест получения ставок поисковых кластеров"""
    mock_get_bids.return_value = mock_search_cluster_bids_response
    
    payload = [
        {
            "advert_id": 123456,
            "nm_id": 983512347,
            "norm_query": "Фраза 1",
            "bid": 1000
        }
    ]
    
    response = client.post("/search-clusters/bids", json=payload)
    assert response.status_code == 200
    assert response.json() == mock_search_cluster_bids_response


@patch.object(WBPromotionClient, 'set_search_cluster_bids')
def test_set_search_cluster_bids(mock_set_bids):
    """Тест установки ставок для поисковых кластеров"""
    mock_response = {"result": "success"}
    mock_set_bids.return_value = mock_response
    
    payload = [
        {
            "advert_id": 123456,
            "nm_id": 983512347,
            "norm_query": "Фраза 1",
            "bid": 1000
        }
    ]
    
    response = client.post("/search-clusters/set-bids", json=payload)
    assert response.status_code == 200
    assert response.json() == mock_response


@patch.object(WBPromotionClient, 'get_search_cluster_stats')
def test_get_search_cluster_stats(mock_get_stats):
    """Тест получения статистики поисковых кластеров"""
    mock_get_stats.return_value = mock_search_cluster_stats_response
    
    payload = {
        "from_date": "2023-01-01",
        "to_date": "2023-01-31",
        "items": [
            {
                "advert_id": 123456,
                "nm_id": 983512347,
                "norm_query": "Фраза 1",
                "bid": 1000
            }
        ]
    }
    
    response = client.post("/search-clusters/stats", json=payload)
    assert response.status_code == 200
    assert response.json() == mock_search_cluster_stats_response


@patch.object(WBPromotionClient, 'get_minus_phrases')
def test_get_minus_phrases(mock_get_minus_phrases):
    """Тест получения минус-фраз"""
    mock_response = {"items": []}
    mock_get_minus_phrases.return_value = mock_response
    
    payload = [
        {
            "advert_id": 123456,
            "nm_id": 983512347
        }
    ]
    
    response = client.post("/search-clusters/minus-phrases", json=payload)
    assert response.status_code == 200
    assert response.json() == mock_response


@patch.object(WBPromotionClient, 'set_minus_phrases')
def test_set_minus_phrases(mock_set_minus_phrases):
    """Тест установки минус-фраз"""
    mock_response = {"result": "success"}
    mock_set_minus_phrases.return_value = mock_response
    
    payload = {
        "advert_id": 123456,
        "nm_id": 983512347,
        "norm_queries": ["минус-фраза"]
    }
    
    response = client.post("/search-clusters/set-minus-phrases", json=payload)
    assert response.status_code == 200
    assert response.json() == mock_response


@patch.object(WBPromotionClient, 'get_search_cluster_list')
def test_get_search_cluster_list(mock_get_cluster_list):
    """Тест получения списка поисковых кластеров"""
    mock_response = {"items": []}
    mock_get_cluster_list.return_value = mock_response
    
    payload = [
        {
            "advert_id": 123456,
            "nm_id": 983512347
        }
    ]
    
    response = client.post("/search-clusters/list", json=payload)
    assert response.status_code == 200
    assert response.json() == mock_response