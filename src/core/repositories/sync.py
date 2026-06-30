from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import SyncMetadata


class SyncRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> SyncMetadata:
        result = await self.session.execute(select(SyncMetadata).where(SyncMetadata.id == 1))
        meta = result.scalar_one_or_none()
        if meta is None:
            meta = SyncMetadata(id=1)
            self.session.add(meta)
            await self.session.commit()
        return meta

    async def update(self, last_changed_at: str, sync_status: str = "idle") -> None:
        meta = await self.get()
        if "T" in last_changed_at:
            last_changed_at = last_changed_at[:10]
        meta.last_changed_at = last_changed_at
        meta.sync_status = sync_status

        if sync_status == "running":
            meta.last_sync_started_at = datetime.now(timezone.utc)
        else:
            meta.last_sync_completed_at = datetime.now(timezone.utc)

        await self.session.commit()