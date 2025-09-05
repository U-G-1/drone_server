from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.hub import hub

ws_router = APIRouter()

@ws_router.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(ws)
