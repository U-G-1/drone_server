import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.services.location_service import list_chimneys, coordinates_by_chimney
from app.ws.hub import hub  # 콘솔/텔레메트리 브로드캐스트 허브

router = APIRouter(prefix="/moveDrone", tags=["moveDrone"])

async def get_session():
    async with SessionLocal() as s:
        yield s

# 1) 굴뚝 목록
class ChimneysOut(BaseModel):
    chimneys: List[str]

@router.get("/chimneys", response_model=ChimneysOut)
async def get_chimneys(session: AsyncSession = Depends(get_session)):
    names = await list_chimneys(session)  # 중복 없이 정렬된 chim_name 목록
    return ChimneysOut(chimneys=names)

# 2) 이동 실행
class MoveIn(BaseModel):
    chimney: str  # 선택된 굴뚝 이름

class MoveOut(BaseModel):
    ok: bool

@router.post("/move", response_model=MoveOut)
async def move_drone(body: MoveIn, session: AsyncSession = Depends(get_session)):
    chim_name = body.chimney.strip()
    if not chim_name:
        raise HTTPException(status_code=400, detail="chimney is required")

    # 같은 chim_name의 좌표를 chim_num ASC로 반환 (서비스에서 정렬 보장)
    coords = await coordinates_by_chimney(session, chim_name)
    if not coords:
        raise HTTPException(status_code=404, detail="No points for this chimney")

    # x y z x y z ...
    args = []
    for (x, y, z) in coords:
        args.extend([str(x), str(y), str(z)])

    await hub.broadcast({"type": "consoleMessage", "data": f"[move] chimney={chim_name}, points={len(coords)}"})

    proc = await asyncio.create_subprocess_exec(
        "python3", "-u", "pyCode/move_drone.py", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _pump(reader, tag: str):
        while True:
            line = await reader.readline()
            if not line:
                break
            msg = line.decode(errors="ignore").rstrip()
            await hub.broadcast({"type": "consoleMessage", "data": f"[{tag}] {msg}"})

    await asyncio.gather(_pump(proc.stdout, "stdout"), _pump(proc.stderr, "stderr"))
    rc = await proc.wait()
    await hub.broadcast({"type": "consoleMessage", "data": f"[move] exit code {rc}"})

    if rc != 0:
        raise HTTPException(status_code=500, detail=f"move script failed rc={rc}")

    return MoveOut(ok=True)
