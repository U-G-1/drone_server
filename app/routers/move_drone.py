import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.services.location_service import list_chimneys, coordinates_by_chimney
from app.ws.hub import hub  # 기존 허브 재사용 (type 필드로 구분)

router = APIRouter(prefix="/moveDrone", tags=["moveDrone"])

async def get_session():
    async with SessionLocal() as s:
        yield s

# 1) 굴뚝 목록
class ChimneysOut(BaseModel):
    chimneys: List[str]

@router.get("/chimneys", response_model=ChimneysOut)
async def get_chimneys(session: AsyncSession = Depends(get_session)):
    names = await list_chimneys(session)
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

    coords = await coordinates_by_chimney(session, chim_name)
    if not coords:
        raise HTTPException(status_code=404, detail="No points for this chimney")

    # pyCode/move_drone.py 에 좌표를 x y z x y z ... 평탄화해서 전달
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
            # 콘솔을 모든 클라이언트로 브로드캐스트
            await hub.broadcast({"type": "consoleMessage", "data": f"[{tag}] {msg}"})

    # 표준출력/표준에러 동시에 읽어 브로드캐스트
    await asyncio.gather(_pump(proc.stdout, "stdout"), _pump(proc.stderr, "stderr"))
    rc = await proc.wait()
    await hub.broadcast({"type": "consoleMessage", "data": f"[move] exit code {rc}"})

    if rc != 0:
        raise HTTPException(status_code=500, detail=f"move script failed rc={rc}")

    return MoveOut(ok=True)
