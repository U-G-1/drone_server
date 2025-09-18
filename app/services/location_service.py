from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.location import Location

async def _next_chim_num(session: AsyncSession, chim_name: str) -> int:
    res = await session.execute(
        select(func.max(Location.chim_num)).where(Location.chim_name == chim_name)
    )
    maxnum = res.scalar()
    return (maxnum or 0) + 1

async def create_location(
    session: AsyncSession,
    *,
    loca_x: float,
    loca_y: float,
    loca_z: float,
    slope: Optional[float],
    chim_name: str,
) -> Location:
    chim_num = await _next_chim_num(session, chim_name)
    row = Location(
        loca_x=loca_x,
        loca_y=loca_y,
        loca_z=loca_z,
        slope=slope,
        chim_name=chim_name,
        chim_num=chim_num,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
