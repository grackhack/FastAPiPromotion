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
        # nm_id=0 означает все товары в кампании
        items = [{
            "advert_id": campaign_id,
            "nm_id": nm_id or 0
        }]
        
        # Получаем статистику через get_normquery_stats
        stats = self.client.get_normquery_stats(
            from_date=from_date,
            to_date=to_date,
            items=items
        )
        
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
        # Используем get_normquery_stats для получения детальной статистики
        items = [{
            "advert_id": campaign_id,
            "nm_id": nm_id
        }]
        
        stats = self.client.get_normquery_stats(
            from_date=from_date,
            to_date=to_date,
            items=items
        )
        return self._process_norm_stats(stats)

    def _get_safe_value(self, obj, attr, default=0):
        """Безопасное получение значения с обработкой Undefined"""
        val = getattr(obj, attr, default)
        # Проверяем на Undefined (pydantic)
        if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'UndefinedType'):
            return default
        return val

    def _process_stats(self, stats: Any, campaign_id: int) -> Dict[str, Any]:
        """
        Обработать статистику по поисковым запросам (normquery stats).
        API возвращает: {"stats": [{"advert_id": X, "nm_id": Y, "stats": [norm_query_stats...]}]}
        
        Поля API:
        - views: Показы
        - clicks: Клики
        - orders: Заказы
        - atbs: Добавления в корзину
        - cpc: Стоимость клика (копейки)
        - cpm: Стоимость 1000 показов (копейки)
        - ctr: CTR (%)
        - avg_pos: Средняя позиция
        - norm_query: Поисковый запрос
        - sum: Выручка (копейки) - если есть
        - shks: Количество штук - если есть
        - spend: Затраты (копейки) - если есть
        """
        stats_list = stats.get("stats") if isinstance(stats, dict) else None

        if not stats_list:
            return {
                "campaign_id": campaign_id,
                "total_views": 0,
                "total_clicks": 0,
                "total_orders": 0,
                "total_revenue": 0,
                "total_atbs": 0,
                "total_spend": 0,
                "ctr": 0,
                "cpc": 0,
                "cpm": 0,
                "avg_pos": 0,
                "days": []
            }

        # Агрегируем данные по всем поисковым запросам
        total_views = 0
        total_clicks = 0
        total_orders = 0
        total_revenue = 0
        total_atbs = 0
        total_spend = 0
        total_cpc = 0
        total_cpm = 0
        total_avg_pos = 0
        days_data = []  # Для normquery stats это будут запросы

        for item in stats_list:
            item_stats = item.get("stats") if isinstance(item, dict) else getattr(item, 'stats', [])
            if item_stats:
                for stat in item_stats:
                    if isinstance(stat, dict):
                        # Это статистика по поисковому запросу
                        views = stat.get('views', 0)
                        clicks = stat.get('clicks', 0)
                        orders = stat.get('orders', 0)
                        atbs = stat.get('atbs', 0)
                        cpc = stat.get('cpc', 0)
                        cpm = stat.get('cpm', 0)
                        ctr = stat.get('ctr', 0)
                        avg_pos = stat.get('avg_pos', 0)
                        revenue = stat.get('sum', 0) or stat.get('revenue', 0)
                        spend = stat.get('spend', 0)
                        shks = stat.get('shks', 0)
                        
                        total_views += views
                        total_clicks += clicks
                        total_orders += orders
                        total_atbs += atbs
                        total_revenue += revenue
                        total_spend += spend
                        total_cpc += cpc
                        total_cpm += cpm
                        total_avg_pos += avg_pos
                        
                        # Добавляем запрос в days_data (для совместимости с шаблоном)
                        days_data.append({
                            "query": stat.get('norm_query', 'N/A'),
                            "views": views,
                            "clicks": clicks,
                            "orders": orders,
                            "atbs": atbs,
                            "revenue": revenue,
                            "spend": spend,
                            "shks": shks,
                            "ctr": ctr,
                            "cpc": cpc,
                            "cpm": cpm,
                            "avg_pos": avg_pos,
                        })
                    else:
                        # Pydantic модель
                        views = self._get_safe_value(stat, 'views', 0)
                        clicks = self._get_safe_value(stat, 'clicks', 0)
                        orders = self._get_safe_value(stat, 'orders', 0)
                        atbs = self._get_safe_value(stat, 'atbs', 0)
                        cpc = self._get_safe_value(stat, 'cpc', 0)
                        cpm = self._get_safe_value(stat, 'cpm', 0)
                        ctr = self._get_safe_value(stat, 'ctr', 0)
                        avg_pos = self._get_safe_value(stat, 'avg_pos', 0)
                        revenue = self._get_safe_value(stat, 'sum', 0) or self._get_safe_value(stat, 'revenue', 0)
                        spend = self._get_safe_value(stat, 'spend', 0)
                        shks = self._get_safe_value(stat, 'shks', 0)
                        
                        total_views += views
                        total_clicks += clicks
                        total_orders += orders
                        total_atbs += atbs
                        total_revenue += revenue
                        total_spend += spend
                        total_cpc += cpc
                        total_cpm += cpm
                        total_avg_pos += avg_pos
                        
                        days_data.append({
                            "query": self._get_safe_value(stat, 'norm_query', 'N/A'),
                            "views": views,
                            "clicks": clicks,
                            "orders": orders,
                            "atbs": atbs,
                            "revenue": revenue,
                            "spend": spend,
                            "shks": shks,
                            "ctr": ctr,
                            "cpc": cpc,
                            "cpm": cpm,
                            "avg_pos": avg_pos,
                        })

        # Считаем средние значения
        count = len(days_data) if days_data else 1
        avg_cpc = round(total_cpc / count, 2)
        avg_cpm = round(total_cpm / count, 2)
        avg_avg_pos = round(total_avg_pos / count, 2)
        ctr = round((total_clicks / total_views * 100) if total_views > 0 else 0, 2)
        cpc = round(total_spend / total_clicks if total_clicks > 0 else 0, 2)

        return {
            "campaign_id": campaign_id,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_atbs": total_atbs,
            "total_spend": total_spend,
            "total_shks": 0,  # Агрегация штук не имеет смысла
            "ctr": ctr,
            "cpc": cpc,
            "cpm": avg_cpm,
            "avg_pos": avg_avg_pos,
            "days": days_data
        }

    def _process_full_stats(self, stats: Any, campaign_id: int) -> Dict[str, Any]:
        """Обработать полную статистику"""
        # Аналогично _process_stats но с дополнительной группировкой
        return self._process_stats(stats, campaign_id)

    def _process_norm_stats(self, stats: Any) -> Dict[str, Any]:
        """Обработать статистику по запросам"""
        # API возвращает dict: {"stats": [{"advert_id": X, "nm_id": Y, "stats": [...]}]}
        stats_list = stats.get("stats") if isinstance(stats, dict) else None
        
        if not stats_list:
            return {"queries": []}

        queries = []
        for item in stats_list:
            item_stats = item.get("stats") if isinstance(item, dict) else getattr(item, 'stats', [])
            if item_stats:
                for stat in item_stats:
                    if isinstance(stat, dict):
                        query_data = {
                            "query": stat.get('norm_query', 'N/A'),
                            "views": stat.get('views', 0),
                            "clicks": stat.get('clicks', 0),
                            "orders": stat.get('orders', 0),
                            "ctr": stat.get('ctr', 0),
                        }
                    else:
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
