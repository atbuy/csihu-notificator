from sqlalchemy import insert, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncEngine

from csihu.db.models import Announcements
from csihu.helpers import Announcement
from csihu.logger import log


async def add_announcement(engine: AsyncEngine, announcement: Announcement) -> None:
    """Add the announcement to the database."""

    query = insert(Announcements).values(**dict(announcement))
    async with engine.begin() as conn:
        await conn.execute(query)


async def get_latest_announcement(engine: AsyncEngine) -> Announcement:
    """Get the latest announcement from the database."""

    query = select(Announcements).order_by(Announcements.id.desc())
    async with engine.begin() as conn:
        result: Row = await conn.execute(query)
        log(f"{result}, {type(result)}")
        row = result.first()
        log(f"{row}, {type(row)}")
        if not row:
            return Announcement(id=-1, title="", description="", link="")
        return Announcement(**dict(row))
