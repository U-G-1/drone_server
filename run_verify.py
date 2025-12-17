# run_verify.py
"""
검증(verification) 전용 실행 엔트리포인트.

- 기존 서버 코드는 그대로 두고(main.py 수정 없이)
- raw(혼재) vs normalized(정리) 텔레메트리 결과를 같은 WebSocket(/ws)로 동시에 브로드캐스트
- 검증용 UI(/verify)에서 두 결과를 한 화면에 표시

실행:
  uvicorn run_verify:app --reload --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from fastapi.responses import FileResponse

# 기존 앱(라우터/WS/정적 mount/기존 streamer.start 포함)을 그대로 재사용
import main as base_main

from app.services.verify_stream import verify_streamer

app = base_main.app
BASE_DIR = Path(__file__).resolve().parent


@app.get("/verify", include_in_schema=False)
def verify_page():
    return FileResponse(BASE_DIR / "static" / "verify.html")


@app.on_event("startup")
async def _startup_verify():
    # base_main의 startup은 이미 등록되어 자동 실행됨.
    # 여기서는 검증 스트리머만 추가 실행.
    verify_streamer.start()


@app.on_event("shutdown")
async def _shutdown_verify():
    await verify_streamer.stop()
