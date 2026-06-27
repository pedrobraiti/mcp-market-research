"""Central configuration, loaded from environment variables / `.env`.

Scout is stateless and data-only, so there is very little to configure today. Keys use the
``SCOUT_`` prefix to avoid collisions with whatever else lives in the user's environment.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the .env at the project root, so the server finds it regardless of the
# directory it is started from (e.g. when Claude Code launches the MCP).
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCOUT_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    log_level: str = "INFO"
    request_timeout_seconds: float = 15.0

    # SEC EDGAR requires an identifiable User-Agent; used by the filings adapter.
    sec_user_agent: str = ""

    # A browser-like User-Agent for the web `extract` tool (reduces trivial bot blocks).
    web_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Crypto market data (CCXT public endpoints — no exchange key, read-only). The exchange is
    # used only for public price/OHLCV; quote_ccy is the default quote for bare symbols ("BTC").
    crypto_exchange: str = "binance"
    crypto_quote_ccy: str = "USDT"


@lru_cache
def get_settings() -> Settings:
    return Settings()
