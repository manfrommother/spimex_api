import json
from datetime import datetime, time
from typing import Any, Optional
import redis
from fastapi import Depends


class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    def _get_ttl(self) -> int:
        '''Вычисляет время до 14:11 следующего дня'''
        now = datetime.now()
        target_time = time(14, 11)

        if now.time() >= target_time:
            #Если текущее время больше или равно 14:11, устанавливаем TTL до завтра
            tomorrow = now.replace(
                hour=14,
                minute=11,
                second=0,
                microsecond=0
            )
            tomorrow = tomorrow.replace(day=tomorrow.day + 1)
            ttl = int((tomorrow - now).total_seconds())
        else:
            #Если текущее время меньше 14:11, устанавливаем TTL до сегодняшних 14:11
            target = now.replace(
                hour=14,
                minute=11,
                second=0,
                microsecond=0
            )
            ttl = int((target - now).total_seconds())
        
        return ttl
    
    def get(self, key:str) -> Optional[Any]:
        '''Получаем данные из кэша'''
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key:str, value: Any) -> None:
        '''Сохраняет данные в кэш до 14:11'''
        ttl = self._get_ttl()
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )

#Dependency для FastAPI
def get_cache() -> RedisCache:
    return RedisCache()