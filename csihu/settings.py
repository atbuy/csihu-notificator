from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    csihu_token: str
    csihu_troll_url: str
    csihu_schedule_url: str
    csihu_moodle_url: str
    csihu_github_url: str
    postgres_user: str
    postgres_pass: str
    postgres_host: str
    postgres_port: int
    postgres_db: str
    announcement_base_url: str
    announcement_feed_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
