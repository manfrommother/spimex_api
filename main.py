from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Optional
import uvicorn
import json

from app.models.database import Base
from app.models.response import (
    LastTradingDatesResponse, 
    TradingDynamicsResponse,
    TradingResultsResponse
)
from app.services.trading import TradingService
from app.cache import RedisCache, get_cache
from app.config import settings

# Настройка базы данных
engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Создание приложения FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description="API для получения данных о торгах СПИМЕКС",
    version=settings.API_VERSION
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для получения сессии БД
async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()

# Инициализация базы данных
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Создаем таблицы, если они не существуют
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", tags=["Info"])
async def root():
    return {
        "message": settings.API_TITLE,
        "version": settings.API_VERSION,
        "endpoints": [
            "/api/trading/dates",
            "/api/trading/dynamics",
            "/api/trading/results"
        ]
    }

@app.get("/api/trading/dates", 
         response_model=LastTradingDatesResponse, 
         tags=["Trading"])
async def get_last_trading_dates(
    limit: int = Query(10, description="Количество последних дат для получения", gt=0, le=100),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """
    Получение списка последних торговых дат.
    
    - **limit**: Количество последних дат для получения (по умолчанию 10, максимум 100)
    """
    # Создание ключа кеша, основанного на параметрах запроса
    cache_key = f"trading_dates:{limit}"
    
    # Проверка наличия данных в кеше
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Получение данных, если они не в кеше
    service = TradingService(db)
    dates = await service.get_last_trading_dates(limit)
    
    # Формирование ответа
    response = {
        "dates": dates,
        "total": len(dates)
    }
    
    # Сохранение в кеш
    cache.set(cache_key, response)
    
    return response

@app.get("/api/trading/dynamics", 
         response_model=TradingDynamicsResponse, 
         tags=["Trading"])
async def get_dynamics(
    start_date: datetime = Query(..., description="Начальная дата периода (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="Конечная дата периода (YYYY-MM-DD)"),
    oil_id: Optional[int] = Query(None, description="ID типа нефтепродукта"),
    delivery_type_id: Optional[int] = Query(None, description="ID типа поставки"),
    delivery_basis_id: Optional[int] = Query(None, description="ID базиса поставки"),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """
    Получение данных о торгах за указанный период.
    
    - **start_date**: Начальная дата периода (обязательный параметр)
    - **end_date**: Конечная дата периода (обязательный параметр)
    - **oil_id**: ID типа нефтепродукта (опционально)
    - **delivery_type_id**: ID типа поставки (опционально)
    - **delivery_basis_id**: ID базиса поставки (опционально)
    """
    # Проверка валидности дат
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Начальная дата не может быть позже конечной")
    
    # Ограничиваем период до 365 дней для оптимизации
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=400, detail="Период не может превышать 365 дней")
    
    # Создание ключа кеша, основанного на параметрах запроса
    cache_key = f"dynamics:{start_date.isoformat()}:{end_date.isoformat()}:{oil_id}:{delivery_type_id}:{delivery_basis_id}"
    
    # Проверка наличия данных в кеше
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Получение данных, если они не в кеше
    service = TradingService(db)
    results = await service.get_dynamics(
        start_date, 
        end_date, 
        oil_id, 
        delivery_type_id, 
        delivery_basis_id
    )
    
    # Формирование ответа
    response = {
        "result": results,
        "total": len(results),
        "start_date": start_date,
        "end_date": end_date
    }
    
    # Сохранение в кеш
    cache.set(cache_key, response)
    
    return response

@app.get("/api/trading/results", 
         response_model=TradingResultsResponse, 
         tags=["Trading"])
async def get_trading_results(
    oil_id: Optional[int] = Query(None, description="ID типа нефтепродукта"),
    delivery_type_id: Optional[int] = Query(None, description="ID типа поставки"),
    delivery_basis_id: Optional[int] = Query(None, description="ID базиса поставки"),
    limit: int = Query(100, description="Ограничение количества записей", gt=0, le=1000),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """
    Получение последних результатов торгов.
    
    - **oil_id**: ID типа нефтепродукта (опционально)
    - **delivery_type_id**: ID типа поставки (опционально)
    - **delivery_basis_id**: ID базиса поставки (опционально)
    - **limit**: Ограничение количества записей (по умолчанию 100, максимум 1000)
    """
    # Создание ключа кеша, основанного на параметрах запроса
    cache_key = f"trading_results:{oil_id}:{delivery_type_id}:{delivery_basis_id}:{limit}"
    
    # Проверка наличия данных в кеше
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Получение данных, если они не в кеше
    service = TradingService(db)
    results = await service.get_trading_result(
        oil_id, 
        delivery_type_id, 
        delivery_basis_id, 
        limit
    )
    
    # Формирование ответа
    response = {
        "result": results,
        "total": len(results)
    }
    
    # Сохранение в кеш
    cache.set(cache_key, response)
    
    return response

# Добавляем эндпоинт для принудительного сброса кеша (только для администраторов)
@app.post("/api/cache/invalidate", tags=["Admin"])
async def invalidate_cache(cache: RedisCache = Depends(get_cache)):
    """
    Принудительно сбрасывает весь кеш Redis.
    Этот эндпоинт должен быть защищен авторизацией в продакшн-среде.
    """
    cache.invalidate_all()
    return {"message": "Кеш успешно сброшен"}

# Запуск приложения при прямом вызове
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.APP_HOST, 
        port=settings.APP_PORT, 
        reload=settings.DEBUG
    )