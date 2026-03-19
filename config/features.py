FEATURES = {
    "daily_events": True,
    "farm_spirit": True,
    "weather_system": True,

    "dynamic_characters": True,
    "mood_profile": True,

    "smart_pve": True,
    "battle_trash_talk": True,

    "casino_talk": True,
    "casino_personality": True,

    "market_talk": True,
    "market_gossip": True,

    "daily_quests": True,
    "reputation": True,
}

FEATURE_CONFIG = {
    "weather_update_hours": 3,

    "max_daily_quests": 3,

 "reputation_bonuses": {
        "low": {
            "market_discount": 0,
            "farm_bonus": 0,
            "casino_luck": 0,
            "battle_exp": 0
        },
        "medium": {
            "market_discount": 5,
            "farm_bonus": 10,
            "casino_luck": 5,
            "battle_exp": 5
        },
        "high": {
            "market_discount": 10,
            "farm_bonus": 20,
            "casino_luck": 10,
            "battle_exp": 10
        },
        "very_high": {
            "market_discount": 15,
            "farm_bonus": 30,
            "casino_luck": 15,
            "battle_exp": 20
        }
    },
}