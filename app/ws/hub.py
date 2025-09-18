import asyncio
from typing import Set
from starlette.websockets import WebSocket

class Hub:
    def __init__(self):
        self._conns: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._conns.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._conns.discard(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in list(self._conns):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for d in dead:
            await self.disconnect(d)

hub = Hub()
