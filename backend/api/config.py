"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/boola"

    # vLLM
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "not-needed"
    vllm_model: str = "Qwen/Qwen2.5-14B-Instruct"

    # Embedding
    embedding_model: str = "BAAI/bge-base-en-v1.5"

    # Application
    environment: str = "development"
    debug: bool = True

    # CORS
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
