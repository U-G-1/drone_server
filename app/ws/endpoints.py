from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.hub import hub

ws_router = APIRouter()

@ws_router.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            # 클라에서 오는 메시지는 안 씀. 핑퐁만 유지
            await ws.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(ws)
