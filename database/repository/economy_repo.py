from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import EconomyLog
from database.repository.base import BaseRepository

class EconomyRepository(BaseRepository[EconomyLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, EconomyLog)

    async def record_transaction(
        self, user_id: int, transaction_type: str,
        give_resource: str = None, give_amount: int = None,
        receive_resource: str = None, receive_amount: int = None
    ) -> EconomyLog:
        log = EconomyLog(
            user_id=user_id, transaction_type=transaction_type,
            give_resource=give_resource, give_amount=give_amount,
            receive_resource=receive_resource, receive_amount=receive_amount,
            created_at=datetime.utcnow()
        )
        return await self.create(log)

    async def get_user_transactions(self, user_id: int, limit: int = 50) -> List[EconomyLog]:
        result = await self.session.execute(
            select(EconomyLog).where(EconomyLog.user_id == user_id)
            .limit(limit)
        )
        return list(result.scalars().all())