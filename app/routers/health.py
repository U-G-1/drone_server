from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}
