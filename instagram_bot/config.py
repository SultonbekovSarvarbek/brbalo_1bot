from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when an environment variable has an invalid value."""


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} должен быть целым числом") from exc
    if value <= 0:
        raise ConfigError(f"{name} должен быть больше нуля")
    return value


def _chat_ids() -> frozenset[int]:
    raw_value = os.getenv("ALLOWED_CHAT_IDS", "").strip()
    if not raw_value:
        return frozenset()

    try:
        return frozenset(int(item.strip()) for item in raw_value.split(",") if item.strip())
    except ValueError as exc:
        raise ConfigError("ALLOWED_CHAT_IDS должен содержать ID чатов через запятую") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    allowed_chat_ids: frozenset[int]
    download_concurrency: int
    download_timeout_seconds: int
    max_file_size_bytes: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or token == "put_new_token_here":
            raise ConfigError("задайте новый TELEGRAM_BOT_TOKEN в файле .env")

        max_file_size_mb = _positive_int("MAX_FILE_SIZE_MB", 49)
        if max_file_size_mb >= 50:
            raise ConfigError("MAX_FILE_SIZE_MB должен быть меньше лимита Telegram в 50 МБ")

        return cls(
            telegram_bot_token=token,
            allowed_chat_ids=_chat_ids(),
            download_concurrency=_positive_int("DOWNLOAD_CONCURRENCY", 2),
            download_timeout_seconds=_positive_int("DOWNLOAD_TIMEOUT_SECONDS", 180),
            max_file_size_bytes=max_file_size_mb * 1024 * 1024,
        )
