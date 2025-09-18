# app/services/location_service.py
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.location import Location
from datetime import datetime, timezone   # ← 추가
from typing import List

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
        ts=datetime.now(timezone.utc),   
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_chimneys(session: AsyncSession) -> Optional[str]:
    """
    저장된 chim_name 목록을 중복 없이 정렬해서 반환
    """
    q = select(Location.chim_name).group_by(Location.chim_name).order_by(Location.chim_name.asc())
    rows = (await session.execute(q)).scalars().all()
    return rows

async def coordinates_by_chimney(session: AsyncSession, chim_name: str) -> Optional[Tuple[float, float, float]]:
    """
    해당 chim_name의 코스를 chim_num 오름차순으로 (x,y,z) 목록으로 반환
    """
    q = (
        select(Location.loca_x, Location.loca_y, Location.loca_z)
        .where(Location.chim_name == chim_name)
        .order_by(Location.chim_num.asc())
    )
    rows = (await session.execute(q)).all()  # list[Row]
    return [(float(x), float(y), float(z)) for (x, y, z) in rows]