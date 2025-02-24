from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Настройки приложения, загружаемые из переменных окружения
    """
    # Настройки базы данных
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = os.getenv("DB_PORT", 5432)
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "12345678")
    DB_NAME: str = os.getenv("DB_NAME", "spimex")
    
    # Настройки Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = os.getenv("REDIS_PORT", 6379)
    REDIS_DB: int = os.getenv("REDIS_DB", 0)
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Настройки приложения
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = os.getenv("APP_PORT", 8000)
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Настройки сброса кеша
    CACHE_RESET_HOUR: int = os.getenv("CACHE_RESET_HOUR", 14)
    CACHE_RESET_MINUTE: int = os.getenv("CACHE_RESET_MINUTE", 11)
    
    # Другие настройки
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "SPIMEX Trading API"
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Формирует URL подключения к базе данных
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем экземпляр настроек
settings = Settings()