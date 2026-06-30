"""Composition root: assembles the concrete adapters from the Settings.

The rest of the code depends only on the ports (``MarketDataSource``, ``FilingsSource``).
Swapping a source — or fanning several into one dossier — happens here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.alternative import AlternativeFearGreed
from ..adapters.apewisdom import ApeWisdomBuzz
from ..adapters.btc_network import BtcNetworkData
from ..adapters.ccxt import CcxtMarketData, CcxtPremium, CcxtStablecoinPeg
from ..adapters.cftc import CftcPositioning
from ..adapters.coingecko import CoinGeckoMacro
from ..adapters.coinpaprika import CoinpaprikaAssets
from ..adapters.commodities import CommodityRatioCalculator
from ..adapters.defillama import DefiLlamaDefi
from ..adapters.deribit import DeribitVol
from ..adapters.derivatives import DerivativesAggregator
from ..adapters.fred import FredMacro
from ..adapters.gdelt import GdeltNewsSearch
from ..adapters.onchain import OnChainNetwork
from ..adapters.openfda import OpenFdaEvents
from ..adapters.price_fallback import PriceFallbackMarketData
from ..adapters.sec import SecEdgar
from ..adapters.statarb import CointegrationAnalyzer
from ..adapters.stooq import StooqPrices
from ..adapters.treasury import TreasuryFiscal
from ..adapters.web import WebExtractor
from ..adapters.wikimedia import WikimediaPageviews
from ..adapters.worldbank import WorldBankMacro
from ..adapters.yfinance import YFinanceMarketData
from ..config import Settings, get_settings
from ..domain.ports import (
    AttentionSource,
    BtcNetworkSource,
    CointegrationSource,
    CommodityRatioSource,
    ContentExtractor,
    CotSource,
    CryptoAssetSource,
    CryptoDerivativesSource,
    CryptoMacroSource,
    CryptoMarketDataSource,
    CryptoOnChainSource,
    CryptoPremiumSource,
    CryptoSentimentSource,
    CryptoVolSource,
    DefiSource,
    FdaSource,
    FilingsSource,
    FinancialsSource,
    MacroSource,
    MarketDataSource,
    NewsSearchSource,
    RetailBuzzSource,
    StablecoinPegSource,
    TreasurySource,
    WorldMacroSource,
)


@dataclass
class Services:
    settings: Settings
    market_data: MarketDataSource
    filings: FilingsSource | None = None
    financials: FinancialsSource | None = None
    extractor: ContentExtractor | None = None
    macro: MacroSource | None = None
    news_search: NewsSearchSource | None = None
    retail_buzz: RetailBuzzSource | None = None
    world_macro: WorldMacroSource | None = None
    treasury: TreasurySource | None = None
    cot: CotSource | None = None
    attention: AttentionSource | None = None
    crypto_market_data: CryptoMarketDataSource | None = None
    crypto_assets: CryptoAssetSource | None = None
    crypto_sentiment: CryptoSentimentSource | None = None
    crypto_buzz: RetailBuzzSource | None = None
    crypto_onchain: CryptoOnChainSource | None = None
    crypto_derivatives: CryptoDerivativesSource | None = None
    crypto_vol: CryptoVolSource | None = None
    defi: DefiSource | None = None
    btc_network: BtcNetworkSource | None = None
    crypto_macro: CryptoMacroSource | None = None
    crypto_premium: CryptoPremiumSource | None = None
    stablecoin_peg: StablecoinPegSource | None = None
    fda: FdaSource | None = None
    commodity_ratios: CommodityRatioSource | None = None
    cointegration: CointegrationSource | None = None


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    timeout = settings.request_timeout_seconds
    sec = SecEdgar(settings.sec_user_agent, timeout=timeout)  # one instance: filings + financials
    market_data = PriceFallbackMarketData(YFinanceMarketData(), StooqPrices(timeout=timeout))

    async def fetch_commodity_history(symbol: str):  # reuse the existing price path, no new client
        return await market_data.get_price_history(symbol, "1y", "1d")

    async def fetch_pair_history(symbol: str):  # 2y covers lookbacks up to ~500 trading days
        return await market_data.get_price_history(symbol, "2y", "1d")

    return Services(
        settings=settings,
        market_data=market_data,
        filings=sec,
        financials=sec,
        extractor=WebExtractor(settings.web_user_agent, timeout=timeout),
        macro=FredMacro(timeout=timeout),
        news_search=GdeltNewsSearch(timeout=timeout),
        retail_buzz=ApeWisdomBuzz(timeout=timeout),
        world_macro=WorldBankMacro(timeout=timeout),
        treasury=TreasuryFiscal(timeout=timeout),
        cot=CftcPositioning(timeout=timeout),
        attention=WikimediaPageviews(timeout=timeout),
        crypto_market_data=CcxtMarketData(
            exchange=settings.crypto_exchange,
            quote_ccy=settings.crypto_quote_ccy,
            timeout=timeout,
        ),
        crypto_assets=CoinpaprikaAssets(timeout=timeout),
        crypto_sentiment=AlternativeFearGreed(timeout=timeout),
        crypto_buzz=ApeWisdomBuzz(
            timeout=timeout, filter_name="all-crypto", strip_suffix=True
        ),
        crypto_onchain=OnChainNetwork(timeout=timeout),
        crypto_derivatives=DerivativesAggregator(timeout=timeout),
        crypto_vol=DeribitVol(timeout=timeout),
        defi=DefiLlamaDefi(timeout=timeout),
        btc_network=BtcNetworkData(timeout=timeout),
        crypto_macro=CoinGeckoMacro(timeout=timeout),
        crypto_premium=CcxtPremium(
            us_market=CcxtMarketData(exchange="coinbase", quote_ccy="USD", timeout=timeout),
            offshore_market=CcxtMarketData(exchange="binance", quote_ccy="USDT", timeout=timeout),
        ),
        stablecoin_peg=CcxtStablecoinPeg(timeout=timeout),
        fda=OpenFdaEvents(timeout=timeout),
        commodity_ratios=CommodityRatioCalculator(fetch_commodity_history),
        cointegration=CointegrationAnalyzer(fetch_pair_history),
    )
