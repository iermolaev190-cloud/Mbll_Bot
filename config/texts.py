START_MESSAGE = """🎮 *MBLL FARM BATTLE*

Добро пожаловать в игру!

Выращивай персонажей, сражайся и торгуй!

Есть вопросы / предложения - @zaebzona"""

MAIN_MENU = """📋 *ГЛАВНОЕ МЕНЮ*

Выбери действие:"""

PROFILE_MESSAGE = """👤 *ПРОФИЛЬ*

📊 Уровень: {level}
💰 Монеты: {coins:,}
💎 Кристаллы: {crystals:,}
💠 Алмазы: {diamonds:,}

⚔️ *Боевая статистика:*
   ✅ Побед: {wins}
   ❌ Поражений: {losses}
   🏆 Рейтинг: #{rating}

🌱 *Ферма:* {farm_slots} слотов
👥 *Персонажей:* {characters_count}

📅 *Последний визит:* {last_visit} (UTС +0/GTM -3)"""

FARM_MENU = """🌱 *ФЕРМА*

{current_slots}/{max_slots} слотов занято

Выбери действие:"""

FARM_SLOT_STATUS = """🌱 *ГРЯДКА #{slot_num}*

{status}

Выбери действие:"""

FARM_SLOT_EMPTY = """⭕ Пусто - готово к посадке"""

FARM_SLOT_GROWING = """👤 {character_name} ({rarity})
🌱 Стадия: {stage} ({progress}%)
⏰ До готовности: {time_left}
💧 Полив: {water_status}"""

FARM_PLANT_SUCCESS = """✅ *СЕМЯ ПОСАЖЕНО!*

{character_name} ({rarity})
🔥 Элемент: {element}

⏰ Время роста: ~7 часов
💧 Требуется полив каждые 2 часа"""

FARM_WATERED = """💧 *ПОЛЕНО!*

Растение получило воду. Следующий полив через {hours}ч"""

HARVEST_SUCCESS = """✨ *УРОЖАЙ СОБРАН!*

🎉 Ты получил: *{character_name}*
🌟 Редкость: {rarity}
🔥 Элемент: {element}

❤️ HP: {hp} | 🗡️ DMG: {damage} | 🛡️ ARM: {armor}"""

HARVEST_NOT_READY = """⏳ Растение не готово
Осталось: {time_left}"""

BATTLE_MENU = """⚔️ *АРЕНА*

Выбери тип боя:"""

TEAM_SELECTION = """👥 *ВЫБОР КОМАНДЫ*

Выбрано: {current}/3

{characters_list}

*Текущая команда:*
{team_display}"""

TEAM_NOT_READY = """❌ Команда не полная
Нужно 3, у тебя {count}"""

TEAM_FULL = """❌ Команда полная (макс 3)"""

TEAM_SET_SUCCESS = """✅ *КОМАНДА ГОТОВА!*

{team_display}

Готов к боям! ⚔️"""

TEAM_EMPTY = """❌ Нет доступных персонажей!

Выращивай на ферме или покупай на рынке"""

CHARACTER_INFO = """👤 *{character_name}* L{level}

🌟 {rarity} | 🔥 {element}

❤️ HP: {hp}/{max_hp}
🗡️ DMG: {damage}
🛡️ ARM: {armor}
⚡ AGI: {agility}
🧠 INT: {intelligence}

⚔️ Побед: {wins}
💀 Поражений: {losses}

📈 Опыт: {exp}/{exp_next}"""

BATTLE_START_PVP = """⚔️ *БОЙ НАЧАЛСЯ!*

🔴 *Твоя команда:*
{your_team}

🔵 *Противник:*
{enemy_team}

Бой идёт... ⏳"""

BATTLE_WIN = """🏆 *ПОБЕДА!*

💰 +{coins} монет
💎 +{crystals} кристаллов

📈 Персонажи получили опыт!
{levelups}"""

BATTLE_LOSS = """💀 *ПОРАЖЕНИЕ*

💰 +{coins} монет утешительно

Попробуй ещё раз! 💪"""

LEADERBOARD = """🏆 *РЕЙТИНГ АРЕНЫ*

{leaderboard}

*Твоё место:* #{your_rank}

🎁 *Награды за неделю:*
🥇 1: 5💠 | 🥈 2: 3💠 | 🥉 3: 1💠"""

MARKET_MENU = """🏪 *РЫНОК*

Комиссия: 5%

Выбери действие:"""

MARKET_LISTINGS = """🏪 *ДОСТУПНЫЕ ОБЪЯВЛЕНИЯ*

{listings}

Выбери персонажа для покупки"""

MARKET_NO_LISTINGS = """🏪 Рынок пуст

Приходи позже!"""

LISTING_INFO = """📋 *ОБЪЯВЛЕНИЕ*

{character_name} ({rarity}) L{level}
🔥 {element}

❤️ {hp} | 🗡️ {damage} | 🛡️ {armor}

💰 Цена: {price}
👤 Продавец: {seller_name}"""

PURCHASE_SUCCESS = """✅ *КУПЛЕНО!*

{character_name}
Цена: {price} 💰
Комиссия: {commission} 💰"""

