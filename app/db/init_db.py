from app.db.session import engine
from app.db.base import Base
from app.models.location import Location  # noqa

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
