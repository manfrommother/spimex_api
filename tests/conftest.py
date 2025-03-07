import sys
import os
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.database import Base, SpimexTradingResult
from app.cache import RedisCache, get_cache
from main import app, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
async def init_db():
    """Инициализирует тестовую базу данных"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def redis_mock():
    """Мок для Redis клиента"""
    with patch("app.cache.redis.Redis") as redis_mock:
        redis_client_mock = MagicMock()
        redis_mock.return_value = redis_client_mock
        yield redis_client_mock

@pytest.fixture
async def async_session():
    """Создает тестовую сессию SQLAlchemy"""
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
def override_get_db():
    """Переопределяет зависимость get_db для использования тестовой БД"""
    # Оригинальная зависимость
    original_get_db = get_db
    
    async def mock_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    # Заменяем зависимость
    app.dependency_overrides[get_db] = mock_get_db
    
    yield
    
    # Восстанавливаем исходную зависимость
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest.fixture
def override_get_cache(redis_mock):
    """Переопределяет зависимость get_cache для использования мока"""
    # Оригинальная зависимость
    original_get_cache = get_cache
    
    # Новая зависимость, которая возвращает мок
    def mock_get_cache():
        cache = RedisCache()
        cache.redis_client = redis_mock
        return cache
    
    # Заменяем зависимость
    app.dependency_overrides[get_cache] = mock_get_cache
    
    yield redis_mock
    
    # Восстанавливаем исходную зависимость
    if get_cache in app.dependency_overrides:
        del app.dependency_overrides[get_cache]

@pytest.fixture
def disable_startup_event():
    """
    Отключает событие startup в FastAPI путем замены его на пустую функцию
    """
    # Сохраняем оригинальный on_event метод
    original_on_event = app.router.on_event
    
    # Определяем мок-функцию, которая ничего не делает
    def mock_on_event(event_type):
        def decorator(func):
            return func
        return decorator
    
    # Заменяем on_event на мок
    app.router.on_event = mock_on_event
    
    yield
    
    # Восстанавливаем оригинальный on_event
    app.router.on_event = original_on_event

@pytest.fixture
def mock_engine():
    """Мок для engine SQLAlchemy"""
    # Создаем мок для AsyncEngine
    with patch('main.engine') as mock_engine:
        # Настраиваем мок для метода begin
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        # Настраиваем мок для метода run_sync
        mock_conn.run_sync = AsyncMock()
        
        yield mock_engine

@pytest.fixture
def test_client(override_get_db, override_get_cache, disable_startup_event, mock_engine):
    """Создает тестовый клиент FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def sample_trading_data(async_session):
    """Создает тестовые данные торгов"""
    now = datetime.now()
    
    test_data = [
        SpimexTradingResult(
            id=i+1,
            trading_date=now - timedelta(days=i),
            oil_id=1 if i % 2 == 0 else 2,
            delivery_type_id=1,
            delivery_basis_id=1,
            volume=100.0 + i,
            price=50.0 + i,
            total_value=(100.0 + i) * (50.0 + i),
            created_at=now,
            updated_at=now
        )
        for i in range(10)
    ]
    
    for item in test_data:
        async_session.add(item)
    
    await async_session.commit()
    
    yield test_data
    
    for item in test_data:
        await async_session.delete(item)
    await async_session.commit()

# Фикстуры для моков кеша

@pytest.fixture
def mock_cache_get():
    """Мок для метода cache.get"""
    with patch.object(RedisCache, 'get', return_value=None) as mock:
        yield mock

@pytest.fixture
def mock_cache_set():
    """Мок для метода cache.set"""
    with patch.object(RedisCache, 'set') as mock:
        yield mock