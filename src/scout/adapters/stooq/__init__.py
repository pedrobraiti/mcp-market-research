"""stooq adapter — keyless CSV price history, used as a fallback when yfinance is unavailable."""

from .prices import StooqPrices

__all__ = ["StooqPrices"]
