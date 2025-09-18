# app/routers/test_control.py
import os
import asyncio
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/test", tags=["test"])

class CommandIn(BaseModel):
    # 여기 land 추가
    action: Literal["arm", "takeoff", "land"]
    altitude: Optional[float] = 5.0  # takeoff 시 목표 고도(m)

def _is_fake() -> bool:
    return os.getenv("FAKE_TELEMETRY", "").strip() not in ("", "0", "false", "False")

async def _arm_real():
    from mavsdk import System
    drone = System()
    await drone.connect(system_address="udp://:14540")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
    await drone.action.arm()
    return {"ok": True, "action": "arm"}

async def _takeoff_real(alt: float):
    from mavsdk import System
    drone = System()
    await drone.connect(system_address="udp://:14540")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
    try:
        if alt and alt > 0:
            await drone.action.set_takeoff_altitude(float(alt))
    except Exception:
        pass
    await drone.action.arm()
    await asyncio.sleep(1)
    await drone.action.takeoff()
    return {"ok": True, "action": "takeoff", "altitude": alt}

async def _land_real():
    from mavsdk import System
    drone = System()
    await drone.connect(system_address="udp://:14540")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
    await drone.action.land()
    # 선택: 안전하게 멈출 시간 조금 주기
    await asyncio.sleep(1)
    return {"ok": True, "action": "land"}

@router.post("/command")
async def send_command(body: CommandIn):
    """
    FAKE_TELEMETRY=1 → 실제 명령 없이 성공 응답만 에뮬레이션
    그 외 → MAVSDK 연결해서 Arm/Takeoff/Land 수행
    """
    if _is_fake():
        await asyncio.sleep(0.3)
        return {"ok": True, "mode": "FAKE", "action": body.action, "altitude": body.altitude}

    try:
        if body.action == "arm":
            return await _arm_real()
        elif body.action == "takeoff":
            alt = body.altitude or 5.0
            return await _takeoff_real(alt)
        elif body.action == "land":
            return await _land_real()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{body.action} 실패: {e}")
