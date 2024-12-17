import logging
from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Prometheus(BaseModel):
    port: int


class CSIHU(BaseModel):
    token: str
    schedule_url: str
    moodle_url: str
    courses_url: str
    github_url: str


class DB(BaseModel):
    username: str
    password: str
    host: str
    port: int
    database: str


class WebDriver(BaseModel):
    host: str
    port: str


class Gotify(BaseModel):
    host: str
    port: int
    priority: int
    token: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CSIHU_", env_nested_delimiter="__")

    csihu: CSIHU
    db: DB
    metrics: Prometheus
    gotify: Gotify
    web_driver: WebDriver
    command_prefix: str = "."
    announcement_url: str
    announcement_base_url: str
    announcement_feed_url: str
    log_level: int = logging.INFO
    debug: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
