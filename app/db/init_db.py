from app.db.session import engine
from app.db.base import Base
from app.models import telemetry, flight_log  # noqa
from app.models import location  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
