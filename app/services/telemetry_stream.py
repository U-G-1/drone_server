import asyncio
import math
from typing import Optional
from app.core.config import settings
from app.services.position_cache import cache
from app.ws.hub import hub

class TelemetryStreamer:
    def __init__(self, drone_id: str = "D001"):
        self.addr = settings.MAVSDK_ADDRESS
        self.drone_id = drone_id
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def _fake_loop(self):
        t = 0.0
        while not self._stop.is_set():
            # 간단한 원운동 좌표
            x = 37.400000 + 0.0001 * math.cos(t)
            y = 127.100000 + 0.0001 * math.sin(t)
            z = 10.0 + 2.0 * math.sin(t / 2)
            slope = None
            await cache.set(self.drone_id, x, y, z, slope)
            await hub.broadcast({"type": "telemetry", "data": {"x": x, "y": y, "z": z, "slope": slope}})
            await asyncio.sleep(1.0)
            t += 0.2

    async def _mavsdk_loop(self):
        from mavsdk import System
        drone = System()
        await drone.connect(system_address=self.addr)

        async for state in drone.core.connection_state():
            if state.is_connected:
                break

        # 옵션: 헬스 체크 대기
        async for health in drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                break

        async for pos in drone.telemetry.position():
            if self._stop.is_set():
                break
            x = float(pos.latitude_deg)
            y = float(pos.longitude_deg)
            z = float(pos.relative_altitude_m)
            slope = None
            await cache.set(self.drone_id, x, y, z, slope)
            await hub.broadcast({"type": "telemetry", "data": {"x": x, "y": y, "z": z, "slope": slope}})

    async def _loop(self):
        while not self._stop.is_set():
            try:
                if settings.FAKE_TELEMETRY:
                    await self._fake_loop()
                else:
                    await self._mavsdk_loop()
            except Exception as e:
                await hub.broadcast({"type":"consoleMessage","data":f"[stream error] {e}"})
                await asyncio.sleep(2)

    def start(self):
        if not self._task or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._stop.set()
        if self._task:
            await asyncio.wait([self._task], timeout=3)

streamer = TelemetryStreamer()
