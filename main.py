from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse

# main.py 상단 import
from fastapi import Request


from app.core.config import settings
from app.db.init_db import init_db
from app.routers import telemetry, flight, health
from app.ws.endpoints import ws_router
from app.routers import save_location
from app.routers import move_drone
from app.services.telemetry_stream import streamer
from app.routers import telemetry_read


app = FastAPI(title="Drone Control API", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router, prefix="")
app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
app.include_router(flight.router, prefix="", tags=["flight"])
app.include_router(ws_router, prefix="", tags=["ws"])
app.include_router(save_location.router)
app.include_router(move_drone.router)
app.include_router(telemetry_read.router)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def _trace_measure(request: Request, call_next):
    if request.url.path == "/saveLocation/measure":
        print("=== MEASURE CALLED ===")
        print("Referer:", request.headers.get("referer"))
        print("UA     :", request.headers.get("user-agent"))
        print("Client :", request.client)
    return await call_next(request)

@app.get("/", include_in_schema=False)
def home_file():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.on_event("startup")
async def on_startup():
    await init_db()
    streamer.start()   # 실시간 좌표 스트리머 시작

@app.on_event("shutdown")
async def on_shutdown():
    await streamer.stop()


