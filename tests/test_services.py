import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, desc

from app.services.trading import TradingService
from app.models.database import SpimexTradingResult

pytestmark = pytest.mark.asyncio

class TestTradingService:
    """Тесты для класса TradingService"""

    async def test_get_last_trading_dates(self):
        """Тест получения списка последних торговых дат с использованием мока"""
        # Создаем мок для сессии
        mock_session = MagicMock()
        
        # Настраиваем метод execute для асинхронной работы
        mock_result = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Настраиваем метод scalars и all
        mock_scalars = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = [datetime.now()]
        
        # Создаем экземпляр сервиса с моком
        service = TradingService(mock_session)
        
        # Вызываем тестируемый метод
        limit = 5
        dates = await service.get_last_trading_dates(limit)
        
        # Проверяем, что execute был вызван
        mock_session.execute.assert_called_once()
        
        # Проверяем результат
        assert len(dates) == 1
        assert isinstance(dates[0], datetime)
    
    async def test_get_last_trading_dates_with_patch(self):
        """Тест получения списка последних торговых дат с использованием patch"""
        # Создаем мок для даты
        test_date = datetime.now()
        
        # Создаем мок для сессии, execute, scalars и all
        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        
        # Патчим select, чтобы не зависеть от реальной реализации
        with patch('app.services.trading.select', return_value=MagicMock()) as mock_select, \
             patch('app.services.trading.desc', return_value=MagicMock()) as mock_desc:
            
            # Настраиваем возвращаемое значение для execute
            mock_result = MagicMock()
            mock_session.execute.return_value = mock_result
            
            # Настраиваем возвращаемое значение для scalars и all
            mock_scalars = MagicMock()
            mock_result.scalars.return_value = mock_scalars
            mock_scalars.all.return_value = [test_date]
            
            # Создаем экземпляр сервиса с моком
            service = TradingService(mock_session)
            
            # Вызываем тестируемый метод
            limit = 5
            dates = await service.get_last_trading_dates(limit)
            
            # Проверяем, что select был вызван
            mock_select.assert_called_once()
            
            # Проверяем, что execute был вызван
            mock_session.execute.assert_called_once()
            
            # Проверяем результат
            assert len(dates) == 1
            assert dates[0] == test_date
    
    async def test_get_last_trading_query_construction(self):
        """
        Тест правильности построения SQL-запроса для получения последних торговых дат
        Демонстрация использования мока для проверки вызова внутренних функций
        """
        # Создаем мок для сессии
        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        
        # Настраиваем возвращаемое значение для execute
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result
        
        # Настраиваем возвращаемое значение для scalars и all
        mock_scalars = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = []
        
        # Патчим sqlalchemy функции
        with patch('app.services.trading.select') as mock_select, \
             patch('app.services.trading.desc') as mock_desc:
            
            # Создаем экземпляр сервиса с моком
            service = TradingService(mock_session)
            
            # Вызываем тестируемый метод
            limit = 5
            await service.get_last_trading_dates(limit)
            
            # Проверяем, что select и desc были вызваны
            mock_select.assert_called_once()
            mock_desc.assert_called_once()
            
            # Проверяем, что execute был вызван
            mock_session.execute.assert_called_once()