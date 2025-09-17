from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.init_db import init_db
from app.routers import telemetry, flight, health
from app.ws.endpoints import ws_router
from app.routers import save_location
from app.routers import move_drone


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


@app.on_event("startup")
async def on_startup():
    await init_db()
