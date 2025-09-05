from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Float, String, DateTime
from datetime import datetime
from typing import Optional
from app.db.base import Base

class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    z: Mapped[float] = mapped_column(Float)
    slope: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
