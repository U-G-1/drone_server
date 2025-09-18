# app/core/config.py
import os
from pydantic import BaseModel
from typing import List  # (py3.10에선 없어도 되지만 호환 위해)

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    MAVSDK_ADDRESS: str = os.getenv("MAVSDK_ADDRESS", "udp://:14540")
    CORS_ORIGINS: List[str] = ["*"]  # ★ 추가: 필요하면 ['http://127.0.0.1:8080']로 제한

settings = Settings()
