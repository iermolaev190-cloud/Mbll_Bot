import random
import asyncio
import json
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import date, datetime

from config.features import FEATURES, FEATURE_CONFIG
from config.api_keys import API_KEYS, MODEL_CONFIG
from utils.cache import cache, get_daily_key, get_weather_key


class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/mbll_farm_bot",
            "X-Title": "MBLL Farm Bot"
        }
        self.model_prices = MODEL_CONFIG["openrouter"].get("prices", {})

    async def generate(
            self,
            prompt: str,
            model: str = None,
            temperature: float = 0.7,
            max_tokens: int = 300
    ) -> Optional[str]:
        """Отправить запрос к OpenRouter"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system",
                 "content": "Ты - помощник для игрового Telegram-бота. Отвечай кратко (1-2 предложения), с эмодзи, в игровом стиле."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        print(f"❌ OpenRouter error {response.status}: {error_text[:200]}")
                        return None
        except Exception as e:
            print(f"❌ OpenRouter exception: {e}")
            return None


openrouter_client = None
if API_KEYS.get("openrouter"):
    openrouter_client = OpenRouterClient(API_KEYS["openrouter"])
    print("✅ OpenRouter клиент инициализирован")


async def call_ai(prompt: str, temperature: float = 0.7, task_type: str = "general") -> Optional[str]:
    """Пробует разные модели от самой дешёвой к более дорогим"""

    if not openrouter_client:
        return None

    models_to_try = MODEL_CONFIG["openrouter"]["free_fallback"].copy()

    if task_type == "creative":
        models_to_try.insert(0, MODEL_CONFIG["openrouter"]["creative"])
    elif task_type == "fast":
        models_to_try.insert(0, MODEL_CONFIG["openrouter"]["fast"])

    seen = set()
    models_to_try = [x for x in models_to_try if not (x in seen or seen.add(x))]

    print(f"🔄 Пробуем модели: {', '.join(models_to_try[:3])}...")

    for model in models_to_try:
        try:
            result = await openrouter_client.generate(prompt, model=model, temperature=temperature)
            if result:
                print(f"✅ Успех с моделью: {model}")
                return result
        except Exception as e:
            print(f"⚠️ {model} не сработала")
            continue

    print("❌ Все модели недоступны")
    return None


FALLBACK_EVENTS = [
    {
        "description": "🌙 Магический туман окутал ферму. Растения светятся в темноте!",
        "bonuses": ["+25% скорость роста", "Шанс найти редкое семя +10%"]
    },
    {
        "description": "🌈 После дождя появилась двойная радуга. Феи танцуют на грядках!",
        "bonuses": ["Урожай +30%", "Все поливы бесплатны сегодня"]
    },
]



async def get_daily_event() -> Optional[Dict]:
    """Генерирует событие дня на ферме"""
    if not FEATURES.get("daily_events"):
        return None

    cache_key = get_daily_key("farm_event")
    cached = cache.get(cache_key)
    if cached:
        return cached

    prompt = """Придумай событие для фэнтези фермы.
    Формат JSON (строго):
    {"description": "описание с эмодзи", "bonuses": ["бонус1", "бонус2"]}

    Пример: {"description": "🌙 Магический туман...", "bonuses": ["+25% скорость", "+10% удача"]}"""

    response = await call_ai(prompt, temperature=0.8)

    result = None
    if response:
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
        except:
            pass

    if not result:
        result = random.choice(FALLBACK_EVENTS)

    cache.set(cache_key, result, ttl_seconds=24 * 3600)
    return result


async def get_spirit_message() -> Optional[str]:
    """Получить сообщение от духа фермы"""
    if not FEATURES.get("farm_spirit"):
        return None

    if random.random() > 0.3:
        return None

    prompt = "Напиши короткое забавное сообщение (1 предложение) от 'Духа фермы' с эмодзи. Он дружелюбный и странный."

    response = await call_ai(prompt, temperature=0.9, task_type="creative")

    if response:
        return f"🌱 *Дух фермы:* {response.strip()}"

    fallback = [
        "🌱 *Дух фермы:* 'Я видел, как ты поливал растения ночью. Ты хороший хозяин!'",
        "🌱 *Дух фермы:* 'Сегодня странный день. Куры несут золотые яйца... ну, почти золотые.'",
    ]
    return random.choice(fallback)


async def generate_character_story(character_name: str, rarity: str, element: str) -> Dict:
    """Генерирует историю для персонажа"""
    if not FEATURES.get("dynamic_characters"):
        return {"story": f"Таинственный {character_name}", "ability": "✨ Скрытая сила"}

    prompt = f"""Придумай историю для персонажа {character_name} (редкость: {rarity}, стихия: {element}).
    Формат JSON:
    {{"story": "короткая история (1 предложение)", "ability": "способность (коротко)"}}"""

    response = await call_ai(prompt, temperature=0.8, task_type="creative")

    if response:
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

    return {
        "story": f"{character_name} появился из магического яйца в день редкого звездопада.",
        "ability": f"✨ Дарует удачу в {element}ных битвах"
    }


async def get_casino_message(message_type: str) -> str:
    """Получить сообщение от крупье"""
    if not FEATURES.get("casino_talk"):
        return ""

    prompt = f"Напиши короткую фразу крупье в казино ({message_type}). 1 предложение, с эмодзи."

    response = await call_ai(prompt, temperature=0.9, task_type="creative")

    if response:
        return f"🎰 *Крупье:* {response.strip()}"

    messages = {
        "welcome": "🎰 *Крупье:* 'Добро пожаловать в наше казино! Удача сегодня на твоей стороне?'",
        "win": "🎰 *Крупье:* 'НЕВЕРОЯТНО! Ты побил рекорд заведения!'",
        "lose": "🎰 *Крупье:* 'Не расстраивайся! Фортуна переменчива.'"
    }
    return messages.get(message_type, "")


async def get_market_message(message_type: str) -> str:
    """Получить сообщение от торговца"""
    if not FEATURES.get("market_talk"):
        return ""

    prompt = f"Напиши короткую фразу торговца на рынке ({message_type}). 1 предложение, с эмодзи, он хитрый."

    response = await call_ai(prompt, temperature=0.9, task_type="creative")

    if response:
        return f"🏪 *Торговец:* {response.strip()}"

    messages = {
        "welcome": "🏪 *Торговец:* 'Заходи, не пожалеешь! Сегодня особенные цены!'",
        "gossip": "🏪 *Торговец:* 'Слышал, на севере нашли легендарного персонажа...'"
    }
    return messages.get(message_type, "")



async def get_mood_message(user_data: Dict) -> Optional[str]:
    """Генерирует сообщение о настроении на основе действий"""
    if not FEATURES.get("mood_profile"):
        return None

    wins = user_data.get("battle_wins", 0)
    losses = user_data.get("battle_losses", 0)
    coins = user_data.get("coins", 0)

    mood = "нейтральное"
    if wins > losses * 2:
        mood = "победное"
    elif losses > wins * 2:
        mood = "унылое"
    elif coins > 100000:
        mood = "богатое"

    prompt = f"Напиши короткое сообщение (1 предложение) о настроении игрока. У игрока {mood} настроение. Статистика: {wins} побед, {losses} поражений, {coins} монет."

    response = await call_ai(prompt, temperature=0.8, task_type="general")

    if response:
        return response.strip()

    moods = {
        "победное": "✨ После вчерашних побед ты чувствуешь небывалый подъём!",
        "унылое": "💫 Поражения закаляют характер... или портят настроение.",
        "богатое": "💰 Кошелёк приятно тяжелеет. Может, купить что-нибудь?",
        "нейтральное": "😊 Обычный день в мире магии и фермерства."
    }
    return moods.get(mood, moods["нейтральное"])


async def generate_pve_enemy(difficulty: str, player_level: int) -> Dict:
    """Генерирует уникального PvE противника"""
    if not FEATURES.get("smart_pve"):
        return {
            "name": f"{difficulty.upper()} противник",
            "talk": "👹 Ты готов к бою?",
            "mechanic": "Обычные атаки"
        }

    difficulty_mult = {"easy": 0.8, "medium": 1.0, "hard": 1.3}
    level = int(player_level * difficulty_mult.get(difficulty, 1.0))

    prompt = f"""Придумай уникального противника для PvE битвы. Сложность: {difficulty}, уровень: {level}.
    Формат JSON:
    {{"name": "имя с эмодзи", "talk": "фраза перед боем", "mechanic": "особая механика"}}"""

    response = await call_ai(prompt, temperature=0.8, task_type="creative")

    if response:
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                enemy = json.loads(json_match.group())
                enemy["level"] = level
                return enemy
        except:
            pass

    enemies = {
        "easy": {"name": "👹 Гоблин", "talk": "💰 Отдавай монеты!", "mechanic": "Иногда ворует", "level": level},
        "medium": {"name": "👺 Теневой маг", "talk": "🌑 Тьма поглотит!", "mechanic": "Накладывает немоту",
                   "level": level},
        "hard": {"name": "👿 Демон", "talk": "🔥 Твоя душа будет гореть!", "mechanic": "Призывает миньонов",
                 "level": level}
    }
    return enemies.get(difficulty, enemies["medium"])


async def get_weather() -> Optional[Dict]:
    """Генерирует погоду"""
    if not FEATURES.get("weather_system"):
        return None

    cache_key = get_weather_key()
    cached = cache.get(cache_key)
    if cached:
        return cached

    weather_types = ["☀️ Солнечно", "🌧️ Дождливо", "🌪️ Ветрено", "🌈 Радуга"]
    weather = random.choice(weather_types)

    effects = {
        "☀️ Солнечно": "Растения растут на 20% быстрее",
        "🌧️ Дождливо": "Полив не требуется",
        "🌪️ Ветрено": "Шанс найти редкое семя +15%",
        "🌈 Радуга": "Удача +10% в казино",
    }

    result = {"name": weather, "effect": effects.get(weather, "Магия в воздухе")}
    cache.set(cache_key, result, ttl_seconds=3 * 3600)
    return result


async def generate_daily_quests(count: int = 3) -> List[Dict]:
    """Генерирует ежедневные квесты"""
    if not FEATURES.get("daily_quests"):
        return []

    cache_key = get_daily_key("quests")
    cached = cache.get(cache_key)
    if cached:
        return cached

    quests = []
    for i in range(count):
        prompt = f"""Придумай квест #{i + 1}. Формат JSON:
        {{"name": "название с эмодзи", "description": "описание", "reward_coins": число, "reward_item": "предмет"}}"""

        response = await call_ai(prompt, temperature=0.8, task_type="creative")

        if response:
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    quests.append(json.loads(json_match.group()))
                    continue
            except:
                pass

        quests.append({
            "name": "🍄 Грибная лихорадка",
            "description": "Принеси 5 светящихся грибов",
            "reward_coins": 2000,
            "reward_item": "✨ Редкое семя"
        })

    cache.set(cache_key, quests, ttl_seconds=24 * 3600)
    return quests