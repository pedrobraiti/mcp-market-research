"""CCXT adapter — keyless public crypto market data (price + OHLCV) over ~100 exchanges."""

from .market_data import CcxtMarketData, normalize_pair

__all__ = ["CcxtMarketData", "normalize_pair"]