PURCHASE_NO_FUNDS = """❌ Недостаточно монет

Нужно: {price}
Есть: {have}"""

SELL_MENU = """💵 *ПРОДАТЬ ПЕРСОНАЖА*

{characters}

Выбери персонажа"""

SELL_NO_CHARS = """❌ Нет доступных персонажей

В команде/на ферме нельзя продавать"""

SELL_PRICE = """💰 *УСТАНОВИТЬ ЦЕНУ*

{character_name} ({rarity}) L{level}

💡 Рекомендуемая цена: {recommended}

Минимум: 1000
Максимум: 1,000,000

Введи цену числом:"""

SELL_CONFIRM = """📋 *ПОДТВЕРДИТЬ ПРОДАЖУ*

{character_name}
Цена: {price} 💰
Комиссия (5%): {commission} 💰
*Получишь:* {net_price} 💰

Активно 7 дней"""

SELL_SUCCESS = """✅ *ОБЪЯВЛЕНИЕ РАЗМЕЩЕНО!*

{character_name}
💰 {net_price} монет за продажу"""

SELL_INVALID_PRICE = """❌ Неверная цена

Минимум: 1000, Максимум: 1,000,000"""

MY_LISTINGS = """📋 *МОИ ОБЪЯВЛЕНИЯ*

{listings}"""

MY_LISTINGS_EMPTY = """📋 Нет активных объявлений"""

ECONOMY_MENU = """💰 *Обмен валют*

💰 Монеты: {coins:,}
💎 Кристаллы: {crystals:,}
💠 Алмазы: {diamonds:,}

Выбери обмен:"""

EXCHANGE_INFO = """💱 *КУРСЫ ОБМЕНА*

1️⃣ 50000 💰 = 1 💎
2️⃣ 150000💰 + 50💎 = 1💠
3️⃣ 500 💎 = 1 💠

*Как получить алмазы:*
• Дорогой обмен
• Топ-3 арены (+5/3/1)"""

EXCHANGE_CONFIRM = """💱 *ПОДТВЕРДИТЬ ОБМЕН*

Даёшь: {give}
Получаешь: {receive}"""

EXCHANGE_SUCCESS = """✅ *ОБМЕН ВЫПОЛНЕН!*

{transaction}

Новый баланс:
💰 {coins:,} | 💎 {crystals:,} | 💠 {diamonds:,}"""

NOT_ENOUGH_RESOURCES = """❌ Недостаточно ресурсов

Требуется: {required}
Есть: {have}
Нужно ещё: {need}"""

HELP_TEXT = """❓ *СПРАВКА*

🌱 *Ферма:* Выращивай персонажей
⚔️ *Боевая:* Сражайся на арене
🏪 *Рынок:* Покупай/продавай
💰 *Экономика:* Обменивай валюты


Удачи! 🚀"""

ERROR_OCCURRED = "❌ Ошибка! Попробуй позже"
INVALID_INPUT = "❌ Неверный ввод"
NOT_FOUND = "❌ Не найдено"
UNAUTHORIZED = "❌ Нет доступа"
COOLDOWN = "⏳ Подожди {seconds}с"

BUTTON_PROFILE = "👤 Профиль"
BUTTON_FARM = "🌱 Ферма"
BUTTON_BATTLE = "⚔️ Боевая арена"
BUTTON_MARKET = "🏪 Рынок"
BUTTON_ECONOMY = "💰 Обмен валют"
BUTTON_BACK = "⬅️ Назад"
BUTTON_MENU = "📋 Меню"
BUTTON_HELP = "❓ Помощь"
BUTTON_REFRESH = "🔄 Обновить"
BUTTON_PLANT = "🌱 Посадить"
BUTTON_WATER = "💧 Полить"
BUTTON_HARVEST = "🌾 Собрать"
BUTTON_SELECT_TEAM = "👥 Команда"
BUTTON_START_BATTLE = "⚔️ Начать"
BUTTON_VIEW_TEAM = "👥 Моя команда"
BUTTON_PVP = "🎮 PvP"
BUTTON_PVE = "👹 PvE"
BUTTON_BUY = "💰 Купить"
BUTTON_SELL = "💵 Продать"
BUTTON_BROWSE = "🔍 Обзор"
BUTTON_MY_LISTINGS = "📋 Мои"
BUTTON_EXCHANGE = "💱 Обмен"
BUTTON_CONFIRM = "✅ Да"
BUTTON_CANCEL = "❌ Нет"
BUTTON_ADD_TEAM = "➕ Добавить"
BUTTON_REMOVE_TEAM = "➖ Удалить"
BUTTON_INFO = "ℹ️ Инфо"
BUTTON_ADMIN = "🔧 Админ"
BUTTON_STATS = "📊 Статистика"

ADMIN_PANEL = """🔧 *АДМИН ПАНЕЛЬ*

{stats}"""

ADMIN_STATS = """📊 *СТАТИСТИКА*

👥 Игроков: {total_players}
🆕 Новых: {new_today}
💰 Монет: {total_coins:,}
💎 Кристаллов: {total_crystals:,}
💠 Алмазов: {total_diamonds:,}
⚔️ Боёв: {total_battles}
👤 Персонажей: {total_characters}"""