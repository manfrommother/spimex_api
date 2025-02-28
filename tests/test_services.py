import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.trading import TradingService
from app.models.database import SpimexTradingResult

pytest = pytest.mark.asyncio


class TestTradingService:
    '''Тесты для класс TradingService'''

    async def test_get_last_trading_dates(self, async_session, sample_trading_data):
        service = TradingService(async_session)

        limit = 5
        dates = await service.get_last_trading_dates(limit)

        assert len(dates) <= limit

        # Проверяем, что даты отсортированы по убывания
        for i in range(len(dates) - 1):
            assert dates[i] > dates[i + 1]

    async def test_get_dynamics_all(self, async_session, sample_trading_data):
        '''Тест получения динамики торгов за период без фильтрации'''

        service = TradingService(async_session)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)

        results = await service.get_dynamics(start_date, end_date)

        assert len(result) > 0

        # Проверяем, что даты торгов входят в заданный период
        for result in results:
            assert start_date <= result.trading_date <= end_date

    async def test_get_dynamics_filtered_by_oil_id(self, async_session, sample_trading_data):
        '''Тест получения динамики торгов за период с фильтрацией по типу нефтипродукта'''
        service = TradingService(async_session)

        # Определяем период и фильтр
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        oil_id = 1

        results = await service.get_dynamics(start_date, end_date, oil_id=oil_id)

        # Проверяем, что данные получены
        assert len(result) > 0

        # Проверяем, что все результаты соответствуют фильтру
        for result in results:
            assert result.oil_id == oil_id
            assert start_date <= result.trading_date <= end_date

    async def test_get_dynamics_filtered_complex(self, async_session, sample_trading_data):
        '''Тест для получения динамики тьоргов за период с комплексной фильтрации'''
        service = TradingService()

        # Определяем период и фильтры
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        oil_id = 1
        delivery_type_id = 1
        delivery_basis_id = 1

        # Получаем данные о торгах за период с фильтрами
        results = await service.get_dynamics(
            start_date,
            end_date,
            oil_id=oil_id,
            delivery_type_id=delivery_type_id,
            delivery_basis_id=delivery_basis_id
        )

        # Проверяем, чтто все результаты соответствуют фильтрам
        for result in results:
            assert result.oil_id == oil_id
            assert result.delivery_type_id == delivery_type_id
            assert result.delivery_basis_id == delivery_basis_id
            assert start_date <= result.trading_date <= end_date

    async def test_get_trading_result_all(self, async_session, sample_trading_data):
        '''Тест для получения результатов без фильтрации'''
        service = TradingService(async_session)

        limit = 5
        results = await service.get_trading_result(limit=limit)

        # Проверяем, что кол-во результатов по убывания даты
        for i in range(len(results) - 1):
            assert results[i].trading_date >= results[i + 1].trading_date

    async def test_get_trading_result_filtered(self, async_session, sample_trading_data):
        service = TradingService(async_session)

        oil_id = 1
        delivery_type_id = 1

        # Получаем результаты торгов с фильтрами
        results = await service.get_trading_result(
            oil_id=oil_id,
            delivery_type_id=delivery_type_id
        )

        # Проверяем, что все результаты соответствуют фильтрам
        for result in results:
            assert result.oil_id == oil_id
            assert result.delivery_type_id == delivery_type_id

    @patch('app.services.trading.select')
    async def test_get_last_trading_query_construction(self, mock_select, async_session):
        '''Тест правильности построения SQL-запроса для получения последних торговых дат'''

        # Настройка моков
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        mock_result = AsyncMock()
        async_session.execute = AsyncMock(return_value=mock_result)
        mock_result.scalars.return_value.all.return_value = []

        # Вызываем тестируемый метод
        service = TradingService(async_session)
        limit = 5
        await service.get_last_trading_dates(limit)

        # Проверка правильности построения запроса
        mock_select.assert_called_once()
        mock_query.distinct.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(limit)
        async_session.execute.assert_called_once_with(mock_query)