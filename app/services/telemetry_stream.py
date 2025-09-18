import asyncio
from typing import Optional
from app.core.config import settings
from app.services.position_cache import cache
from app.ws.hub import hub  # 기존 WS 허브 사용

class TelemetryStreamer:
    def __init__(self, drone_id: str = "D001"):
        self.addr = settings.MAVSDK_ADDRESS
        self.drone_id = drone_id
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def _loop(self):
        from mavsdk import System  # 지연 import

        while not self._stop.is_set():
            try:
                drone = System()
                await drone.connect(system_address=self.addr)

                async for state in drone.core.connection_state():
                    if state.is_connected:
                        break

                async for health in drone.telemetry.health():
                    if health.is_global_position_ok and health.is_home_position_ok:
                        break

                async for pos in drone.telemetry.position():
                    if self._stop.is_set():
                        break
                    x = float(pos.latitude_deg)
                    y = float(pos.longitude_deg)
                    z = float(pos.relative_altitude_m)  # 필요시 절대/상대 조합으로 변경
                    slope = None

                    await cache.set(self.drone_id, x, y, z, slope)
                    await hub.broadcast({
                        "type": "telemetry",
                        "data": {"x": x, "y": y, "z": z, "slope": slope, "drone_id": self.drone_id}
                    })

            except Exception as e:
                await hub.broadcast({"type": "consoleMessage", "data": f"[stream] {e}"})
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
