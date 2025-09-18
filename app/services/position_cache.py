import asyncio
from dataclasses import dataclass
from typing import Optional, Dict
from time import time

@dataclass
class Position:
    x: float
    y: float
    z: float
    slope: Optional[float]
    ts: float

class PositionCache:
    def __init__(self):
        self._store: Dict[str, Position] = {}
        self._lock = asyncio.Lock()

    async def set(self, drone_id: str, x: float, y: float, z: float, slope: Optional[float]):
        async with self._lock:
            self._store[drone_id] = Position(x, y, z, slope, time())

    async def get(self, drone_id: str) -> Optional[Position]:
        async with self._lock:
            return self._store.get(drone_id)

cache = PositionCache()
