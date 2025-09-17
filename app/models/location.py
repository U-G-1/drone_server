from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Float, String, DateTime, UniqueConstraint
from datetime import datetime
from typing import Optional
from app.db.base import Base

class Location(Base):
    __tablename__ = "location"

    uid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 좌표
    loca_x: Mapped[float] = mapped_column(Float)
    loca_y: Mapped[float] = mapped_column(Float)
    loca_z: Mapped[float] = mapped_column(Float)

    # 선택 값
    slope: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 그룹핑 키
    chim_name: Mapped[str] = mapped_column(String(100))
    chim_num: Mapped[int] = mapped_column(Integer)

    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("chim_name", "chim_num", name="ux_chim_name_num"),
    )
