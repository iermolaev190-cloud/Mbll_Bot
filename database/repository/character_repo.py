from typing import List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Character
from database.repository.base import BaseRepository
from config.character_config import get_character, RARITY_STAT_MULTIPLIER
from config.game_config import MAX_CHARACTER_LEVEL


class CharacterRepository(BaseRepository[Character]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Character)

    async def get_by_owner(self, owner_id: int) -> List[Character]:
        result = await self.session.execute(
            select(Character).where(Character.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def get_team(self, owner_id: int) -> List[Character]:
        result = await self.session.execute(
            select(Character).where(
                Character.owner_id == owner_id,
                Character.is_in_team == True
            )
        )
        return list(result.scalars().all())

    async def create_character(self, owner_id: int, character_type: str, level: int = 1) -> Character:
        char_data = get_character(character_type)
        if not char_data:
            raise ValueError(f"Unknown character type: {character_type}")

        rarity = char_data.rarity
        multiplier = RARITY_STAT_MULTIPLIER.get(rarity, 1.0)
        level_mult = 1.0 + (level - 1) * 0.05

        character = Character(
            owner_id=owner_id,
            character_type=character_type,
            level=level,
            experience=0,
            base_damage=int(char_data.base_damage * multiplier * level_mult),
            base_armor=int(char_data.base_armor * multiplier * level_mult),
            base_agility=int(char_data.base_agility * multiplier * level_mult),
            base_intelligence=int(char_data.base_intelligence * multiplier * level_mult),
            max_hp=int(char_data.base_hp * multiplier * level_mult),
            current_hp=int(char_data.base_hp * multiplier * level_mult),
            is_on_farm=False,
            is_in_team=False,
        )
        return await self.create(character)

    async def get_available_for_team(self, owner_id: int) -> List[Character]:
        result = await self.session.execute(
            select(Character).where(
                Character.owner_id == owner_id,
                Character.is_on_farm == False,
                Character.is_in_team == False
            )
        )
        return list(result.scalars().all())

    async def set_team(self, owner_id: int, character_ids: List[int]) -> bool:

        await self.session.execute(
            update(Character)
            .where(Character.owner_id == owner_id)
            .values(is_in_team=False)
        )

        if character_ids:
            await self.session.execute(
                update(Character)
                .where(Character.id.in_(character_ids))
                .values(is_in_team=True)
            )

        await self.session.commit()
        return True

    async def get_total_characters_count(self) -> int:
        result = await self.session.execute(select(Character))
        return len(list(result.scalars().all()))

    async def add_experience(self, character_id: int, amount: int):
        character = await self.get_by_id(character_id)
        if character:
            character.experience += amount
            await self.update(character)

    async def level_up(self, character_id: int):
        character = await self.get_by_id(character_id)
        if character and character.level < MAX_CHARACTER_LEVEL:
            character.level += 1
            character.experience = 0
            multiplier = 1.05
            character.max_hp = int(character.max_hp * multiplier)
            character.current_hp = character.max_hp
            character.base_damage = int(character.base_damage * multiplier)
            character.base_armor = int(character.base_armor * multiplier)
            await self.update(character)

    async def add_battle_record(self, character_id: int, won: bool):
        character = await self.get_by_id(character_id)
        if character:
            if won:
                character.battle_wins += 1
            else:
                character.battle_losses += 1
            await self.update(character)