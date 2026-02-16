"""
Пример использования Wildberries Promotion API Manager
"""

import asyncio
import aiohttp
from datetime import date

# Пример использования API
async def example_usage():
    # URL вашего запущенного приложения
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Пример 1: Получение списка кампаний
        print("Получение списка кампаний...")
        async with session.get(f"{base_url}/campaigns") as resp:
            campaigns = await resp.json()
            print(f"Кампании: {campaigns}")
        
        # Пример 2: Получение ставок поисковых кластеров
        print("\nПолучение ставок поисковых кластеров...")
        payload = [
            {
                "advert_id": 123456,  # Замените на реальный ID кампании
                "nm_id": 789012,      # Замените на реальный артикул WB
                "norm_query": "поисковый запрос",
                "bid": 1000
            }
        ]
        async with session.post(f"{base_url}/search-clusters/bids", json=payload) as resp:
            bids = await resp.json()
            print(f"Ставки кластеров: {bids}")
        
        # Пример 3: Установка ставок для поисковых кластеров
        print("\nУстановка ставок для поисковых кластеров...")
        payload = [
            {
                "advert_id": 123456,  # Замените на реальный ID кампании
                "nm_id": 789012,      # Замените на реальный артикул WB
                "norm_query": "поисковый запрос",
                "bid": 1500
            }
        ]
        async with session.post(f"{base_url}/search-clusters/set-bids", json=payload) as resp:
            result = await resp.json()
            print(f"Результат установки ставок: {result}")
        
        # Пример 4: Получение статистики по кластерам
        print("\nПолучение статистики по кластерам...")
        payload = {
            "from_date": date.today().isoformat(),
            "to_date": date.today().isoformat(),
            "items": [
                {
                    "advert_id": 123456,  # Замените на реальный ID кампании
                    "nm_id": 789012,      # Замените на реальный артикул WB
                    "norm_query": "поисковый запрос",
                    "bid": 1000
                }
            ]
        }
        async with session.post(f"{base_url}/search-clusters/stats", json=payload) as resp:
            stats = await resp.json()
            print(f"Статистика: {stats}")

if __name__ == "__main__":
    asyncio.run(example_usage())