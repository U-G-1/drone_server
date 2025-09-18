from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.position_cache import cache

router = APIRouter()

class CurrentOut(BaseModel):
    x: float
    y: float
    z: float
    slope: Optional[float] = None

@router.get("/current", response_model=CurrentOut)
async def current():
    p = await cache.get("D001")
    if not p:
        raise HTTPException(status_code=404, detail="no telemetry yet")
    return CurrentOut(x=p.x, y=p.y, z=p.z, slope=p.slope)
