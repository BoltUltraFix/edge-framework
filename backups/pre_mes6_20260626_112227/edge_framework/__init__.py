"""
EdgeFramework — Infraestructura de ejecución algorítmica.
"""

from edge_framework.engine import ExecutionEngine, StrategySignal
from edge_framework.connectors.instrument_mapper import InstrumentMapper

__version__ = "0.2.0"
__author__ = "EdgeFramework"

__all__ = [
    "ExecutionEngine",
    "StrategySignal",
    "InstrumentMapper",
]