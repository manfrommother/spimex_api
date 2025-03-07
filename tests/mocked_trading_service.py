from datetime import datetime, timedelta
from typing import List, Optional
from unittest.mock import AsyncMock

from app.models.database import SpimexTradingResult


def create_mock_trading_result(
    id: int, 
    days_ago: int = 0, 
    oil_id: int = 1, 
    delivery_type_id: int = 1, 
    delivery_basis_id: int = 1
) -> SpimexTradingResult:
    """
    Создает мок SpimexTradingResult
    
    Args:
        id: ID записи
        days_ago: Количество дней назад (относительно текущей даты)
        oil_id: ID типа нефтепродукта
        delivery_type_id: ID типа поставки
        delivery_basis_id: ID базиса поставки
        
    Returns:
        SpimexTradingResult: Объект результата торгов
    """
    now = datetime.now()
    trading_date = now - timedelta(days=days_ago)
    
    return SpimexTradingResult(
        id=id,
        trading_date=trading_date,
        oil_id=oil_id,
        delivery_type_id=delivery_type_id,
        delivery_basis_id=delivery_basis_id,
        volume=100.0 + id,
        price=50.0 + id,
        total_value=(100.0 + id) * (50.0 + id),
        created_at=now,
        updated_at=now
    )


class MockTradingService:
    """
    Мок-класс для TradingService с настраиваемыми ответами
    """
    
    def __init__(self):
        # Настройка мок-методов
        self.get_last_trading_dates = AsyncMock()
        self.get_dynamics = AsyncMock()
        self.get_trading_result = AsyncMock()
        
        # Установка значений по умолчанию
        self._setup_default_responses()
    
    def _setup_default_responses(self):
        """
        Устанавливает ответы методов по умолчанию
        """
        now = datetime.now()
        
        # Последние торговые даты (10 дней)
        trading_dates = [now - timedelta(days=i) for i in range(10)]
        self.get_last_trading_dates.return_value = trading_dates
        
        # Динамика торгов
        trading_results = [
            create_mock_trading_result(id=i+1, days_ago=i, oil_id=1 if i % 2 == 0 else 2)
            for i in range(10)
        ]
        self.get_dynamics.return_value = trading_results
        
        # Результаты торгов
        self.get_trading_result.return_value = trading_results
    
    def configure_last_trading_dates(self, dates: List[datetime]):
        """
        Настраивает ответ метода get_last_trading_dates
        
        Args:
            dates: Список дат для возврата
        """
        self.get_last_trading_dates.return_value = dates
    
    def configure_dynamics(self, results: List[SpimexTradingResult]):
        """
        Настраивает ответ метода get_dynamics
        
        Args:
            results: Список результатов торгов для возврата
        """
        self.get_dynamics.return_value = results
    
    def configure_trading_result(self, results: List[SpimexTradingResult]):
        """
        Настраивает ответ метода get_trading_result
        
        Args:
            results: Список результатов торгов для возврата
        """
        self.get_trading_result.return_value = results
    
    def inject_into_service(self, service_instance):
        """
        Внедряет мок-методы в существующий экземпляр сервиса
        
        Args:
            service_instance: Экземпляр TradingService
        """
        service_instance.get_last_trading_dates = self.get_last_trading_dates
        service_instance.get_dynamics = self.get_dynamics
        service_instance.get_trading_result = self.get_trading_result
        
        return service_instance