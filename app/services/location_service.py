from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.location import Location

async def next_chim_num(session: AsyncSession, chim_name: str) -> int:
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
    chim_num = await next_chim_num(session, chim_name)
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

# === 여기부터 moveDrone용 추가 ===

async def list_chimneys(session: AsyncSession) -> List[str]:
    q = select(Location.chim_name).group_by(Location.chim_name).order_by(Location.chim_name.asc())
    rows = (await session.execute(q)).scalars().all()
    return rows

async def coordinates_by_chimney(session: AsyncSession, chim_name: str) -> List[Tuple[float, float, float]]:
    q = (
        select(Location.loca_x, Location.loca_y, Location.loca_z)
        .where(Location.chim_name == chim_name)
        .order_by(Location.chim_num.asc())
    )
    rows = (await session.execute(q)).all()
    # rows: list[Row(loca_x, loca_y, loca_z)] → tuple list로 변환
    return [(float(x), float(y), float(z)) for (x, y, z) in rows]
