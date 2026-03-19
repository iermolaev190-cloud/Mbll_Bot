from datetime import timedelta

PLANT_GROWTH_STAGES = {
    "seed": {"duration": timedelta(hours=1, minutes=45), "name": "🥚 Яйцо"},
    "sprout": {"duration": timedelta(hours=1, minutes=45), "name": "🐣 Росток"},
    "teenager": {"duration": timedelta(hours=1, minutes=45), "name": "🐥 Птенец"},
    "adult": {"duration": timedelta(hours=1, minutes=45), "name": "🐔 Взрослый"},
}

FARM_SLOTS = 9
PLANT_WATER_INTERVAL = timedelta(hours=2)

HARVEST_RARITY_CHANCE = {
    "common": 0.40, "uncommon": 0.30, "rare": 0.15,
    "epic": 0.10, "legendary": 0.04, "mythical": 0.01,
}

BATTLE_TEAM_SIZE = 3
ARENA_REWARD_COINS = {"win": 100, "loss": 0}
ARENA_REWARD_CRYSTALS = {"win": 1, "loss": 0}
PVE_REWARD_COINS = {"win": 100, "loss": 50}
PVE_REWARD_CRYSTALS = {"win": 1, "loss": 0}

BASE_WIN_CHANCE = 0.50
ELEMENT_ADVANTAGE_MULTIPLIER = 1.3
ELEMENT_DISADVANTAGE_MULTIPLIER = 0.7

MIN_CHARACTER_LEVEL = 1
MAX_CHARACTER_LEVEL = 50
EXP_PER_WIN = 100
EXP_PER_LOSS = 30

def EXP_FOR_LEVEL_UP(level):
    return 500 + (level - 1) * 100

STARTING_COINS = 5000
STARTING_CRYSTALS = 10

from datetime import timedelta

EXCHANGE_RATES = {
    "coins_to_crystals": 5000,
    "coins_and_crystals_to_diamond": {
        "coins": 50000,
        "crystals": 10
    },
    "crystals_to_diamonds": 20,
}

EXCHANGE_TEXTS = {
    "coins_to_crystals": "5,000💰 → 1💎",
    "coins_and_crystals_to_diamond": "50,000💰 + 10💎 → 1💠",
    "crystals_to_diamonds": "20💎 → 1💠",
}
TOP_3_DIAMOND_REWARD = {1: 5, 2: 3, 3: 1}

MARKET_COMMISSION_PERCENT = 0.05
MARKET_MAX_LISTINGS = 20
MIN_MARKET_PRICE = 1000
MAX_MARKET_PRICE = 1000000
EGG_PRICE = 5000
SEED_PRICE = 5000

PRICES = {
    "reroll_team": 1000,
    "reset_farm": 500,
    "speed_up_growth": {"1_hour": 50, "full": 150},
}

PASSIVE_INCOME_RATE = {
    "base_per_character": 300,
    "max_storage_hours": 24,
    "collect_cooldown": 60,
}

BATTLE_COOLDOWN = timedelta(minutes=1)
DAILY_QUEST_RESET = timedelta(hours=24)

MAX_FARM_QUEUE = 100
ENABLE_ADMIN_COMMANDS = True
ENABLE_MARKET = True
ENABLE_PVE_CAMPAIGNS = True

RARITY_STAT_MULTIPLIER = {
    "common": 1.0, "uncommon": 1.15, "rare": 1.35,
    "epic": 1.65, "legendary": 2.0, "mythical": 2.5,
}

LEVEL_STAT_MULTIPLIER = 1.05

PVE_OPPONENTS = {
    "easy": {"name": "Рыцарь", "level": 5, "multiplier": 0.8},
    "medium": {"name": "Черепаха", "level": 15, "multiplier": 1.0},
    "hard": {"name": "Лорд", "level": 25, "multiplier": 1.3},
}

WEEKLY_RESET_DAY = 0
WEEKLY_RESET_HOUR = 0

PASSIVE_INCOME_RATES = {
    "common": 25,
    "uncommon": 50,
    "rare": 100,
    "epic": 175,
    "legendary": 250,
    "mythical": 500,
}

MAX_PASSIVE_HOURS = 24