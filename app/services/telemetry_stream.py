import asyncio
from typing import Optional
from app.core.config import settings
from app.services.position_cache import cache
from app.ws.hub import hub  # 기존 broadcast 허브 사용

class TelemetryStreamer:
    def __init__(self, drone_id: str = "D001"):
        self.addr = settings.MAVSDK_ADDRESS
        self.drone_id = drone_id
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def _loop(self):
        # 지연 import (mavsdk 미설치 환경 대비)
        from mavsdk import System

        while not self._stop.is_set():
            try:
                drone = System()
                await drone.connect(system_address=self.addr)

                # 연결 대기
                async for state in drone.core.connection_state():
                    if state.is_connected:
                        break

                # 글로발 포지션/홈 준비 대기(옵션)
                async for health in drone.telemetry.health():
                    if health.is_global_position_ok and health.is_home_position_ok:
                        break

                # 실시간 수신 루프
                async for pos in drone.telemetry.position():
                    if self._stop.is_set():
                        break
                    # 위경도 + 절대고도로 가정 (필요 시 변환/상대고도 조정)
                    x = float(pos.latitude_deg)
                    y = float(pos.longitude_deg)
                    # absolute_altitude_m + relative_altitude_m 조합 대신, 예시는 relative_altitude_m 사용 가능
                    z = float(pos.relative_altitude_m)
                    slope = None

                    await cache.set(self.drone_id, x, y, z, slope)

                    await hub.broadcast({
                        "type": "telemetry",
                        "data": {"x": x, "y": y, "z": z, "slope": slope, "drone_id": self.drone_id}
                    })
                # 루프가 빠져나오면 재연결 시도
            except Exception as e:
                # 에러를 콘솔 브로드캐스트로 보여주고 2초 후 재시도
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
