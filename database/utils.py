from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from services.farm_service import FarmService

async def get_user_or_create(session: AsyncSession, user_id: int, username: str = None, first_name: str = None):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(user_id)
    if not user:
        try:
            user = await user_repo.get_or_create(user_id, username, first_name)
            if user:
                farm_service = FarmService(session)
                await farm_service.initialize_farm(user.id)
                char_repo = CharacterRepository(session)
                await char_repo.create_character(user.id, "layla", level=1)
                await session.commit()
        except Exception as e:
            print(f"Ошибка создания пользователя {user_id}: {e}")
            return None
    return user
