import requests
from typing import List, Dict, Any, Optional
import logging
from .utils import handle_api_error, RateLimitError
from .models import (
    Campaign,
    SearchClusterBidItem,
    AdvertListItem,
    CampaignGroup,
    CampaignCountResponse,
    PromotionCampaign,
    PromotionAdvertsResponse,
    MediaCampaign,
    MediaCampaignCountResponse,
    MediaCampaignCountItem,
    BidSettings,
    NMSettingItem,
    CampaignSettings,
    Placements,
    CampaignTimestamps,
)
from .schemas import SearchClusterBid, MinusPhraseRequest
from datetime import datetime


class WBPromotionClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://advert-api.wildberries.ru"
        self.media_base_url = "https://advert-media-api.wildberries.ru"
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

    def get_campaigns_count(self) -> CampaignCountResponse:
        """
        Получить список всех рекламных кампаний продавца с их ID.
        Кампании сгруппированы по типу и статусу.
        
        Эндпоинт: GET /adv/v1/promotion/count
        
        Возвращает:
            CampaignCountResponse - объект с группами кампаний и общим количеством
        """
        try:
            endpoint = "/adv/v1/promotion/count"
            data = self._make_request("GET", endpoint)
            
            # Преобразуем данные в модели
            advert_groups = []
            for group in data.get("adverts", []):
                advert_list = []
                for item in group.get("advert_list", []):
                    change_time_str = item["changeTime"].replace("Z", "+00:00")
                    # Fix for Python 3.9: handle various ISO formats
                    try:
                        change_time = datetime.fromisoformat(change_time_str)
                    except ValueError:
                        import re
                        match = re.match(r'(.+T\d+:\d+:\d+)\.(\d+)([+-]\d+:\d+)', change_time_str)
                        if match:
                            base, micro, tz = match.groups()
                            micro = micro.ljust(6, '0')[:6]
                            change_time_str = f"{base}.{micro}{tz}"
                        change_time = datetime.fromisoformat(change_time_str)
                    advert_list.append(AdvertListItem(advertId=item["advertId"], changeTime=change_time))
                advert_groups.append(
                    CampaignGroup(
                        type=group["type"],
                        status=group["status"],
                        count=group["count"],
                        advert_list=advert_list
                    )
                )
            
            return CampaignCountResponse(
                adverts=advert_groups,
                all=data.get("all", 0)
            )
        except Exception as e:
            self.logger.error(f"Error in get_campaigns_count: {str(e)}")
            raise

    def get_adverts(
        self,
        ids: Optional[str] = None,
        statuses: Optional[str] = None,
        payment_type: Optional[str] = None
    ) -> PromotionAdvertsResponse:
        """
        Получить подробную информацию о рекламных кампаниях с единой или ручной ставкой.
        
        Эндпоинт: GET /api/advert/v2/adverts
        
        Параметры:
            ids - ID кампаний через запятую (максимум 50)
            statuses - Статусы кампаний через запятую (-1, 4, 7, 8, 9, 11)
            payment_type - Тип оплаты: cpm или cpc
            
        Возвращает:
            PromotionAdvertsResponse - список кампаний с подробной информацией
        """
        try:
            endpoint = "/api/advert/v2/adverts"
            params = {}
            if ids:
                params["ids"] = ids
            if statuses:
                params["statuses"] = statuses
            if payment_type:
                params["payment_type"] = payment_type
            
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Преобразуем данные в модели
            adverts = []
            for camp in data.get("adverts", []):
                nm_settings = []
                for nm in camp.get("nm_settings", []):
                    bids = nm.get("bids_kopecks", {})
                    nm_settings.append(
                        NMSettingItem(
                            bids_kopecks=BidSettings(
                                recommendations=bids.get("recommendations", 0),
                                search=bids.get("search", 0)
                            ),
                            nm_id=nm["nm_id"],
                            subject=nm.get("subject", {})
                        )
                    )
                
                settings_data = camp.get("settings", {})
                placements_data = settings_data.get("placements", {})
                
                timestamps_data = camp.get("timestamps", {})

                def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
                    if not ts_str:
                        return None
                    # Fix for Python 3.9: handle various ISO formats
                    ts_str = ts_str.replace("Z", "+00:00")
                    # Handle format like '2024-10-28T22:49:16.38403+03:00' (5 digit microseconds)
                    try:
                        return datetime.fromisoformat(ts_str)
                    except ValueError:
                        # Try to fix microseconds format (pad to 6 digits)
                        import re
                        match = re.match(r'(.+T\d+:\d+:\d+)\.(\d+)([+-]\d+:\d+)', ts_str)
                        if match:
                            base, micro, tz = match.groups()
                            micro = micro.ljust(6, '0')[:6]  # Pad or truncate to 6 digits
                            ts_str = f"{base}.{micro}{tz}"
                        return datetime.fromisoformat(ts_str)
                
                adverts.append(
                    PromotionCampaign(
                        bid_type=camp.get("bid_type", "unknown"),
                        id=camp["id"],
                        nm_settings=nm_settings,
                        settings=CampaignSettings(
                            name=settings_data.get("name", ""),
                            payment_type=settings_data.get("payment_type", ""),
                            placements=Placements(
                                recommendations=placements_data.get("recommendations", False),
                                search=placements_data.get("search", False)
                            )
                        ),
                        status=camp.get("status", 0),
                        timestamps=CampaignTimestamps(
                            created=parse_timestamp(timestamps_data.get("created")),
                            deleted=parse_timestamp(timestamps_data.get("deleted")),
                            started=parse_timestamp(timestamps_data.get("started")),
                            updated=parse_timestamp(timestamps_data.get("updated"))
                        )
                    )
                )
            
            return PromotionAdvertsResponse(adverts=adverts)
        except Exception as e:
            self.logger.error(f"Error in get_adverts: {str(e)}")
            raise

    def get_media_campaigns(
        self,
        status: Optional[int] = None,
        type: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
        direction: Optional[str] = None
    ) -> List[MediaCampaign]:
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

        Возвращает:
            List[MediaCampaign] - список медиакампаний
        """
        try:
            endpoint = "/adv/v1/adverts"
            params = {}
            if status is not None:
                params["status"] = status
            if type is not None:
                params["type"] = type
            if limit is not None:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset
            if order:
                params["order"] = order
            if direction:
                params["direction"] = direction

            url = f"{self.media_base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Преобразуем данные в модели
            campaigns = []
            for camp in data:
                create_time_str = camp["createTime"].replace("Z", "+00:00")
                # Fix for Python 3.9: handle various ISO formats
                try:
                    create_time = datetime.fromisoformat(create_time_str)
                except ValueError:
                    import re
                    match = re.match(r'(.+T\d+:\d+:\d+)\.(\d+)([+-]\d+:\d+)', create_time_str)
                    if match:
                        base, micro, tz = match.groups()
                        micro = micro.ljust(6, '0')[:6]
                        create_time_str = f"{base}.{micro}{tz}"
                    create_time = datetime.fromisoformat(create_time_str)
                campaigns.append(
                    MediaCampaign(
                        advertId=camp["advertId"],
                        name=camp["name"],
                        brand=camp["brand"],
                        type=camp["type"],
                        status=camp["status"],
                        createTime=create_time
                    )
                )
            
            return campaigns
        except Exception as e:
            self.logger.error(f"Error in get_media_campaigns: {str(e)}")
            raise

    def get_media_campaigns_count(self) -> MediaCampaignCountResponse:
        """
        Получить количество медиакампаний продавца с группировкой по статусам.

        Эндпоинт: GET /adv/v1/count

        Возвращает:
            MediaCampaignCountResponse - объект с количеством кампаний
        """
        try:
            endpoint = "/adv/v1/count"
            url = f"{self.media_base_url}{endpoint}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            advert_list = []
            for item in data.get("adverts", []):
                advert_list.append(
                    MediaCampaignCountItem(
                        type=item["type"],
                        status=item["status"],
                        count=item["count"]
                    )
                )
            
            return MediaCampaignCountResponse(
                all=data.get("all", 0),
                adverts=advert_list
            )
        except Exception as e:
            self.logger.error(f"Error in get_media_campaigns_count: {str(e)}")
            raise

    def get_campaigns(self) -> List[Dict[str, Any]]:
        """
        Получить список всех рекламных кампаний (комбинированный метод).
        
        Сначала получает список ID кампаний через get_campaigns_count(),
        затем получает подробную информацию через get_adverts().
        
        Возвращает:
            List[Dict[str, Any]] - список кампаний с подробной информацией
        """
        try:
            # Шаг 1: Получаем список всех кампаний с ID
            count_response = self.get_campaigns_count()
            
            # Собираем все ID кампаний
            all_ids = []
            for group in count_response.adverts:
                for advert_item in group.advert_list:
                    all_ids.append(str(advert_item.advertId))
            
            if not all_ids:
                return []
            
            # Шаг 2: Получаем подробную информацию о кампаниях (максимум 50 ID за запрос)
            all_adverts = []
            batch_size = 50
            for i in range(0, len(all_ids), batch_size):
                ids_batch = ",".join(all_ids[i:i + batch_size])
                adverts_response = self.get_adverts(ids=ids_batch)
                all_adverts.extend(adverts_response.adverts)
            
            # Преобразуем в список словарей для обратной совместимости
            result = []
            for advert in all_adverts:
                result.append({
                    "id": advert.id,
                    "name": advert.settings.name,
                    "status": advert.status,
                    "bid_type": advert.bid_type,
                    "payment_type": advert.settings.payment_type,
                    "created": advert.timestamps.created.isoformat() if advert.timestamps.created else None,
                    "started": advert.timestamps.started.isoformat() if advert.timestamps.started else None,
                    "nm_count": len(advert.nm_settings)
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error in get_campaigns: {str(e)}")
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

            # Проверяем статус ответа
            if response.status_code != 200:
                error_msg = ""
                try:
                    # Пытаемся распарсить JSON ошибку
                    if response.text:
                        error_data = response.json()
                        error_msg = error_data.get('detail', str(error_data))
                    else:
                        error_msg = f"HTTP {response.status_code}"
                except Exception as json_err:
                    # Если не JSON, используем текст ответа
                    error_msg = response.text or f"HTTP {response.status_code} ({str(json_err)})"
                
                self.logger.error(f"API error response: {response.status_code} - {response.text[:200] if response.text else 'empty'}")
                raise Exception(f"Ошибка API: {error_msg}")

            # Проверяем, есть ли тело ответа
            if not response.text:
                # Пустой ответ - это успех (HTTP 200)
                return {"success": True, "message": "Минус-фразы успешно установлены"}
            
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

    def get_normquery_stats(self, from_date: str, to_date: str, items: List[Dict[str, int]]) -> Dict[str, Any]:
        """
        Получить статистику поисковых кластеров (ключевых фраз)
        
        Args:
            from_date: Дата начала периода (YYYY-MM-DD)
            to_date: Дата окончания периода (YYYY-MM-DD)
            items: Список словарей с advert_id и nm_id
        """
        try:
            url = f"{self.base_url}/adv/v0/normquery/stats"
            payload = {
                "from": from_date,
                "to": to_date,
                "items": [
                    {
                        "advert_id": item["advert_id"],
                        "nm_id": item["nm_id"]
                    } for item in items
                ]
            }
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                raise Exception(f"Ошибка API: {error_msg}")
            
            return response.json()
        except Exception as e:
            error_context = "get_normquery_stats"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def get_normquery_daily_stats(
        self,
        advert_id: int,
        nm_id: int,
        from_date: str,
        to_date: str
    ) -> Dict[str, Any]:
        """
        Получить статистику по фразам по дням (API /adv/v1/normquery/stats)

        Args:
            advert_id: ID кампании
            nm_id: ID товара
            from_date: Дата начала периода (YYYY-MM-DD)
            to_date: Дата окончания периода (YYYY-MM-DD)
        """
        try:
            url = f"{self.base_url}/adv/v1/normquery/stats"
            
            # Формируем payload согласно документации WB API
            payload = {
                "from": from_date,
                "to": to_date,
                "items": [
                    {
                        "advertId": advert_id,
                        "nmId": nm_id
                    }
                ]
            }
            
            # Логируем для отладки
            self.logger.info(f"get_normquery_daily_stats: url={url}, payload={payload}")
            
            response = requests.post(url, json=payload, headers=self.headers)
            
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response body: {response.text[:500]}")

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                raise Exception(f"Ошибка API: {error_msg}")

            return response.json()
        except Exception as e:
            error_context = "get_normquery_daily_stats"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise

    def get_full_stats(self, ids: List[int], from_date: str, to_date: str, nm_id: int = None) -> Dict[str, Any]:
        """
        Получить полную статистику по кампаниям

        Args:
            ids: Список ID кампаний
            from_date: Дата начала периода (YYYY-MM-DD)
            to_date: Дата окончания периода (YYYY-MM-DD)
            nm_id: ID товара (опционально, для фильтрации по конкретному товару)
        """
        try:
            url = f"{self.base_url}/adv/v3/fullstats"
            params = {
                "ids": ",".join(map(str, ids)),
                "beginDate": from_date,
                "endDate": to_date
            }
            
            # Добавляем фильтрацию по товару если указан nm_id
            if nm_id:
                params["nmId"] = nm_id
            
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"

                # Проверка на лимитирование запросов
                if "Limited by global limiter" in error_msg or "per seller" in error_msg:
                    raise RateLimitError(f"Превышен лимит запросов к API: {error_msg}")

                raise Exception(f"Ошибка API: {error_msg}")

            return response.json()
        except RateLimitError:
            raise
        except Exception as e:
            error_context = "get_full_stats"
            self.logger.error(f"Error in {error_context}: {str(e)}")
            raise