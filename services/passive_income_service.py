from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from config.game_config import PASSIVE_INCOME_RATES, MAX_PASSIVE_HOURS
from config.character_config import get_character


class PassiveIncomeService:
    """Сервис пассивного дохода от персонажей"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.character_repo = CharacterRepository(session)

    async def calculate_income(self, user_id: int) -> dict:
        """Рассчитать доход в час от всех персонажей"""
        characters = await self.character_repo.get_by_owner(user_id)

        total_per_hour = 0
        income_by_rarity = {
            "common": 0,
            "uncommon": 0,
            "rare": 0,
            "epic": 0,
            "legendary": 0,
            "mythical": 0
        }

        for char in characters:
            char_data = get_character(char.character_type)
            rate = PASSIVE_INCOME_RATES.get(char_data.rarity, 10)
            total_per_hour += rate
            income_by_rarity[char_data.rarity] += rate

        return {
            "total_per_hour": total_per_hour,
            "by_rarity": income_by_rarity,
            "characters_count": len(characters)
        }

    async def collect_income(self, user_id: int) -> dict:
        """Собрать накопленный доход"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"error": "User not found"}

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        last_collect = user.last_passive_collect or user.created_at

        seconds_passed = (now - last_collect).total_seconds()
        hours_passed = seconds_passed / 3600

        if hours_passed > MAX_PASSIVE_HOURS:
            hours_passed = MAX_PASSIVE_HOURS
            last_collect = now - timedelta(hours=MAX_PASSIVE_HOURS)

        if hours_passed < 0.0167:
            return {
                "error": "too_soon",
                "seconds_left": 60 - int(seconds_passed),
                "collected": 0
            }

        income_info = await self.calculate_income(user_id)
        earned = int(income_info["total_per_hour"] * hours_passed)

        if earned > 0:
            user.coins += earned
            user.last_passive_collect = now
            await self.user_repo.update(user)

        return {
            "success": True,
            "collected": earned,
            "hours_passed": round(hours_passed, 1),
            "total_per_hour": income_info["total_per_hour"],
            "new_balance": user.coins
        }