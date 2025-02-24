import json
from datetime import datetime, time
from typing import Any, Optional
import redis
from fastapi import Depends

from app.config import settings


class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def _get_ttl(self) -> int:
        '''Вычисляет время до заданного часа:минуты следующего дня'''
        now = datetime.now()
        target_time = time(settings.CACHE_RESET_HOUR, settings.CACHE_RESET_MINUTE)

        if now.time() >= target_time:
            # Если текущее время больше или равно целевому времени, устанавливаем TTL до завтра
            tomorrow = now.replace(
                hour=settings.CACHE_RESET_HOUR,
                minute=settings.CACHE_RESET_MINUTE,
                second=0,
                microsecond=0
            )
            tomorrow = tomorrow.replace(day=tomorrow.day + 1)
            ttl = int((tomorrow - now).total_seconds())
        else:
            # Если текущее время меньше целевого времени, устанавливаем TTL до сегодняшнего целевого времени
            target = now.replace(
                hour=settings.CACHE_RESET_HOUR,
                minute=settings.CACHE_RESET_MINUTE,
                second=0,
                microsecond=0
            )
            ttl = int((target - now).total_seconds())
        
        return ttl
    
    def get(self, key: str) -> Optional[Any]:
        '''Получаем данные из кэша'''
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        '''
        Сохраняет данные в кэш до заданного часа:минуты
        
        Args:
            key: Ключ для сохранения
            value: Значение для сохранения
            ttl: Необязательное время жизни в секундах (если не указано, используется время до сброса кеша)
        '''
        if ttl is None:
            ttl = self._get_ttl()
        
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )
    
    def invalidate_all(self) -> None:
        '''Очищает весь кэш'''
        self.redis_client.flushdb()
    
    def invalidate_key(self, key: str) -> None:
        '''Удаляет конкретный ключ из кэша'''
        self.redis_client.delete(key)


# Dependency для FastAPI
def get_cache() -> RedisCache:
    return RedisCache()