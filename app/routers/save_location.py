from pathlib import Path
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.location_service import create_location

router = APIRouter(prefix="/saveLocation", tags=["saveLocation"])

BASE_DIR = Path(__file__).resolve().parents[2]  # drone_server/ 루트

async def get_session():
    async with SessionLocal() as s:
        yield s

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
    chimneyNumber: Optional[str] = None

@router.post("/")
async def set_chimney(body: SetChimneyIn, response: Response):
    response.set_cookie("chimneyNumber", body.chimneyNumber, httponly=True, max_age=86400, samesite="lax")
    return {"ok": True}

@router.post("/measure_DISABLED", response_model=MeasureOut)
async def measure():
    script = BASE_DIR / "pyCode" / "save_location.py"
    if not script.exists():
        # 경로 문제를 바로 알 수 있게 상세 에러 제공
        raise HTTPException(status_code=500, detail=f"script not found: {script}")

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-u", str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"spawn failed: {e}")

    out, err = await proc.communicate()
    if proc.returncode != 0:
        # mavsdk 미설치/PX4 미실행 등 stderr를 그대로 보여줌
        raise HTTPException(status_code=503, detail=f"measure failed (rc={proc.returncode}): {err.decode(errors='ignore')}")

    lines = [ln.strip() for ln in out.decode().splitlines() if ln.strip()]
    if len(lines) < 3:
        raise HTTPException(status_code=500, detail=f"unexpected output: {lines}")

    try:
        x = float(lines[0]); y = float(lines[1]); z = float(lines[2])
    except ValueError:
        raise HTTPException(status_code=500, detail=f"cannot parse floats: {lines[:3]}")

    return MeasureOut(values=lines, x=x, y=y, z=z)

@router.post("/add")
async def add(body: AddIn, session: AsyncSession = Depends(get_session), chimneyNumber_cookie: Optional[str] = Cookie(None)):
    chim_name = body.chimneyNumber or chimneyNumber_cookie
    if not chim_name:
        raise HTTPException(status_code=400, detail="chimneyNumber not provided (cookie or body).")

    row = await create_location(session, loca_x=body.loca_x, loca_y=body.loca_y, loca_z=body.loca_z, slope=body.slope, chim_name=chim_name)
    return {"ok": True, "uid": row.uid, "chim_name": row.chim_name, "chim_num": row.chim_num, "ts": row.ts.isoformat()}

@router.post("/save")
async def save_final(body: AddIn, session: AsyncSession = Depends(get_session), chimneyNumber_cookie: Optional[str] = Cookie(None)):
    chim_name = body.chimneyNumber or chimneyNumber_cookie
    if not chim_name:
        raise HTTPException(status_code=400, detail="chimneyNumber not provided (cookie or body).")

    row = await create_location(session, loca_x=body.loca_x, loca_y=body.loca_y, loca_z=body.loca_z, slope=body.slope, chim_name=chim_name)
    return {"ok": True, "redirect": "/"}
