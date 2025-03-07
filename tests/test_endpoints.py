import pytest
from datetime import datetime, timedelta
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.trading import TradingService


class TestTradingEndpoints:
    """Тесты для API эндпоинтов торговли"""
    
    def test_get_last_trading_dates(self, test_client, mock_cache_get, mock_cache_set):
        """Тест получения списка последних торговых дат"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Получаем текущую дату
        now = datetime.now()
        trading_dates = [now - timedelta(days=i) for i in range(5)]
        
        # Патчим метод сервиса
        with patch.object(TradingService, 'get_last_trading_dates', 
                         return_value=trading_dates, new_callable=AsyncMock) as mock_method:
            
            # Выполняем запрос к API
            response = test_client.get("/api/trading/dates?limit=5")
            
            # Проверяем, что метод был вызван
            assert mock_method.called
            
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        assert "dates" in data
        assert "total" in data
    
    def test_get_last_trading_dates_from_cache(self, test_client, mock_cache_get):
        """Тест получения списка последних торговых дат из кеша"""
        # Имитируем наличие данных в кеше
        mock_cache_data = {
            "dates": ["2024-01-01T00:00:00", "2023-12-31T00:00:00"],
            "total": 2
        }
        mock_cache_get.return_value = mock_cache_data
        
        # Выполняем запрос к API
        response = test_client.get("/api/trading/dates?limit=5")
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа и что данные взяты из кеша
        data = response.json()
        assert data == mock_cache_data
    
    def test_get_dynamics(self, test_client, mock_cache_get, mock_cache_set):
        """Тест получения динамики торгов за период"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Определяем период для запроса
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        # Патчим метод сервиса
        with patch.object(TradingService, 'get_dynamics', 
                         return_value=[], new_callable=AsyncMock) as mock_method:
            
            # Выполняем запрос к API
            response = test_client.get(f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}")
            
            # Проверяем, что метод был вызван
            assert mock_method.called
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        assert "result" in data
        assert "total" in data
        assert "start_date" in data
        assert "end_date" in data
    
    def test_get_dynamics_with_filters(self, test_client, mock_cache_get, mock_cache_set):
        """Тест получения динамики торгов за период с фильтрацией"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Определяем период и фильтры для запроса
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        oil_id = 1
        
        # Патчим метод сервиса
        with patch.object(TradingService, 'get_dynamics', 
                         return_value=[], new_callable=AsyncMock) as mock_method:
            
            # Выполняем запрос к API
            response = test_client.get(
                f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}&oil_id={oil_id}"
            )
            
            # Проверяем, что метод был вызван
            assert mock_method.called
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_dynamics_invalid_dates(self, test_client):
        """Тест получения динамики торгов с некорректными датами"""
        # Определяем некорректный период (конечная дата раньше начальной)
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        # Выполняем запрос к API
        response = test_client.get(f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}")
        
        # Проверяем статус ответа (должен быть код ошибки)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_dynamics_too_long_period(self, test_client):
        """Тест получения динамики торгов за слишком длинный период"""
        # Определяем период более 365 дней
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=366)).strftime("%Y-%m-%d")
        
        # Выполняем запрос к API
        response = test_client.get(f"/api/trading/dynamics?start_date={start_date}&end_date={end_date}")
        
        # Проверяем статус ответа (должен быть код ошибки)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_trading_results(self, test_client, mock_cache_get, mock_cache_set):
        """Тест получения результатов торгов"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Патчим метод сервиса
        with patch.object(TradingService, 'get_trading_result', 
                         return_value=[], new_callable=AsyncMock) as mock_method:
            
            # Выполняем запрос к API
            response = test_client.get("/api/trading/results?limit=5")
            
            # Проверяем, что метод был вызван
            assert mock_method.called
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем структуру ответа
        data = response.json()
        assert "result" in data
        assert "total" in data
    
    def test_get_trading_results_with_filters(self, test_client, mock_cache_get, mock_cache_set):
        """Тест получения результатов торгов с фильтрацией"""
        # Проверяем, что кеш проверялся
        mock_cache_get.return_value = None
        
        # Определяем фильтры для запроса
        oil_id = 1
        
        # Патчим метод сервиса
        with patch.object(TradingService, 'get_trading_result', 
                         return_value=[], new_callable=AsyncMock) as mock_method:
            
            # Выполняем запрос к API
            response = test_client.get(f"/api/trading/results?oil_id={oil_id}&limit=5")
            
            # Проверяем, что метод был вызван
            assert mock_method.called
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
    
    def test_invalidate_cache(self, test_client, override_get_cache):
        """Тест принудительного сброса кеша"""
        # Выполняем запрос к API
        response = test_client.post("/api/cache/invalidate")
        
        # Проверяем статус ответа
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что метод invalidate_all был вызван
        override_get_cache.flushdb.assert_called_once()
    
    def test_root_endpoint(self, test_client):
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