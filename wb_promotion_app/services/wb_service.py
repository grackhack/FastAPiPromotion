"""
WB API Service
Инкапсулирует работу с Wildberries API
"""
from typing import List, Dict, Any, Optional
from datetime import date

from ..api_client import WBPromotionClient


class WBService:
    """Сервис для работы с WB API"""
    
    def __init__(self, client: WBPromotionClient):
        self.client = client
    
    def get_campaigns(self, ids: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить список кампаний"""
        try:
            adverts = self.client.get_adverts(ids=ids)
            return [self._to_dict(advert) for advert in adverts.adverts]
        except Exception as e:
            raise Exception(f"Ошибка загрузки кампаний: {str(e)}")
    
    def get_media_campaigns(
        self,
        status: Optional[int] = None,
        type: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Получить список медиакампаний"""
        try:
            campaigns = self.client.get_media_campaigns(status=status, type=type)
            return [self._to_dict(c) for c in campaigns]
        except Exception as e:
            raise Exception(f"Ошибка загрузки медиакампаний: {str(e)}")
    
    def get_stats(
        self,
        from_date: date,
        to_date: date,
        items: List[Dict[str, int]]
    ) -> Dict[str, Any]:
        """Получить статистику по фразам"""
        try:
            return self.client.get_normquery_stats(
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
                items=items
            )
        except Exception as e:
            raise Exception(f"Ошибка загрузки статистики: {str(e)}")
    
    def get_full_stats(
        self,
        ids: List[int],
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """Получить полную статистику"""
        try:
            return self.client.get_full_stats(
                ids=ids,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat()
            )
        except Exception as e:
            raise Exception(f"Ошибка загрузки полной статистики: {str(e)}")
    
    def get_minus_phrases(
        self,
        advert_id: int,
        nm_id: int
    ) -> List[str]:
        """Получить минус-фразы для товара"""
        try:
            # Создаём объект запроса
            from ..schemas import MinusPhraseRequest
            request_item = MinusPhraseRequest(advert_id=advert_id, nm_id=nm_id)
            
            result = self.client.get_minus_phrases([request_item])

            # Извлекаем фразы из ответа
            phrases = []
            if isinstance(result, dict):
                for item in result.get('items', []):
                    if isinstance(item, dict):
                        if item.get('advert_id') == advert_id and item.get('nm_id') == nm_id:
                            phrases = item.get('norm_queries', []) or item.get('excluded', [])
                            break
                    else:
                        if getattr(item, 'advert_id', None) == advert_id and getattr(item, 'nm_id', None) == nm_id:
                            phrases = getattr(item, 'norm_queries', []) or getattr(item, 'excluded', [])
                            break

            return phrases
        except Exception as e:
            raise Exception(f"Ошибка загрузки минус-фраз: {str(e)}")
    
    def set_minus_phrases(
        self,
        advert_id: int,
        nm_id: int,
        phrases: List[str]
    ) -> Dict[str, Any]:
        """Установить минус-фразы для товара"""
        try:
            return self.client.set_minus_phrases(advert_id, nm_id, phrases)
        except Exception as e:
            raise Exception(f"Ошибка установки минус-фраз: {str(e)}")

    def get_search_cluster_list(
        self,
        advert_id: int,
        nm_id: int
    ) -> Dict[str, Any]:
        """Получить списки активных и неактивных поисковых кластеров"""
        try:
            result = self.client.get_search_cluster_list(advert_id, nm_id)
            
            # Извлекаем списки из ответа
            clusters = {
                "active": [],
                "excluded": []
            }
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        if item.get('advert_id') == advert_id and item.get('nm_id') == nm_id:
                            clusters["active"] = item.get('active', [])
                            clusters["excluded"] = item.get('excluded', [])
                            break
                    else:
                        if getattr(item, 'advert_id', None) == advert_id and getattr(item, 'nm_id', None) == nm_id:
                            clusters["active"] = getattr(item, 'active', [])
                            clusters["excluded"] = getattr(item, 'excluded', [])
                            break
            
            return clusters
        except Exception as e:
            raise Exception(f"Ошибка загрузки списков кластеров: {str(e)}")
    
    def get_search_clusters(
        self,
        advert_id: int,
        nm_id: int
    ) -> Dict[str, List[str]]:
        """Получить активные и неактивные кластеры"""
        try:
            return self.client.get_search_cluster_list([{
                "advert_id": advert_id,
                "nm_id": nm_id
            }])
        except Exception as e:
            raise Exception(f"Ошибка загрузки кластеров: {str(e)}")
    
    def _to_dict(self, obj) -> Dict[str, Any]:
        """Конвертирует объект в JSON-сериализуемый dict"""
        import json
        from datetime import datetime, date
        
        if obj is None:
            return None
        
        # Обработка datetime/date
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Pydantic v2 с mode='json' для вложенных моделей
        if hasattr(obj, 'model_dump'):
            try:
                return obj.model_dump(mode='json')
            except (TypeError, AttributeError):
                # Если mode='json' не работает, пробуем обычный
                return obj.model_dump()
        
        # Pydantic v1
        if hasattr(obj, 'dict'):
            return obj.dict()
        
        # Dataclass
        if hasattr(obj, '__dataclass_fields__'):
            from dataclasses import asdict
            try:
                return asdict(obj)
            except (TypeError, AttributeError):
                pass
        
        # Обычный объект
        if hasattr(obj, '__dict__'):
            return {k: self._to_dict(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
        
        # Список
        if isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        
        # Dict
        if isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        
        # Базовые типы
        return obj
