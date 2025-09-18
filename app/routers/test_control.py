# app/routers/test_control.py
import os
import asyncio
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/test", tags=["test"])

class CommandIn(BaseModel):
    action: Literal["arm", "takeoff"]
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
    # 옵션: 목표 이륙 고도 설정
    try:
        if alt and alt > 0:
            await drone.action.set_takeoff_altitude(float(alt))
    except Exception:
        pass
    await drone.action.arm()
    await asyncio.sleep(1)
    await drone.action.takeoff()
    return {"ok": True, "action": "takeoff", "altitude": alt}

@router.post("/command")
async def send_command(body: CommandIn):
    """
    FAKE_TELEMETRY=1 → 실제 명령 없이 성공 응답만 에뮬레이션
    그 외 → MAVSDK 연결해서 Arm/Takeoff 수행
    """
    if _is_fake():
        # 에뮬 모드: 바로 완료 응답 (UI/연동 테스트용)
        await asyncio.sleep(0.3)
        return {"ok": True, "mode": "FAKE", "action": body.action, "altitude": body.altitude}

    try:
        if body.action == "arm":
            return await _arm_real()
        elif body.action == "takeoff":
            alt = body.altitude or 5.0
            return await _takeoff_real(alt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{body.action} 실패: {e}")
