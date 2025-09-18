# app/models/location.py
from sqlalchemy import Integer, String, DECIMAL, DateTime, text
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

    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        # 파이썬 기본값 + SQLite 기본값 둘 다 지정
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP")
    )
