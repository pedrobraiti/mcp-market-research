"""Research aggregators — meta-tools that compose several port reads into one result.

These orchestrate the domain ports (they never reach a concrete adapter directly) and stay
stateless: pure aggregation of data, no judgment and no persistence.
"""

from .dossier import build_dossier

__all__ = ["build_dossier"]
