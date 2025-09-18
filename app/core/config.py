import os
from pydantic import BaseModel
from typing import List

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    MAVSDK_ADDRESS: str = os.getenv("MAVSDK_ADDRESS", "udp://:14540")
    CORS_ORIGINS: List[str] = ["*"]
    FAKE_TELEMETRY: bool = os.getenv("FAKE_TELEMETRY", "0") == "1"

settings = Settings()
