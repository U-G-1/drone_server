from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio

router = APIRouter()

class TakeoffIn(BaseModel):
    altitude: float = 3.0  # m

@router.post("/actions/takeoff")
async def takeoff(body: TakeoffIn, tasks: BackgroundTasks):
    # TODO: MAVSDK 연결로 교체 (지금은 시뮬레이션)
    async def _simulate():
        await asyncio.sleep(1)
    tasks.add_task(_simulate)
    return {"ok": True, "msg": f"Takeoff to {body.altitude}m (simulated)"}

class AutoFlightIn(BaseModel):
    tag: Optional[str] = None
    speed_m_s: float = 2.0

@router.post("/flight/auto")
async def auto_flight(body: AutoFlightIn):
    # TODO: DB에서 tag 경로 조회 → MAVSDK 호출(혹은 pyCode/move_drone.py)
    return {"ok": True, "msg": f"Auto-flight start, tag={body.tag}, speed={body.speed_m_s}"}
