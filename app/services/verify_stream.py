# app/services/verify_stream.py
import asyncio
import math
import time
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.ws.hub import hub


@dataclass
class _LastValue:
    ts: float
    payload: dict


class VerifyTelemetryStreamer:
    """
    - raw: 들어오는 즉시 브로드캐스트(혼재 그대로)
      {type:'raw_telemetry', data:{kind:'position'|'battery', ts, ...}}
    - normalized: 1Hz 스케줄링 스냅샷 브로드캐스트(정리된 결과)
      {type:'normalized_telemetry', data:{ts, position:{...}, battery:{...}}}
    """

    def __init__(self, drone_id: str = "D001"):
        self.addr = settings.MAVSDK_ADDRESS
        self.drone_id = drone_id
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

        self._last_pos: Optional[_LastValue] = None
        self._last_batt: Optional[_LastValue] = None

    async def _broadcast_raw(self, kind: str, payload: dict):
        now = time.time()
        await hub.broadcast({"type": "raw_telemetry", "data": {"kind": kind, "ts": now, **payload}})

    async def _normalized_loop(self):
        while not self._stop.is_set():
            now = time.time()
            data = {
                "ts": now,
                "position": self._last_pos.payload if self._last_pos else None,
                "battery": self._last_batt.payload if self._last_batt else None,
                "pos_ts": self._last_pos.ts if self._last_pos else None,
                "batt_ts": self._last_batt.ts if self._last_batt else None,
            }
            await hub.broadcast({"type": "normalized_telemetry", "data": data})
            await asyncio.sleep(1.0)

    async def _fake_loop(self):
        # FAKE에서 “주기 다르게” 만들어 혼재를 더 확실히 보이게 함
        t = 0.0

        async def _pos():
            nonlocal t
            while not self._stop.is_set():
                x = 37.400000 + 0.0001 * math.cos(t)
                y = 127.100000 + 0.0001 * math.sin(t)
                z = 10.0 + 2.0 * math.sin(t / 2)
                payload = {"x": float(x), "y": float(y), "z": float(z)}
                self._last_pos = _LastValue(ts=time.time(), payload=payload)
                await self._broadcast_raw("position", payload)
                await asyncio.sleep(0.2)  # position은 빠르게
                t += 0.15

        async def _batt():
            remaining = 1.0
            while not self._stop.is_set():
                remaining = max(0.0, remaining - 0.01)
                payload = {"remaining": float(remaining)}
                self._last_batt = _LastValue(ts=time.time(), payload=payload)
                await self._broadcast_raw("battery", payload)
                await asyncio.sleep(2.0)  # battery는 느리게

        await asyncio.gather(_pos(), _batt(), self._normalized_loop())

    async def _mavsdk_loop(self):
        from mavsdk import System

        drone = System()
        await drone.connect(system_address=self.addr)

        async for state in drone.core.connection_state():
            if state.is_connected:
                break

        async def _pos():
            async for pos in drone.telemetry.position():
                if self._stop.is_set():
                    break
                payload = {
                    "x": float(pos.latitude_deg),
                    "y": float(pos.longitude_deg),
                    "z": float(pos.relative_altitude_m),
                }
                self._last_pos = _LastValue(ts=time.time(), payload=payload)
                await self._broadcast_raw("position", payload)

        async def _batt():
            async for b in drone.telemetry.battery():
                if self._stop.is_set():
                    break
                payload = {
                    "remaining": float(getattr(b, "remaining_percent", 0.0) or 0.0),
                    "voltage_v": float(getattr(b, "voltage_v", 0.0) or 0.0),
                    "current_a": float(getattr(b, "current_a", 0.0) or 0.0),
                }
                self._last_batt = _LastValue(ts=time.time(), payload=payload)
                await self._broadcast_raw("battery", payload)

        await asyncio.gather(_pos(), _batt(), self._normalized_loop())

    async def _loop(self):
        while not self._stop.is_set():
            try:
                if settings.FAKE_TELEMETRY:
                    await self._fake_loop()
                else:
                    await self._mavsdk_loop()
            except Exception as e:
                await hub.broadcast({"type": "consoleMessage", "data": f"[verify_stream error] {e}"})
                await asyncio.sleep(2)

    def start(self):
        if not self._task or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._stop.set()
        if self._task:
            await asyncio.wait([self._task], timeout=3)


verify_streamer = VerifyTelemetryStreamer()
