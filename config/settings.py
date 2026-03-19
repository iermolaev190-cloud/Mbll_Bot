from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    bot_token: str
    database_url: str = "sqlite+aiosqlite:///./mbll_bot.db"
    log_level: str = "INFO"
    admin_ids: str = "7697645186"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.admin_ids:
            return []
        if isinstance(self.admin_ids, list):
            return [int(x) for x in self.admin_ids]
        return [int(x.strip()) for x in str(self.admin_ids).split(",") if x.strip().isdigit()]


settings = Settings()