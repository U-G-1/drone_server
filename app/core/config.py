import os
from pydantic import BaseModel

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    MAVSDK_ADDRESS: str = os.getenv("MAVSDK_ADDRESS", "udp://:14540")  # PX4 SITL 기본

settings = Settings()
