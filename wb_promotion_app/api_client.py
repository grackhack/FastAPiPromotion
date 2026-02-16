import requests
from typing import List, Dict, Any, Optional
import logging
from utils import handle_api_error
from models import Campaign, SearchClusterBidItem
from schemas import SearchClusterBid, MinusPhraseRequest


class WBPromotionClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://advert-api.wildberries.ru"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Внутренний метод для выполнения HTTP-запросов к API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=payload, headers=self.headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=payload, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Проверяем статус код
            if response.status_code != 200:
                self.logger.error(f"API request failed with status {response.status_code}: {response.text}")
                response.raise_for_status()
                
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_campaigns(self) -> List[Dict[str, Any]]:
        """
        Получить список рекламных кампаний
        """
        try:
            # В документации не указан точный эндпоинт для получения списка кампаний
            # Используем предполагаемый эндпоинт, который может отличаться
            url = f"{self.base_url}/adv/v0/campaigns/list"
            response = requests.get(url, headers=self.headers)
            
            # Если статус 200 OK, возвращаем результат
            if response.status_code == 200:
                return response.json()
            # Если статус 404, возможно, эндпоинт другой
            elif response.status_code == 404:
                # Пробуем альтернативный эндпоинт
                alt_url = f"{self.base_url}/adv/v1/campaigns/list"
                alt_response = requests.get(alt_url, headers=self.headers)
                alt_response.raise_for_status()
                return alt_response.json()
            else:
                response.raise_for_status()
        except Exception as e:
            error_context = "get_campaigns"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def get_search_cluster_bids(self, items: List[SearchClusterBid]) -> Dict[str, Any]:
        """
        Получить ставки поисковых кластеров для указанных товаров в кампаниях
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/get-bids"
            payload = {
                "items": [
                    {
                        "advert_id": item.advert_id,
                        "nm_id": item.nm_id
                    } for item in items
                ]
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "get_search_cluster_bids"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def set_search_cluster_bids(self, bids: List[SearchClusterBid]) -> Dict[str, Any]:
        """
        Установить ставки для поисковых кластеров
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/bids"
            payload = {
                "bids": [
                    {
                        "advert_id": bid.advert_id,
                        "nm_id": bid.nm_id,
                        "norm_query": bid.norm_query,
                        "bid": bid.bid
                    } for bid in bids
                ]
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "set_search_cluster_bids"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def remove_search_cluster_bids(self, bids: List[SearchClusterBid]) -> Dict[str, Any]:
        """
        Удалить ставки с поисковых кластеров
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/bids"
            payload = {
                "bids": [
                    {
                        "advert_id": bid.advert_id,
                        "nm_id": bid.nm_id,
                        "norm_query": bid.norm_query,
                        "bid": bid.bid
                    } for bid in bids
                ]
            }
            response = requests.delete(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "remove_search_cluster_bids"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def get_search_cluster_stats(self, from_date: str, to_date: str, items: List[SearchClusterBid]) -> Dict[str, Any]:
        """
        Получить статистику по поисковым кластерам за указанный период
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/stats"
            payload = {
                "from": from_date,
                "to": to_date,
                "items": [
                    {
                        "advert_id": item.advert_id,
                        "nm_id": item.nm_id
                    } for item in items
                ]
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "get_search_cluster_stats"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def get_minus_phrases(self, items: List[MinusPhraseRequest]) -> Dict[str, Any]:
        """
        Получить список минус-фраз для товаров в кампаниях
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/get-minus"
            payload = {
                "items": [
                    {
                        "advert_id": item.advert_id,
                        "nm_id": item.nm_id
                    } for item in items
                ]
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "get_minus_phrases"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def set_minus_phrases(self, advert_id: int, nm_id: int, norm_queries: List[str]) -> Dict[str, Any]:
        """
        Установить минус-фразы для товара в кампании
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/set-minus"
            payload = {
                "advert_id": advert_id,
                "nm_id": nm_id,
                "norm_queries": norm_queries
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "set_minus_phrases"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def get_search_cluster_list(self, items: List[MinusPhraseRequest]) -> Dict[str, Any]:
        """
        Получить списки активных и неактивных поисковых кластеров
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/list"
            payload = {
                "items": [
                    {
                        "advertId": item.advert_id,
                        "nmId": item.nm_id
                    } for item in items
                ]
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_context = "get_search_cluster_list"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise