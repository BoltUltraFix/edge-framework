"""
EdgeFramework — InstrumentMapper
Mapea nombres de símbolos entre brokers.
El cliente define sus mapeos en el YAML.
El framework no sabe qué símbolo es "oro" o "Dow".
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class InstrumentMapper:
    """
    Mapea símbolos entre diferentes brokers/plataformas.

    Config YAML:
        connector:
          instrument_map:
            XAUUSD: "XAUUSD"      # MT5
            US30: "US30.cash"     # MT5
            GOLD: "MGC"           # Topstep
            DOW: "MYM"            # Topstep

    Uso:
        mapper = InstrumentMapper(config)
        symbol_broker = mapper.to_broker("XAUUSD")
        symbol_generic = mapper.from_broker("US30.cash")
    """

    def __init__(self, config: Dict = None):
        cfg = config or {}
        conn_cfg = cfg.get('connector', {})
        self._map = conn_cfg.get('instrument_map', {})
        self._reverse = {v: k for k, v in self._map.items()}
        logger.info(f"[InstrumentMapper] {len(self._map)} instrumentos configurados")

    def to_broker(self, generic_symbol: str) -> str:
        """Convierte símbolo genérico al nombre del broker."""
        return self._map.get(generic_symbol, generic_symbol)

    def from_broker(self, broker_symbol: str) -> str:
        """Convierte símbolo del broker al nombre genérico."""
        return self._reverse.get(broker_symbol, broker_symbol)

    def get_all_broker_symbols(self, generic_symbols: list) -> list:
        """Convierte lista de símbolos genéricos a nombres del broker."""
        return [self.to_broker(s) for s in generic_symbols]

    @property
    def has_map(self) -> bool:
        return len(self._map) > 0