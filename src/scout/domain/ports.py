"""Domain ports (interfaces) — contracts that concrete adapters implement.

Async ``Protocol``s: a data source (yfinance today; SEC EDGAR, FRED, a paid provider
tomorrow) must satisfy these without explicit inheritance. Every method takes an optional
``as_of`` so the same call can read the present or a past snapshot — the key to keeping
Scout stateless while still serving "what changed since" questions.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from .models import (
    AnalystView,
    BtcNetwork,
    CoinbasePremium,
    CointegratedPairs,
    Cointegration,
    CommodityRatios,
    CompanySnapshot,
    CotReport,
    CryptoAssetProfile,
    CryptoDerivatives,
    CryptoFearGreed,
    CryptoImpliedVol,
    CryptoMacro,
    CryptoMoversList,
    CryptoOnChain,
    CryptoOrderBook,
    CryptoPriceHistory,
    CryptoQuote,
    CryptoSectors,
    CryptoSymbolSearch,
    DefiFees,
    DefiOverview,
    DefiYields,
    DividendHistory,
    EarningsInfo,
    EtfHoldings,
    ExtractedPage,
    FdaEvents,
    FilingSearch,
    FilingsList,
    Fundamentals,
    MacroSnapshot,
    MoversList,
    NewsList,
    OptionsVolatility,
    Ownership,
    Period,
    PriceHistory,
    QualityMetrics,
    RetailBuzz,
    SecFinancials,
    StablecoinPeg,
    StablecoinSupply,
    SymbolSearch,
    TreasuryData,
    WebNewsSearch,
    WikipediaAttention,
    WorldBankData,
)


@runtime_checkable
class MarketDataSource(Protocol):
    """Reads of company-level market and fundamental data."""

    async def get_snapshot(
        self, symbol: str, as_of: date | None = None
    ) -> CompanySnapshot | None:
        """Price, day move and key multiples. ``None`` if the symbol can't be resolved."""
        ...

    async def get_fundamentals(
        self, symbol: str, period: Period = Period.ANNUAL, as_of: date | None = None
    ) -> Fundamentals | None:
        """Income/balance/cash-flow figures for the latest period at or before ``as_of``."""
        ...

    async def get_dividends(
        self, symbol: str, as_of: date | None = None
    ) -> DividendHistory | None:
        """Dividend history, trailing yield, growth streak and cut flag up to ``as_of``."""
        ...

    async def get_price_history(
        self,
        symbol: str,
        range: str = "6mo",
        interval: str = "1d",
        as_of: date | None = None,
    ) -> PriceHistory | None:
        """OHLCV bars over ``range`` at ``interval``, truncated at/before ``as_of``."""
        ...

    async def get_news(self, symbol: str, limit: int = 10) -> NewsList | None:
        """Recent news headlines (title, publisher, date, url) for a symbol."""
        ...

    async def get_earnings(self, symbol: str, as_of: date | None = None) -> EarningsInfo | None:
        """Upcoming earnings date and history (estimate / actual / surprise)."""
        ...

    async def get_analyst_view(self, symbol: str) -> AnalystView | None:
        """Sell-side consensus rating and price targets (third-party opinion, as data)."""
        ...

    async def get_quality_metrics(
        self, symbol: str, as_of: date | None = None
    ) -> QualityMetrics | None:
        """Derived ROE/ROA, margins and revenue/earnings growth & CAGR."""
        ...

    async def get_etf_holdings(self, symbol: str) -> EtfHoldings | None:
        """An ETF's declared top holdings and sector weights; ``None`` if not a fund."""
        ...

    async def get_ownership(self, symbol: str) -> Ownership | None:
        """Insider/institution ownership percentages, top institutions and recent insider trades."""
        ...

    async def get_options_volatility(
        self, symbol: str, expiry: str | None = None
    ) -> OptionsVolatility | None:
        """ATM implied vol and the options-implied expected move to the (nearest) expiry."""
        ...

    async def search_symbols(self, query: str, limit: int = 10) -> SymbolSearch:
        """Resolve a free-text query (company name / partial ticker) to matching symbols."""
        ...

    async def get_movers(self, category: str = "gainers", limit: int = 20) -> MoversList:
        """Market-wide top gainers / losers / most-active (no symbol needed)."""
        ...


@runtime_checkable
class FilingsSource(Protocol):
    """Reads of regulatory filings (SEC EDGAR today)."""

    async def get_filings(
        self,
        symbol: str,
        form_type: str | None = None,
        limit: int = 20,
        as_of: date | None = None,
    ) -> FilingsList | None:
        """Recent filings, optionally restricted to ``form_type`` and dated at/before ``as_of``."""
        ...

    async def search_filings(
        self, query: str, forms: str | None = None, limit: int = 10
    ) -> FilingSearch:
        """Full-text search across all EDGAR filings — find companies by what they disclose."""
        ...


