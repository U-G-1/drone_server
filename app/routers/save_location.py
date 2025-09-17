import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.location_service import create_location

router = APIRouter(prefix="/saveLocation", tags=["saveLocation"])

# ----- 의존성: 세션 -----
async def get_session():
    async with SessionLocal() as s:
        yield s

# ----- 스키마 -----
class SetChimneyIn(BaseModel):
    chimneyNumber: str

class MeasureOut(BaseModel):
    values: list[str]
    x: float
    y: float
    z: float

class AddIn(BaseModel):
    loca_x: float
    loca_y: float
    loca_z: float
    slope: Optional[float] = 0.0
    # 프론트 편의를 위해 body로도 받을 수 있게(쿠키 없을 때 대비)
    chimneyNumber: Optional[str] = None

# ----- 1) 굴뚝 번호 쿠키 설정: POST /saveLocation -----
@router.post("/")
async def set_chimney(body: SetChimneyIn, response: Response):
    response.set_cookie(
        key="chimneyNumber",
        value=body.chimneyNumber,
        httponly=True,
        max_age=24 * 60 * 60,  # 1 day
        samesite="lax",
    )
    return {"ok": True}

# ----- 2) 측정: POST /saveLocation/measure -----
# Node에서 spawn 하던 saveLocation.py를 그대로 실행해서 x,y,z 한 번 뽑아옴
@router.post("/measure", response_model=MeasureOut)
async def measure():
    proc = await asyncio.create_subprocess_exec(
        "python3", "-u", "pyCode/save_location.py",  # 파일명 스네이크케이스로 가정
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Python script failed: {err.decode()}")

    lines = [ln.strip() for ln in out.decode().splitlines() if ln.strip()]
    if len(lines) < 3:
        raise HTTPException(status_code=500, detail=f"Unexpected script output: {lines}")

    try:
        x = float(lines[0]); y = float(lines[1]); z = float(lines[2])
    except ValueError:
        raise HTTPException(status_code=500, detail=f"Cannot parse floats from: {lines[:3]}")

    return MeasureOut(values=lines, x=x, y=y, z=z)

# ----- 3) 저장(누를 때마다 INSERT): POST /saveLocation/add -----
@router.post("/add")
async def add(
    body: AddIn,
    session: AsyncSession = Depends(get_session),
    chimneyNumber_cookie: Optional[str] = Cookie(None),
):
    chim_name = body.chimneyNumber or chimneyNumber_cookie
    if not chim_name:
        raise HTTPException(status_code=400, detail="chimneyNumber not provided (cookie or body).")

    row = await create_location(
        session,
        loca_x=body.loca_x, loca_y=body.loca_y, loca_z=body.loca_z,
        slope=body.slope, chim_name=chim_name,
    )
    return {
        "ok": True,
        "uid": row.uid,
        "chim_name": row.chim_name,
        "chim_num": row.chim_num,
        "ts": row.ts.isoformat(),
    }

# ----- 4) (선택) 완료 저장: POST /saveLocation/save -----
# add와 동일하되, 프론트에서 홈으로 이동하고 싶으면 이걸로 분리해서 써도 됨.
@router.post("/save")
async def save_final(
    body: AddIn,
    session: AsyncSession = Depends(get_session),
    chimneyNumber_cookie: Optional[str] = Cookie(None),
):
    chim_name = body.chimneyNumber or chimneyNumber_cookie
    if not chim_name:
        raise HTTPException(status_code=400, detail="chimneyNumber not provided (cookie or body).")

    row = await create_location(
        session,
        loca_x=body.loca_x, loca_y=body.loca_y, loca_z=body.loca_z,
        slope=body.slope, chim_name=chim_name,
    )
    return {"ok": True, "redirect": "/"}
