from edge_framework.connectors.base import (
    BrokerConnector, OrderRequest, OrderResult,
    OrderDirection, Position, AccountInfo, Candle
)
from edge_framework.connectors.paper import PaperConnector

try:
    from edge_framework.connectors.mt5 import MT5Connector
except ImportError:
    MT5Connector = None  # type: ignore

try:
    from edge_framework.connectors.topstep import TopstepConnector
except ImportError:
    TopstepConnector = None  # type: ignore

__all__ = [
    "BrokerConnector", "OrderRequest", "OrderResult",
    "OrderDirection", "Position", "AccountInfo",
    "Candle", "PaperConnector",
]
if MT5Connector is not None:
    __all__.append("MT5Connector")
if TopstepConnector is not None:
    __all__.append("TopstepConnector")