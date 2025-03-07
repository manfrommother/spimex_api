import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock

from app.models.database import SpimexTradingResult


def create_mock_trading_results(count: int = 10, start_date: Optional[datetime] = None) -> List[SpimexTradingResult]:
    """
    Создает список мок-объектов SpimexTradingResult для тестирования
    
    Args:
        count: Количество объектов для создания
        start_date: Начальная дата (если не указана, используется текущая дата)
        
    Returns:
        List[SpimexTradingResult]: Список объектов SpimexTradingResult
    """
    if start_date is None:
        start_date = datetime.now()
    
    results = []
    for i in range(count):
        trading_date = start_date - timedelta(days=i)
        # Чередуем значения oil_id для создания разнообразных данных
        oil_id = 1 if i % 2 == 0 else 2
        delivery_type_id = 1 if i % 3 == 0 else 2
        delivery_basis_id = i % 3 + 1
        
        # Создаем объект результата торгов
        result = SpimexTradingResult(
            id=i + 1,
            trading_date=trading_date,
            oil_id=oil_id,
            delivery_type_id=delivery_type_id,
            delivery_basis_id=delivery_basis_id,
            volume=100.0 + i * 10,
            price=50.0 + i,
            total_value=(100.0 + i * 10) * (50.0 + i),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        results.append(result)
    
    return results


def create_mock_trading_service() -> AsyncMock:
    """
    Создает мок сервиса TradingService с предопределенными ответами
    
    Returns:
        AsyncMock: Мок сервиса торговли
    """
    mock_service = AsyncMock()
    
    # Настраиваем мок-методы
    async def mock_get_last_trading_dates(limit: int = 10) -> List[datetime]:
        now = datetime.now()
        return [now - timedelta(days=i) for i in range(min(limit, 10))]
    
    mock_service.get_last_trading_dates.side_effect = mock_get_last_trading_dates
    
    async def mock_get_dynamics(
        start_date: datetime,
        end_date: datetime,
        oil_id: Optional[int] = None,
        delivery_type_id: Optional[int] = None,
        delivery_basis_id: Optional[int] = None
    ) -> List[SpimexTradingResult]:
        # Создаем мок-результаты
        all_results = create_mock_trading_results(20, end_date)
        
        # Фильтруем по дате
        results = [r for r in all_results if start_date <= r.trading_date <= end_date]
        
        # Применяем фильтры, если они указаны
        if oil_id is not None:
            results = [r for r in results if r.oil_id == oil_id]
        if delivery_type_id is not None:
            results = [r for r in results if r.delivery_type_id == delivery_type_id]
        if delivery_basis_id is not None:
            results = [r for r in results if r.delivery_basis_id == delivery_basis_id]
        
        return results
    
    mock_service.get_dynamics.side_effect = mock_get_dynamics
    
    async def mock_get_trading_result(
        oil_id: Optional[int] = None,
        delivery_type_id: Optional[int] = None,
        delivery_basis_id: Optional[int] = None,
        limit: int = 100
    ) -> List[SpimexTradingResult]:
        # Создаем мок-результаты
        all_results = create_mock_trading_results(20)
        
        # Применяем фильтры, если они указаны
        results = all_results
        if oil_id is not None:
            results = [r for r in results if r.oil_id == oil_id]
        if delivery_type_id is not None:
            results = [r for r in results if r.delivery_type_id == delivery_type_id]
        if delivery_basis_id is not None:
            results = [r for r in results if r.delivery_basis_id == delivery_basis_id]
        
        # Применяем ограничение
        return results[:min(limit, len(results))]
    
    mock_service.get_trading_result.side_effect = mock_get_trading_result
    
    return mock_service


def create_mock_redis_cache() -> AsyncMock:
    """
    Создает мок RedisCache с предопределенными ответами
    
    Returns:
        AsyncMock: Мок кеша Redis
    """
    mock_cache = AsyncMock()
    
    # Словарь для хранения данных мок-кэша
    mock_data = {}
    
    def mock_get(key: str) -> Optional[Any]:
        return mock_data.get(key)
    
    mock_cache.get.side_effect = mock_get
    
    def mock_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
        mock_data[key] = value
    
    mock_cache.set.side_effect = mock_set
    
    def mock_invalidate_all() -> None:
        mock_data.clear()
    
    mock_cache.invalidate_all.side_effect = mock_invalidate_all
    
    def mock_invalidate_key(key: str) -> None:
        if key in mock_data:
            del mock_data[key]
    
    mock_cache.invalidate_key.side_effect = mock_invalidate_key
    
    return mock_cache


async def example_usage_of_mocks():
    # Создаем мок сервиса
    mock_service = create_mock_trading_service()
    
    # Создаем мок кэша
    mock_cache = create_mock_redis_cache()
    
    # Получаем последние торговые даты
    dates = await mock_service.get_last_trading_dates(5)
    print(f"Последние 5 торговых дат: {dates}")
    
    # Получаем динамику торгов за последние 3 дня
    now = datetime.now()
    start_date = now - timedelta(days=3)
    end_date = now
    dynamics = await mock_service.get_dynamics(start_date, end_date, oil_id=1)
    print(f"Динамика торгов за последние 3 дня (oil_id=1): получено {len(dynamics)} результатов")
    
    # Сохраняем результаты в кэш
    mock_cache.set("test_key", {"results": len(dynamics)})
    
    # Получаем данные из кэша
    cached_data = mock_cache.get("test_key")
    print(f"Данные из кеша: {cached_data}")
    
    # Сбрасываем кэш
    mock_cache.invalidate_all()
    
    # Проверяем, что кэш пуст
    assert mock_cache.get("test_key") is None
    print("Кеш успешно сброшен")


if __name__ == "__main__":
    import asyncio
    
    # Запускаем пример использования моков
    asyncio.run(example_usage_of_mocks())