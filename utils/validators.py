from config.game_config import MIN_MARKET_PRICE, MAX_MARKET_PRICE, MAX_CHARACTER_LEVEL

def validate_price(price: int) -> bool:
    return MIN_MARKET_PRICE <= price <= MAX_MARKET_PRICE

def validate_character_level(level: int) -> bool:
    return 1 <= level <= MAX_CHARACTER_LEVEL

def validate_team_size(team: list, required_size: int = 3) -> bool:
    return len(team) == required_size

def validate_slot_number(slot_num: int, max_slots: int = 9) -> bool:
    return 1 <= slot_num <= max_slots