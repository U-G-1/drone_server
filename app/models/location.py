from sqlalchemy import Integer, String, DECIMAL, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Location(Base):
    __tablename__ = "location"

    uid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loca_x: Mapped[float] = mapped_column(DECIMAL(40, 20), nullable=False)
    loca_y: Mapped[float] = mapped_column(DECIMAL(40, 20), nullable=False)
    loca_z: Mapped[float] = mapped_column(DECIMAL(40, 20), nullable=False)
    slope: Mapped[float | None] = mapped_column(DECIMAL(40, 20), nullable=True)
    chim_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chim_num: Mapped[int] = mapped_column(Integer, nullable=False)
    ts: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
