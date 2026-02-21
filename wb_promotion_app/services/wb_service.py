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
            result = self.client.get_minus_phrases([{
                "advert_id": advert_id,
                "nm_id": nm_id
            }])
            
            # Извлекаем фразы из ответа
            phrases = []
            for item in result.get('items', []):
                if item.get('advert_id') == advert_id and item.get('nm_id') == nm_id:
                    phrases = item.get('norm_queries', []) or item.get('excluded', [])
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
        """Конвертирует объект в dict"""
        if hasattr(obj, 'model_dump'):
            return obj.model_dump(mode='json')
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return obj
