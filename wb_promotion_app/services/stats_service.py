"""
Сервис для работы со статистикой рекламных кампаний
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from ..api_client import WBPromotionClient
from ..schemas import (
    StatsRequest,
    StatsItemResponse,
    FullStatsRequest,
    FullStatsResponse,
)


class StatsService:
    """Сервис для получения и обработки статистики"""

    def __init__(self, wb_client: WBPromotionClient):
        self.client = wb_client

    def get_campaign_stats(
        self,
        campaign_id: int,
        from_date: str,
        to_date: str,
        nm_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Получить статистику по кампании
        
        Args:
            campaign_id: ID кампании
            from_date: Дата начала (YYYY-MM-DD)
            to_date: Дата окончания (YYYY-MM-DD)
            nm_id: ID товара (опционально)
            
        Returns:
            Словарь со статистикой
        """
        # Формируем запрос к API
        request = StatsRequest(
            from_date=from_date,
            to_date=to_date,
            items=[{
                "advert_id": campaign_id,
                "nm_id": nm_id
            }] if nm_id else [{"advert_id": campaign_id}]
        )
        
        # Получаем статистику
        stats = self.client.get_stats(request)
        
        return self._process_stats(stats, campaign_id)

    def get_full_stats(
        self,
        campaign_id: int,
        from_date: str,
        to_date: str
    ) -> Dict[str, Any]:
        """
        Получить полную статистику по кампании с группировкой
        
        Args:
            campaign_id: ID кампании
            from_date: Дата начала (YYYY-MM-DD)
            to_date: Дата окончания (YYYY-MM-DD)
            
        Returns:
            Словарь с полной статистикой
        """
        request = FullStatsRequest(
            from_date=from_date,
            to_date=to_date,
            items=[{"advert_id": campaign_id}]
        )
        
        stats = self.client.get_full_stats(request)
        return self._process_full_stats(stats, campaign_id)

    def get_norm_query_stats(
        self,
        campaign_id: int,
        nm_id: int,
        from_date: str,
        to_date: str
    ) -> Dict[str, Any]:
        """
        Получить статистику по нормализованным запросам
        
        Args:
            campaign_id: ID кампании
            nm_id: ID товара
            from_date: Дата начала
            to_date: Дата окончания
            
        Returns:
            Статистика по запросам
        """
        # Используем get_stats для получения детальной статистики
        request = StatsRequest(
            from_date=from_date,
            to_date=to_date,
            items=[{
                "advert_id": campaign_id,
                "nm_id": nm_id
            }]
        )
        
        stats = self.client.get_stats(request)
        return self._process_norm_stats(stats)

    def _get_safe_value(self, obj, attr, default=0):
        """Безопасное получение значения с обработкой Undefined"""
        val = getattr(obj, attr, default)
        # Проверяем на Undefined (pydantic)
        if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'UndefinedType'):
            return default
        return val

    def _process_stats(self, stats: Any, campaign_id: int) -> Dict[str, Any]:
        """Обработать статистику"""
        if not stats or not hasattr(stats, 'items') or not stats.items:
            return {
                "campaign_id": campaign_id,
                "total_views": 0,
                "total_clicks": 0,
                "total_orders": 0,
                "total_revenue": 0,
                "ctr": 0,
                "cpc": 0,
                "days": []
            }
        
        # Агрегируем данные по дням
        days_data = []
        total_views = 0
        total_clicks = 0
        total_orders = 0
        total_revenue = 0
        
        for item in stats.items:
            if hasattr(item, 'stats') and item.stats:
                for stat in item.stats:
                    day_data = {
                        "date": self._get_safe_value(stat, 'date', 'N/A'),
                        "views": self._get_safe_value(stat, 'views', 0),
                        "clicks": self._get_safe_value(stat, 'clicks', 0),
                        "orders": self._get_safe_value(stat, 'orders', 0),
                        "revenue": self._get_safe_value(stat, 'revenue', 0),
                        "ctr": self._get_safe_value(stat, 'ctr', 0),
                        "cpc": self._get_safe_value(stat, 'cpc', 0),
                    }
                    days_data.append(day_data)
                    total_views += day_data["views"]
                    total_clicks += day_data["clicks"]
                    total_orders += day_data["orders"]
                    total_revenue += day_data["revenue"]
        
        # Считаем средние значения
        ctr = round((total_clicks / total_views * 100) if total_views > 0 else 0, 2)
        cpc = round(total_revenue / total_clicks if total_clicks > 0 else 0, 2)
        
        return {
            "campaign_id": campaign_id,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "ctr": ctr,
            "cpc": cpc,
            "days": days_data
        }

    def _process_full_stats(self, stats: Any, campaign_id: int) -> Dict[str, Any]:
        """Обработать полную статистику"""
        # Аналогично _process_stats но с дополнительной группировкой
        return self._process_stats(stats, campaign_id)

    def _process_norm_stats(self, stats: Any) -> Dict[str, Any]:
        """Обработать статистику по запросам"""
        if not stats or not hasattr(stats, 'items') or not stats.items:
            return {"queries": []}
        
        queries = []
        for item in stats.items:
            if hasattr(item, 'stats') and item.stats:
                for stat in item.stats:
                    query_data = {
                        "query": self._get_safe_value(stat, 'norm_query', 'N/A'),
                        "views": self._get_safe_value(stat, 'views', 0),
                        "clicks": self._get_safe_value(stat, 'clicks', 0),
                        "orders": self._get_safe_value(stat, 'orders', 0),
                        "ctr": self._get_safe_value(stat, 'ctr', 0),
                    }
                    queries.append(query_data)
        
        # Сортируем по просмотрам
        queries.sort(key=lambda x: x["views"], reverse=True)
        
        return {"queries": queries}
