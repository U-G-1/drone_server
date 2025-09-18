from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.position_cache import cache

router = APIRouter(prefix="/telemetry", tags=["telemetry-read"])

class CurrentOut(BaseModel):
    x: float; y: float; z: float
    slope: float | None = None  # 파이썬3.9면 Optional[float]로 변경
    drone_id: str

@router.get("/current", response_model=CurrentOut)
async def current(drone_id: str = "D001"):
    p = await cache.get(drone_id)
    if not p:
        raise HTTPException(status_code=404, detail="no telemetry yet")
    return CurrentOut(x=p.x, y=p.y, z=p.z, slope=p.slope, drone_id=drone_id)
