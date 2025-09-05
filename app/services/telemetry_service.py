from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.telemetry import Telemetry

async def create(session: AsyncSession, **data) -> Telemetry:
    row = Telemetry(**data)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row

async def recent(session: AsyncSession, limit: int = 50) -> list[Telemetry]:
    stmt = select(Telemetry).order_by(Telemetry.id.desc()).limit(limit)
    rows = (await session.scalars(stmt)).all()
    return list(reversed(rows))
