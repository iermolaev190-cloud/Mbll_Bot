from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import BattleLog
from database.repository.base import BaseRepository

class BattleRepository(BaseRepository[BattleLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BattleLog)

    async def record_battle(
        self, player_id: int, opponent_id: Optional[int], player_won: bool,
        player_team: str, opponent_team: str, coins_earned: int = 0,
        crystals_earned: int = 0, is_pve: bool = False, pve_type: str = None
    ) -> BattleLog:
        battle = BattleLog(
            player_id=player_id, opponent_id=opponent_id, player_won=player_won,
            player_team=player_team, opponent_team=opponent_team,
            coins_earned=coins_earned, crystals_earned=crystals_earned,
            is_pve=is_pve, pve_type=pve_type, battle_date=datetime.utcnow()
        )
        return await self.create(battle)

    async def get_battles_by_player(self, player_id: int, limit: int = 10) -> List[BattleLog]:
        result = await self.session.execute(
            select(BattleLog).where(BattleLog.player_id == player_id)
            .order_by(desc(BattleLog.battle_date)).limit(limit)
        )
        return list(result.scalars().all())

    async def get_wins_count(self, player_id: int) -> int:
        result = await self.session.execute(
            select(BattleLog).where(
                BattleLog.player_id == player_id, BattleLog.player_won == True
            )
        )
        return len(result.scalars().all())

    async def check_cooldown(self, player_id: int, cooldown_timedelta: timedelta) -> bool:
        result = await self.session.execute(
            select(BattleLog).where(BattleLog.player_id == player_id)
            .order_by(desc(BattleLog.battle_date)).limit(1)
        )
        last_battle = result.scalars().first()
        if not last_battle:
            return True
        time_since = datetime.utcnow() - last_battle.battle_date
        return time_since >= cooldown_timedelta

    async def get_total_battles_count(self) -> int:
        result = await self.session.execute(select(BattleLog))
        return len(list(result.scalars().all()))

    async def get_week_wins(self, player_id: int) -> int:
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.session.execute(
            select(BattleLog).where(
                BattleLog.player_id == player_id,
                BattleLog.player_won == True,
                BattleLog.battle_date >= week_ago
            )
        )
        return len(list(result.scalars().all()))