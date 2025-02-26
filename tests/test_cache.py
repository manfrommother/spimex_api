import pytest
from datetime import datetime, time
from unittest.mock import patch, MagicMock
import json

from app.cache import RedisCache
from app.config import settings

pytestmark = pytest.mark.asyncio

class TestRedisCache:
    '''Тесты для класса RedisCache'''

    def test_init(self, redis_mock):
        'Тест инициализации RedisCache'
        cache = RedisCache()

        # Проверяем, что Redis.Redis был вызван с правильными параметрами
        assert cache.redis_client is not None

    @patch('app.cache.datetime')
    def test_get_ttl_before_target(self, mock_datetime, redis_mock):
        '''Тест вычисления TTL когда'''
        # Настраиваем текущее время на 10:00
        mock_now = datetime(2025, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now

        #Целевое время сброса кеша в 14:11
        settings.CACHE_RESET_HOUR = 14
        settings.CACHE_RESET_MINUTE = 11

        cache = RedisCache()
        ttl = cache._get_ttl()

        #Ожидаемое время до сброса: от 10:00 до 14:11 = 4 часа 11 минут = 15060 секунд
        expected_ttl = (4 * 60 * 60) + (11 * 60)
        assert ttl == expected_ttl
    
    @patch('app.cache.datetime')
    def test_get_ttl_after_target(self, mock_datetime, redis_mock):
        '''Тест вычисления TTL когда текущее время больше целевого время сброса кеша'''
        #Настраиваем текущее вреся на 15:00
        mock_now = datetime(2025, 1, 1, 15, 0, 0)
        mock_datetime.now.return_value = mock_now

        #Целевое время сброса кеша в 14:11
        settings.CACHE_RESET_HOUR = 14
        settings.CACHE_RESET_MINUTE = 11

        cache = RedisCache()
        ttl = cache._get_ttl()

        #Ожидаемое время до сброса: от 15:00 до 14:11 следующего дня = 13 часа 11 минут = 83460 секугд
        expected_ttl = (23 * 60 * 60) + (11 * 60)
        assert ttl == expected_ttl

    def test_get_existing_data(self, redis_mock):
        '''Тест получения существующих данных из кэша'''
        #Настриваем мок для redis_client.get
        mock_data = json.dumps({"test": "data"})
        redis_mock.get.return_value = mock_data

        cache = RedisCache()
        result = cache.get('test_key')

        #Проверяем, что get был вызван с правильным ключом
        redis_mock.get.assert_called_with('test_key')
        #Проверяем, что результат был правильно десериализирован
        assert result == {"test": "data"}

    def test_get_nonexistent_data(self, redis_mock):
        '''Тест получения несуществующих данных из кеша'''
        #Настраиваем мок для redis_client.get, возвращающий None
        redis_mock.get.return_value = None

        cache = RedisCache()
        result = cache.get('test_key')

        #Проверяем, что get был вызван с правильным ключом
        redis_mock.get.assert_called_with('test_key')
        #Проверяем, что результат None
        assert result is None
    
    def test_set_with_custom_ttl(self, redis_mock):
        """Тест установки данных в кеш с заданным TTL"""
        cache = RedisCache()
        test_data = {"test": "data"}
        custom_ttl = 3600  # 1 час
        
        cache.set("test_key", test_data, ttl=custom_ttl)
        
        # Проверяем, что setex был вызван с правильными параметрами
        redis_mock.setex.assert_called_once()
        args, kwargs = redis_mock.setex.call_args
        assert args[0] == "test_key"
        assert args[1] == custom_ttl
        assert json.loads(args[2]) == test_data
    
    @patch.object(RedisCache, '_get_ttl')
    def test_set_with_default_ttl(self, mock_get_ttl, redis_mock):
        """Тест установки данных в кеш с TTL по умолчанию"""
        # Настраиваем мок для _get_ttl
        mock_get_ttl.return_value = 3600  # 1 час
        
        cache = RedisCache()
        test_data = {"test": "data"}
        
        cache.set("test_key", test_data)
        
        # Проверяем, что _get_ttl был вызван
        mock_get_ttl.assert_called_once()
        
        # Проверяем, что setex был вызван с правильными параметрами
        redis_mock.setex.assert_called_once()
        args, kwargs = redis_mock.setex.call_args
        assert args[0] == "test_key"
        assert args[1] == 3600
        assert json.loads(args[2]) == test_data
    
    def test_invalidate_all(self, redis_mock):
        """Тест очистки всего кеша"""
        cache = RedisCache()
        cache.invalidate_all()
        
        # Проверяем, что flushdb был вызван
        redis_mock.flushdb.assert_called_once()
    
    def test_invalidate_key(self, redis_mock):
        """Тест удаления конкретного ключа из кеша"""
        cache = RedisCache()
        cache.invalidate_key("test_key")
        
        # Проверяем, что delete был вызван с правильным ключом
        redis_mock.delete.assert_called_with("test_key")
