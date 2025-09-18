# app/models/location.py
from sqlalchemy import Integer, String, DECIMAL, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

class Location(Base):
    __tablename__ = "location"

    uid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loca_x: Mapped[float] = mapped_column(DECIMAL(40, 20), nullable=False)
    loca_y: Mapped[float] = mapped_column(DECIMAL(40, 20), nullable=False)
    loca_z: Mapped[float] = mapped_column(DECIMAL(40, 20), nullable=False)
    slope: Mapped[float | None] = mapped_column(DECIMAL(40, 20), nullable=True)
    chim_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chim_num: Mapped[int] = mapped_column(Integer, nullable=False)

    # 핵심: 파이썬 기본값 + SQLite 서버 기본값을 둘 다 지정
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),             # Python-side default
        server_default=text("CURRENT_TIMESTAMP")                # SQLite-side default
    )
