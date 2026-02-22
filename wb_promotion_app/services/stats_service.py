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
        to_date: str,
        nm_id: int = None
    ) -> Dict[str, Any]:
        """
        Получить полную статистику по кампании с группировкой

        Args:
            campaign_id: ID кампании
            from_date: Дата начала (YYYY-MM-DD)
            to_date: Дата окончания (YYYY-MM-DD)
            nm_id: ID товара (опционально, для фильтрации по товару)

        Returns:
            Словарь с полной статистикой
        """
        try:
            # Получаем статистику через API
            stats = self.client.get_full_stats(
                ids=[campaign_id],
                from_date=from_date,
                to_date=to_date,
                nm_id=nm_id
            )
            return self._process_full_stats(stats, campaign_id)
        except Exception as e:
            # Возвращаем пустую статистику при ошибке
            return {
                "campaign_id": campaign_id,
                "total_views": 0,
                "total_clicks": 0,
                "total_orders": 0,
                "total_atbs": 0,
                "total_shks": 0,
                "total_spend": 0,
                "ctr": 0,
                "cpc": 0,
                "cpm": 0,
                "avg_pos": 0,
                "days": []
            }

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
        
        Поля API (согласно документации):
        - norm_query: string - Поисковый кластер
        - views: integer - Количество просмотров
        - clicks: integer - Количество кликов
        - atbs: integer - Количество добавлений товаров в корзину
        - orders: integer - Количество заказов
        - ctr: number <double> - Кликабельность (%)
        - cpc: number <double> - Стоимость одного клика, ₽
        - cpm: number <double> - Средняя стоимость за тысячу показов, ₽
        - avg_pos: number <double> - Средняя позиция товара
        - shks: integer - Количество заказанных товаров, шт.
        - spend: number <double> - Затраты на продвижение, ₽
        """
        stats_list = stats.get("stats") if isinstance(stats, dict) else None

        if not stats_list:
            return {
                "campaign_id": campaign_id,
                "total_views": 0,
                "total_clicks": 0,
                "total_orders": 0,
                "total_atbs": 0,
                "total_shks": 0,
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
        total_atbs = 0
        total_shks = 0
        total_spend = 0
        total_cpc = 0
        total_cpm = 0
        total_avg_pos = 0
        days_data = []

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
                        shks = stat.get('shks', 0)
                        ctr = stat.get('ctr', 0)
                        cpc = stat.get('cpc', 0)  # Уже в рублях
                        cpm = stat.get('cpm', 0)  # Уже в рублях
                        avg_pos = stat.get('avg_pos', 0)
                        spend = stat.get('spend', 0)  # Уже в рублях
                        
                        total_views += views
                        total_clicks += clicks
                        total_orders += orders
                        total_atbs += atbs
                        total_shks += shks
                        total_spend += spend
                        total_cpc += cpc
                        total_cpm += cpm
                        total_avg_pos += avg_pos
                        
                        # Добавляем запрос в days_data
                        days_data.append({
                            "query": stat.get('norm_query', 'N/A'),
                            "views": views,
                            "clicks": clicks,
                            "orders": orders,
                            "atbs": atbs,
                            "shks": shks,
                            "ctr": ctr,
                            "cpc": cpc,
                            "cpm": cpm,
                            "avg_pos": avg_pos,
                            "spend": spend,
                        })
                    else:
                        # Pydantic модель
                        views = self._get_safe_value(stat, 'views', 0)
                        clicks = self._get_safe_value(stat, 'clicks', 0)
                        orders = self._get_safe_value(stat, 'orders', 0)
                        atbs = self._get_safe_value(stat, 'atbs', 0)
                        shks = self._get_safe_value(stat, 'shks', 0)
                        ctr = self._get_safe_value(stat, 'ctr', 0)
                        cpc = self._get_safe_value(stat, 'cpc', 0)
                        cpm = self._get_safe_value(stat, 'cpm', 0)
                        avg_pos = self._get_safe_value(stat, 'avg_pos', 0)
                        spend = self._get_safe_value(stat, 'spend', 0)
                        
                        total_views += views
                        total_clicks += clicks
                        total_orders += orders
                        total_atbs += atbs
                        total_shks += shks
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
                            "shks": shks,
                            "ctr": ctr,
                            "cpc": cpc,
                            "cpm": cpm,
                            "avg_pos": avg_pos,
                            "spend": spend,
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
            "total_atbs": total_atbs,
            "total_shks": total_shks,
            "total_spend": total_spend,
            "ctr": ctr,
            "cpc": cpc,
            "cpm": avg_cpm,
            "avg_pos": avg_avg_pos,
            "days": days_data
        }

    def _process_full_stats(self, stats: Any, campaign_id: int) -> Dict[str, Any]:
        """
        Обработать полную статистику из /adv/v3/fullstats
        
        API возвращает массив кампаний:
        [
            {
                "advertId": 123,
                "days": [
                    {
                        "date": "2024-01-01T...",
                        "apps": [
                            {
                                "appType": 1,
                                "nms": [
                                    {
                                        "nmId": 456,
                                        "name": "Товар",
                                        "views": 100,
                                        "clicks": 10,
                                        ...
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        """
        # API возвращает массив кампаний
        if not stats or not isinstance(stats, list) or len(stats) == 0:
            return {
                "campaign_id": campaign_id,
                "total_views": 0,
                "total_clicks": 0,
                "total_orders": 0,
                "total_atbs": 0,
                "total_shks": 0,
                "total_spend": 0,
                "ctr": 0,
                "cpc": 0,
                "cpm": 0,
                "avg_pos": 0,
                "days": []
            }
        
        # Берём первую кампанию (запрашивали одну)
        campaign = stats[0] if isinstance(stats, list) else stats
        
        # Агрегируем статистику по всем дням и товарам
        total_views = 0
        total_clicks = 0
        total_orders = 0
        total_atbs = 0
        total_shks = 0
        total_spend = 0
        total_cpc = 0
        total_cpm = 0
        total_avg_pos = 0
        days_data = []
        
        days = campaign.get("days", []) if isinstance(campaign, dict) else getattr(campaign, 'days', [])
        
        for day in days:
            if isinstance(day, dict):
                day_views = day.get('views', 0)
                day_clicks = day.get('clicks', 0)
                day_orders = day.get('orders', 0)
                day_atbs = day.get('atbs', 0)
                day_shks = day.get('shks', 0)
                day_sum = day.get('sum', 0)
                day_cpc = day.get('cpc', 0)
                day_cpm = day.get('cpm', 0)
                day_ctr = day.get('ctr', 0)
                day_avg_pos = day.get('avg_pos', 0)
            else:
                day_views = getattr(day, 'views', 0)
                day_clicks = getattr(day, 'clicks', 0)
                day_orders = getattr(day, 'orders', 0)
                day_atbs = getattr(day, 'atbs', 0)
                day_shks = getattr(day, 'shks', 0)
                day_sum = getattr(day, 'sum', 0)
                day_cpc = getattr(day, 'cpc', 0)
                day_cpm = getattr(day, 'cpm', 0)
                day_ctr = getattr(day, 'ctr', 0)
                day_avg_pos = getattr(day, 'avg_pos', 0)
            
            total_views += day_views
            total_clicks += day_clicks
            total_orders += day_orders
            total_atbs += day_atbs
            total_shks += day_shks
            total_spend += day_sum
            total_cpc += day_cpc
            total_cpm += day_cpm
            total_avg_pos += day_avg_pos
            
            # Добавляем день в данные (используем дату как query для совместимости с шаблоном)
            day_date = day.get('date', '') if isinstance(day, dict) else getattr(day, 'date', '')
            days_data.append({
                "query": str(day_date)[:10] if day_date else 'N/A',
                "views": day_views,
                "clicks": day_clicks,
                "orders": day_orders,
                "atbs": day_atbs,
                "shks": day_shks,
                "ctr": day_ctr,
                "cpc": day_cpc,
                "cpm": day_cpm,
                "avg_pos": day_avg_pos,
                "spend": day_sum,
            })
        
        # Считаем средние значения
        count = len(days_data) if days_data else 1
        avg_cpc = round(total_cpc / count, 2) if count > 0 else 0
        avg_cpm = round(total_cpm / count, 2) if count > 0 else 0
        avg_avg_pos = round(total_avg_pos / count, 2) if count > 0 else 0
        ctr = round((total_clicks / total_views * 100) if total_views > 0 else 0, 2)
        cpc = round(total_spend / total_clicks if total_clicks > 0 else 0, 2)
        
        return {
            "campaign_id": campaign_id,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_orders": total_orders,
            "total_atbs": total_atbs,
            "total_shks": total_shks,
            "total_spend": total_spend,
            "ctr": ctr,
            "cpc": cpc,
            "cpm": avg_cpm,
            "avg_pos": avg_avg_pos,
            "days": days_data
        }

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
