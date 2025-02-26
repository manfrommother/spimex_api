import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient

from app.models.database import Base, SpimexTradingResult
from app.config import settings
from app.cache import RedisCache
from main import app

# Настройка тестовой БД
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Переопределяем зависимости
@pytest.fixture
def redis_mock():
    """Мок для Redis клиента"""
    with patch("app.cache.redis.Redis") as redis_mock:
        redis_client_mock = MagicMock()
        redis_mock.return_value = redis_client_mock
        yield redis_client_mock

@pytest.fixture
async def test_engine():
    """Создает тестовый движок БД"""
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def async_session(test_engine):
    """Создает тестовую сессию SQLAlchemy"""
    async_session_maker = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

@pytest.fixture
def override_get_db(async_session):
    """Переопределяет зависимость get_db для использования тестовой сессии"""
    async def _override_get_db():
        yield async_session
    
    app.dependency_overrides = {}  # Сброс переопределений
    app.dependency_overrides["get_db"] = _override_get_db
    
    return async_session

@pytest.fixture
def override_get_cache(redis_mock):
    """Переопределяет зависимость get_cache для использования мока"""
    def _override_get_cache():
        cache = RedisCache()
        cache.redis_client = redis_mock
        return cache
    
    app.dependency_overrides["get_cache"] = _override_get_cache
    
    return redis_mock

@pytest.fixture
def test_client(override_get_db, override_get_cache):
    """Создает тестовый клиент FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def sample_trading_data(async_session):
    """Создает тестовые данные торгов"""
    # Создаем несколько записей для тестирования
    now = datetime.now()
    
    test_data = [
        SpimexTradingResult(
            id=1,
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
        for i in range(10)  # Создаем 10 записей за последние 10 дней
    ]
    
    for item in test_data:
        async_session.add(item)
    
    await async_session.commit()
    
    return test_data

# Фикстура для мока cache.get
@pytest.fixture
def mock_cache_get():
    """Мок для метода cache.get"""
    with patch.object(RedisCache, 'get', return_value=None) as mock:
        yield mock

# Фикстура для мока cache.set
@pytest.fixture
def mock_cache_set():
    """Мок для метода cache.set"""
    with patch.object(RedisCache, 'set') as mock:
        yield mock