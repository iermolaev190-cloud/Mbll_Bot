def format_balance(coins: int, crystals: int, diamonds: int) -> str:
    return f"💰 {coins:,} | 💎 {crystals:,} | 💠 {diamonds:,}"

def format_character_stats(char_info: dict) -> str:
    return f"""❤️ {char_info['hp']}/{char_info['max_hp']} | 🗡️ {char_info['damage']} | 🛡️ {char_info['armor']}"""

def format_progress_bar(current: int, max_val: int, length: int = 10) -> str:
    filled = int(length * current / max_val)
    return "█" * filled + "░" * (length - filled)

def format_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        return f"{seconds // 60}м"
    else:
        return f"{seconds // 3600}ч"