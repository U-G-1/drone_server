from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.schemas.telemetry import TelemetryIn, TelemetryOut
from app.services import telemetry_service
from app.ws.hub import hub

router = APIRouter()

async def get_session():
    async with SessionLocal() as s: yield s

@router.post("", response_model=TelemetryOut)
async def save_telemetry(body: TelemetryIn, session: AsyncSession = Depends(get_session)):
    row = await telemetry_service.create(session, **body.model_dump())
    await hub.broadcast({"type": "telemetry", "data": TelemetryOut.model_validate(row).model_dump()})
    return row

@router.get("/recent", response_model=list[TelemetryOut])
async def recent(limit: int = 50, session: AsyncSession = Depends(get_session)):
    rows = await telemetry_service.recent(session, limit=limit)
    return [TelemetryOut.model_validate(r) for r in rows]
