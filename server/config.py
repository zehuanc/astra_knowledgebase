import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Astra Knowledge Base"
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "secret_key_for_development")
    DIFY_API_KEY: str = os.environ.get("DIFY_API_KEY", "")
    DIFY_DATASET_APIKEY: str = os.environ.get("DIFY_DATASET_APIKEY", "")
    JINA_TOKEN: str = os.environ.get("JINA_TOKEN", "")
    
    # Database settings can be added here
    # DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./astra.db")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 