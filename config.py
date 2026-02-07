from pydantic import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    admin_id: int
    database_url: str
    log_level: str = "INFO"
    debug_mode: bool = False
    max_farm_slots: int = 9
    max_team_size: int = 3
    daily_quest_limit: int = 5
    market_commission: float = 0.05  # 5%
    starting_coins: int = 1000
    starting_crystals: int = 50
    character_growth_hours: int = 24
    battle_cooldown_seconds: int = 60
    quest_reset_hour: int = 0
    character_types: list = [
        'Fire Dragon', 'Water Serpent', 'Earth Golem', 'Air Phoenix', 'Light Unicorn', 
        'Dark Wolf', 'Electric Tiger', 'Ice Yeti', 'Nature Dryad', 'Metal Knight', 
        'Poison Scorpion', 'Crystal Beetle', 'Shadow Panther', 'Holy Lion', 'Chaos Demon'
    ]
    character_rarities: list = [
        'Common', 'Rare', 'Epic', 'Legendary', 'Mythical'
    ]
    growth_stages: list = [
        'Seed', 'Sprout', 'Teen', 'Adult'
    ]
    max_character_level: int = 50

    class Config:
        env_file = '.env'