@runtime_checkable
class FinancialsSource(Protocol):
    """Reads of authoritative reported financials (SEC EDGAR XBRL today)."""

    async def get_financials(self, symbol: str, as_of: date | None = None) -> SecFinancials | None:
        """Latest annual reported figures (with provenance) at or before ``as_of``."""
        ...


@runtime_checkable
class MacroSource(Protocol):
    """Reads of macro indicators (FRED today)."""

    async def get_macro_context(self, as_of: date | None = None) -> MacroSnapshot:
        """Latest value of each key macro series, at or before ``as_of``."""
        ...


@runtime_checkable
class WorldMacroSource(Protocol):
    """Country-level macro indicators (World Bank today)."""

    async def get_indicators(
        self, country: str = "USA", codes: list[str] | None = None
    ) -> WorldBankData:
        """Latest value of key macro indicators for a country."""
        ...


@runtime_checkable
class TreasurySource(Protocol):
    """Official US Treasury fiscal data (Fiscal Data API today)."""

    async def get_data(self) -> TreasuryData:
        """Latest headline fiscal figures (public debt, average interest rates)."""
        ...


@runtime_checkable
class RetailBuzzSource(Protocol):
    """Reddit mention buzz (ApeWisdom today)."""

    async def get_buzz(self, symbol: str | None = None, limit: int = 20) -> RetailBuzz:
        """Trending tickers by Reddit mentions, or one symbol's buzz if given."""
        ...


@runtime_checkable
class CotSource(Protocol):
    """CFTC Commitments of Traders futures positioning (keyless Socrata today)."""

    async def get_positioning(self, market: str, weeks: int = 12) -> CotReport:
        """Speculator/commercial futures positioning for a market, with ``weeks`` of history."""
        ...


@runtime_checkable
class AttentionSource(Protocol):
    """Wikipedia pageviews as an attention proxy (Wikimedia today)."""

    async def get_pageviews(self, article: str, days: int = 30) -> WikipediaAttention:
        """Daily pageviews for a Wikipedia article over the last ``days``."""
        ...


@runtime_checkable
class NewsSearchSource(Protocol):
    """Free-text news/event search across global media (GDELT today)."""

    async def search_news(
        self, query: str, limit: int = 20, days: int = 7
    ) -> WebNewsSearch:
        """Recent articles matching a free-text query within the last ``days``."""
        ...


@runtime_checkable
class ContentExtractor(Protocol):
    """Fetches a web page and returns its main content as clean markdown."""

    async def extract(self, url: str) -> ExtractedPage:
        """Fetch ``url`` and extract the main content. Always returns a result (with
        ``fetched_ok=False`` and a note on a block/error), never raises for the agent."""
        ...


@runtime_checkable
class CryptoMarketDataSource(Protocol):
    """Reads of public crypto spot market data (CCXT public endpoints today)."""

    async def get_quote(self, symbol: str) -> CryptoQuote | None:
        """Live spot quote (last/bid/ask, 24h move) for a pair. ``None`` if it can't be resolved."""
        ...

    async def get_price_history(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 200,
        as_of: date | None = None,
    ) -> CryptoPriceHistory | None:
        """OHLCV candles for a pair, most recent ``limit`` bars truncated at/before ``as_of``."""
        ...

    async def get_movers(self, category: str = "gainers", limit: int = 20) -> CryptoMoversList:
        """Top gainers / losers / most-active pairs on the configured exchange."""
        ...

    async def get_order_book(self, symbol: str, limit: int = 20) -> CryptoOrderBook | None:
        """Top-of-book + aggregated depth for a pair — a pre-trade liquidity/slippage read."""
        ...


@runtime_checkable
class CryptoAssetSource(Protocol):
    """Reads of asset-level crypto data: supply, market cap, rank (Coinpaprika today)."""

    async def get_profile(self, base: str) -> CryptoAssetProfile | None:
        """Supply/market-cap/rank/ATH for a base asset (e.g. ``BTC``). ``None`` if not found."""
        ...

    async def search(self, query: str, limit: int = 10) -> CryptoSymbolSearch:
        """Resolve a free-text query (name / partial symbol) to crypto assets."""
        ...


