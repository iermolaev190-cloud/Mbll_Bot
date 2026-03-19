from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.character_repo import CharacterRepository
from config.character_config import CHARACTERS
from config.game_config import MAX_CHARACTER_LEVEL, EXP_FOR_LEVEL_UP

class CharacterService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_repo = CharacterRepository(session)

    async def get_character_info(self, character_id: int) -> Optional[Dict]:
        """
        Получить информацию о персонаже
        Возвращает словарь с данными или None, если персонаж не найден
        """
        character = await self.character_repo.get_by_id(character_id)
        if not character:
            return None

        char_data = CHARACTERS.get(character.character_type)
        if not char_data:
            return None

        exp_needed = EXP_FOR_LEVEL_UP(character.level)

        return {
            "id": character.id,
            "name": char_data.name,
            "character_type": character.character_type,
            "level": character.level,
            "experience": character.experience,
            "rarity": char_data.rarity,
            "element": char_data.element,
            "hp": character.current_hp,
            "max_hp": character.max_hp,
            "damage": character.base_damage,
            "armor": character.base_armor,
            "agility": character.base_agility,
            "intelligence": character.base_intelligence,
            "is_in_team": character.is_in_team,
            "is_on_farm": character.is_on_farm,
            "battle_wins": character.battle_wins,
            "battle_losses": character.battle_losses,
            "exp_next": exp_needed,
        }

    async def get_player_characters(self, user_id: int) -> list:
        """Получить всех персонажей игрока"""
        characters = await self.character_repo.get_by_owner(user_id)
        result = []
        for char in characters:
            info = await self.get_character_info(char.id)
            if info:
                result.append(info)
        return result

    async def add_battle_record(self, character_id: int, won: bool):
        """Добавить запись о бое"""
        character = await self.character_repo.get_by_id(character_id)
        if character:
            if won:
                character.battle_wins += 1
            else:
                character.battle_losses += 1
            await self.character_repo.update(character)

    async def check_level_up(self, character_id: int) -> bool:
        """Проверить и выполнить повышение уровня"""
        character = await self.character_repo.get_by_id(character_id)
        if not character:
            return False

        exp_needed = EXP_FOR_LEVEL_UP(character.level)
        if character.experience >= exp_needed and character.level < MAX_CHARACTER_LEVEL:
            await self.character_repo.level_up(character_id)
            return True
        return False