from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from app.models.database import Base
from app.config import settings
from app.cache import RedisCache, get_cache

# Создаем тестовый движок SQLite в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Создаем фабрику сессий
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Асинхронный контекстный менеджер для lifespan событий
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Функция жизненного цикла приложения для тестов.
    Создает таблицы в памяти и удаляет их после тестов.
    """
    # Создаем таблицы перед запуском тестов
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Удаляем таблицы после тестов
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Функция зависимости для получения сессии БД
async def get_test_db():
    """
    Функция-зависимость для получения тестовой сессии БД.
    """
    async with TestSessionLocal() as session:
        yield session

# Функция-зависимость для получения мок-кеша
def get_test_cache():
    """
    Функция-зависимость для получения тестового кеша Redis.
    """
    return RedisCache()

# Создаем тестовое приложение FastAPI
def create_test_app() -> FastAPI:
    """
    Создает тестовое приложение FastAPI с настроенными зависимостями.
    """
    app = FastAPI(
        title=settings.API_TITLE,
        description="Тестовое API для получения данных о торгах СПИМЕКС",
        version=settings.API_VERSION,
        lifespan=lifespan,  # Используем специальный lifespan для тестов
    )
    
    return app

# Готовое тестовое приложение
test_app = create_test_app()