@runtime_checkable
class CryptoSentimentSource(Protocol):
    """Market-wide crypto sentiment (alternative.me Fear & Greed today)."""

    async def get_fear_greed(self, days: int = 30) -> CryptoFearGreed:
        """Current Fear & Greed index plus the daily history over the last ``days``."""
        ...


@runtime_checkable
class CryptoOnChainSource(Protocol):
    """On-chain network-health metrics (mempool.space for BTC, Blockscout for ETH today)."""

    async def get_onchain(self, asset: str = "BTC") -> CryptoOnChain:
        """Network metrics (fees, hashrate, gas, addresses) for a chain."""
        ...


@runtime_checkable
class CryptoDerivativesSource(Protocol):
    """Perp funding rate & open interest across exchanges — positioning context (never executed)."""

    async def get_derivatives(self, base: str) -> CryptoDerivatives:
        """Funding rate + open interest per venue for a base asset."""
        ...


@runtime_checkable
class CryptoPremiumSource(Protocol):
    """US-spot vs offshore price premium (Coinbase USD vs Binance USDT) — a demand tell."""

    async def get_premium(self, symbol: str = "BTC", days: int = 30) -> CoinbasePremium:
        """Latest premium + a daily premium series (with its z-score) for a base asset."""
        ...


@runtime_checkable
class StablecoinPegSource(Protocol):
    """Stablecoin price deviation from the $1 peg (the PRICE axis; complements supply)."""

    async def get_peg(
        self, symbols: list[str] | None = None, venue: str | None = None
    ) -> StablecoinPeg:
        """Per-stablecoin price + basis-point deviation from $1 + a depeg flag, on one venue."""
        ...


@runtime_checkable
class CryptoVolSource(Protocol):
    """Options-implied volatility (Deribit DVOL today)."""

    async def get_implied_vol(self, asset: str = "BTC") -> CryptoImpliedVol:
        """The DVOL index ('crypto VIX') current value plus recent history."""
        ...


@runtime_checkable
class DefiSource(Protocol):
    """DeFi ecosystem data: TVL, stablecoins, yields (DefiLlama today)."""

    async def get_tvl(self, slug: str | None = None) -> DefiOverview:
        """Total value locked by chain (no slug) or one protocol's breakdown (with slug)."""
        ...

    async def get_stablecoins(self) -> StablecoinSupply:
        """Stablecoin circulation and peg status."""
        ...

    async def get_yields(
        self, chain: str | None = None, project: str | None = None, min_tvl: float = 1_000_000
    ) -> DefiYields:
        """Yield/APY pools, filterable by chain/project/min TVL."""
        ...

    async def get_fees(self, protocol: str | None = None) -> DefiFees:
        """Protocol fees vs revenue: overview (no protocol) or one protocol's summary."""
        ...


@runtime_checkable
class BtcNetworkSource(Protocol):
    """BTC base-layer fundamentals + fee market (Blockchain.com + mempool.space today)."""

    async def get_network(self) -> BtcNetwork:
        """Hash rate / miner revenue / NVT valuation plus the live sat/vB fee market."""
        ...


@runtime_checkable
class CryptoMacroSource(Protocol):
    """Crypto-wide macro & sector data (CoinGecko today)."""

    async def get_macro(self) -> CryptoMacro:
        """Total market cap, BTC/ETH dominance and DeFi share."""
        ...

    async def get_sectors(self) -> CryptoSectors:
        """Per-category (sector) performance."""
        ...


@runtime_checkable
class FdaSource(Protocol):
    """Drug approvals + recalls for a pharma/biotech sponsor (openFDA, keyless)."""

    async def get_events(self, company: str, limit: int = 10) -> FdaEvents:
        """Approvals (drugsfda) and recalls (enforcement) for a sponsor name."""
        ...


@runtime_checkable
class CointegrationSource(Protocol):
    """Engle-Granger cointegration / pairs read for two symbols (keyless)."""

    async def get_cointegration(
        self, symbol_a: str, symbol_b: str, lookback_days: int = 252
    ) -> Cointegration:
        """Hedge ratio, residual ADF stat, spread z-score and half-life for a pair."""
        ...

    async def find_pairs(
        self, symbols: list[str], lookback_days: int = 252, min_correlation: float = 0.5
    ) -> CointegratedPairs:
        """Screen a basket for cointegrated pairs (correlation pre-filter → ADF test)."""
        ...




@runtime_checkable
class CommodityRatioSource(Protocol):
    """Macro bellwether commodity ratios — copper/gold, gold/silver (yfinance, keyless)."""

    async def get_ratios(self) -> CommodityRatios:
        """Latest copper/gold + gold/silver ratios, their z-scores and a daily history."""
        ...
