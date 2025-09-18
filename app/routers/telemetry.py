from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.location_service import create_location

router = APIRouter()

async def get_session():
    async with SessionLocal() as s:
        yield s

class TelemetryIn(BaseModel):
    x: float
    y: float
    z: float
    slope: Optional[float] = Field(default=None)
    tag: str  # chim_name

@router.post("", summary="Save current coordinate with chim_name")
async def save_telemetry(body: TelemetryIn, session: AsyncSession = Depends(get_session)):
    if not body.tag:
        raise HTTPException(status_code=400, detail="tag (chim_name) is required")
    row = await create_location(
        session,
        loca_x=body.x, loca_y=body.y, loca_z=body.z,
        slope=body.slope, chim_name=body.tag,
    )
    return {"ok": True, "uid": row.uid, "chim_name": row.chim_name, "chim_num": row.chim_num}
