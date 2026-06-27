"""Research aggregators — meta-tools that compose several port reads into one result.

These orchestrate the domain ports (they never reach a concrete adapter directly) and stay
stateless: pure aggregation of data, no judgment and no persistence.
"""

from .batch import build_calendar, build_classification, build_news_digest
from .comparison import build_comparison
from .correlation import build_correlation
from .crypto import (
    build_crypto_comparison,
    build_crypto_correlation,
    build_crypto_dossier,
    build_crypto_relative_strength,
)
from .dossier import build_dossier
from .relative_strength import build_relative_strength
from .sectors import build_sector_performance

__all__ = [
    "build_calendar",
    "build_classification",
    "build_comparison",
    "build_correlation",
    "build_crypto_comparison",
    "build_crypto_correlation",
    "build_crypto_dossier",
    "build_crypto_relative_strength",
    "build_dossier",
    "build_news_digest",
    "build_relative_strength",
    "build_sector_performance",
]
