import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncEngine

def patch_postgres_engine():
    """
    Патчит PostgreSQL engine, чтобы избежать конфликтов с asyncpg
    
    """
    # Создаем мок для AsyncEngine
    mock_engine = MagicMock(spec=AsyncEngine)
    
    # Создаем мок для метода begin
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    
    # Создаем мок для метода run_sync
    mock_conn.run_sync = MagicMock()
    
    # Патчим engine в основном модуле
    patcher = patch('main.engine', mock_engine)
    mock_engine_instance = patcher.start()
    
    return patcher, mock_engine_instance

@pytest.fixture
def mock_postgres_engine():
    """
    Фикстура для патчинга PostgreSQL engine в тестах
    """
    patcher, mock_engine = patch_postgres_engine()
    yield mock_engine
    patcher.stop()