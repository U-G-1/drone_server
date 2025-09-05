import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    CORS_ORIGINS: list[str] = ["*"]

settings = Settings()
