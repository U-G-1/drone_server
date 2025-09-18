from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.db.init_db import init_db
from app.ws.endpoints import ws_router
from app.routers import health, telemetry, telemetry_read
from app.services.telemetry_stream import streamer
from app.routers import test_control
from app.routers import move_drone

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Drone Control API", version="0.1.0")

# 정적 파일 (절대경로로 고정)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터
app.include_router(health.router)
app.include_router(ws_router)
app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
app.include_router(telemetry_read.router, prefix="/telemetry", tags=["telemetry"])
app.include_router(test_control.router)
app.include_router(move_drone.router)

# 홈
@app.get("/", include_in_schema=False)
def home_file():
    return FileResponse(BASE_DIR / "static" / "index.html")

# (안전장치) 과거 폴링 경로를 강제로 차단
@app.api_route("/saveLocation/measure", methods=["GET", "POST"])
async def _kill_measure(request: Request):
    return JSONResponse({"detail": "measure disabled"}, status_code=410)

# 수명주기
@app.on_event("startup")
async def on_startup():
    await init_db()
    streamer.start()     # MAVSDK(또는 FAKE) → WS로 계속 브로드캐스트

@app.on_event("shutdown")
async def on_shutdown():
    await streamer.stop()
