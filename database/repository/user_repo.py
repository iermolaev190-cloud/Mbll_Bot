from datetime import timezone
from typing import Optional, List, Sequence
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.repository.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_or_create(self, telegram_id: int, username: str = None, first_name: str = None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name)
            user = await self.create(user)
        return user

    async def get_top_players(self, limit: int = 10) -> Sequence[User]:
        result = await self.session.execute(
            select(User).order_by(desc(User.battle_wins)).limit(limit)
        )
        return result.scalars().all()

    async def get_total_stats(self) -> dict:
        all_users = await self.get_all()
        return {
            "total_players": len(all_users),
            "total_coins": sum(u.coins for u in all_users),
            "total_crystals": sum(u.crystals for u in all_users),
            "total_diamonds": sum(u.diamonds for u in all_users),
            "total_battles": sum(u.battle_wins + u.battle_losses for u in all_users),
        }

    async def add_coins(self, user_id: int, amount: int):
        user = await self.get_by_id(user_id)
        if user:
            user.coins = max(0, user.coins + amount)
            await self.update(user)

    async def add_crystals(self, user_id: int, amount: int):
        user = await self.get_by_id(user_id)
        if user:
            user.crystals = max(0, user.crystals + amount)
            await self.update(user)

    async def add_diamonds(self, user_id: int, amount: int):
        user = await self.get_by_id(user_id)
        if user:
            user.diamonds = max(0, user.diamonds + amount)
            await self.update(user)

    async def update_last_visit(self, user_id: int):
        """Обновить время последнего визита"""
        user = await self.get_by_id(user_id)
        if user:
            user.last_visit = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.update(user)

    async def get_new_today(self) -> int:
        from datetime import timedelta
        today = datetime.utcnow() - timedelta(days=1)
        result = await self.session.execute(
            select(User).where(User.created_at >= today)
        )
        return len(result.scalars().all())

    async def ban_user(self, user_id: int, reason: str = None) -> bool:
        """Забанить пользователя"""
        print(f"🔨 БАН: пытаемся забанить пользователя {user_id}")
        user = await self.get_by_id(user_id)
        if user:
            print(f"   Найден пользователь: {user.first_name}")
            user.is_banned = True
            user.ban_reason = reason
            await self.update(user)

            check = await self.get_by_id(user_id)
            print(f"   После бана: is_banned = {check.is_banned}")
            return True
        print(f"❌ Пользователь {user_id} не найден!")
        return False

    async def unban_user(self, user_id: int) -> bool:
        """Разбанить пользователя по ВНУТРЕННЕМУ ID"""
        print(f"🔓 Разбан: пытаемся разбанить пользователя с id={user_id}")
        user = await self.get_by_id(user_id)
        if user:
            print(f"   Найден пользователь: {user.first_name}, текущий статус: {user.is_banned}")
            user.is_banned = False
            user.ban_reason = None
            await self.update(user)

            check = await self.get_by_id(user_id)
            print(f"   После разбана: is_banned = {check.is_banned}")
            return True
        print(f"❌ Пользователь с id={user_id} не найден!")
        return False

    async def get_banned_users(self) -> List[User]:
        """Получить список забаненных"""
        result = await self.session.execute(
            select(User).where(User.is_banned == True)
        )
        return list(result.scalars().all())
