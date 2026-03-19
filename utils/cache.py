from datetime import date, datetime, timedelta
from typing import Any, Optional
import json


class Cache:
    """Простой кэш в памяти"""

    def __init__(self):
        self._data = {}
        self._expiry = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Сохранить в кэш с опциональным временем жизни"""
        self._data[key] = value
        if ttl_seconds:
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        """Получить из кэша"""
        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                del self._data[key]
                del self._expiry[key]
                return None
        return self._data.get(key)

    def delete(self, key: str):
        """Удалить из кэша"""
        if key in self._data:
            del self._data[key]
        if key in self._expiry:
            del self._expiry[key]


cache = Cache()


def get_daily_key(base: str) -> str:
    """Ключ, который меняется каждый день"""
    return f"{base}_{date.today().isoformat()}"


def get_weather_key() -> str:
    """Ключ для погоды (обновляется каждые 3 часа)"""
    hour_block = datetime.now().hour // 3
    return f"weather_{date.today().isoformat()}_{hour_block}"