import pytest
import json

from datetime import datetime, timedelta
from fastapi import status
from unittest.mock import patch


class TestTradingEndpoints:
    '''Тесты для API эндпоинтов торговли'''

    async def test_get_last_trading_dates(self, test_client, sample_trading_data, mock_cache_get, mock_cache_set):
        '''Тест получения списка последних торговых дат'''

        mock_cache_set.return_value = None

        response = test_client.get('/api/trading/dates?limit=5')

        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK

        # Проверяем структуру ответа
        data = response.json()
        assert "dates" in data
        assert "total" in data
        assert data["total"] <= 5
        assert len(data["dates"]) == data["total"]

        # Проверяем, что кеш был установлен
        mock_cache_set.assert_called_once()

    async def test_get_last_trading_dates_from_cache(self, test_client, mock_cache_get):
        '''Тест получения списка последних торговых дат из кэша'''
        # Имитируем наличие данных в кэше
        mock_cache_data = {
            "dates": ["2024-01-01T00:00:00", "2023-12-31T00:00:00"],
            "total": 2
        }
        mock_cache_get.returne_value = mock_cache_data

        # Выполняем запрос к API
        response = test_client.get('/api/trading/dates?limit=5')

        assert response.status_code == status.HTTP_200_OK

        # Проверяем структуру ответа и что данные взяты из кэша
        data = response.json()
        assert data == mock_cache_data

    async def test_get_dynamics(self, test_client, sample_trading_data, mock_cache_get, mock_cache_set):
        '''Тест получения динамики торгов за период'''
        # Проверяем, что кэш проверялся
        mock_cache_get.return_value = None

        # Определяем период для запроса
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

        response = test_client.get(f'/api/trading/dynamics?start_date={start_date}&end_date={end_date}')

        assert response.status_code == status.HTTP_200_OK

        # Проверяем структуру ответа
        data = response.json()
        assert "result" in data
        assert "total" in data
        assert "start_date" in data
        assert "end_date" in data

        # Проверяем, что кэш был установлен
        mock_cache_set.assert_called_once()

    async def test_get_dynamics_with_filters(self, test_client, sample_trading_data, mock_cache_get, mock_cache_set):
        """Тест получения динамики торгов за период с фильтрацией"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Определяем период и фильтры для запроса
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        oil_id = 1
        
        # Выполняем запрос к API
        response = test_client.get(
            f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}&oil_id={oil_id}"
        )
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        assert "result" in data
        
        # Проверяем, что все результаты соответствуют фильтру oil_id
        for item in data["result"]:
            assert item["oil_id"] == oil_id
    
    async def test_get_dynamics_invalid_dates(self, test_client):
        """Тест получения динамики торгов с некорректными датами"""
        # Определяем некорректный период (конечная дата раньше начальной)
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        # Выполняем запрос к API
        response = test_client.get(f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}")
        
        # Проверяем статус ответа (должен быть код ошибки)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_get_dynamics_too_long_period(self, test_client):
        """Тест получения динамики торгов за слишком длинный период"""
        # Определяем период более 365 дней
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=366)).strftime("%Y-%m-%d")
        
        # Выполняем запрос к API
        response = test_client.get(f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}")
        
        # Проверяем статус ответа (должен быть код ошибки)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_get_trading_results(self, test_client, sample_trading_data, mock_cache_get, mock_cache_set):
        """Тест получения результатов торгов"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Выполняем запрос к API
        response = test_client.get("/api/trading/results?limit=5")
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        assert "result" in data
        assert "total" in data
        assert data["total"] <= 5
        assert len(data["result"]) == data["total"]
        
        # Проверяем, что кеш был установлен
        mock_cache_set.assert_called_once()
    
    async def test_get_trading_results_with_filters(self, test_client, sample_trading_data, mock_cache_get, mock_cache_set):
        """Тест получения результатов торгов с фильтрацией"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Определяем фильтры для запроса
        oil_id = 1
        
        # Выполняем запрос к API
        response = test_client.get(f"/api/trading/results?oil_id={oil_id}&limit=5")
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        
        # Если есть результаты, проверяем, что все соответствуют фильтру oil_id
        if data["total"] > 0:
            for item in data["result"]:
                assert item["oil_id"] == oil_id
    
    async def test_invalidate_cache(self, test_client, override_get_cache):
        """Тест принудительного сброса кеша"""
        # Выполняем запрос к API
        response = test_client.post("/api/cache/invalidate")
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что метод invalidate_all был вызван
        override_get_cache.flushdb.assert_called_once()
    
    async def test_root_endpoint(self, test_client):
        """Тест корневого эндпоинта"""
        # Выполняем запрос к API
        response = test_client.get("/")
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert len(data["endpoints"]) == 3  # Проверяем, что есть 3 эндпоинта
