"""
Conector MT5 específico para EdgeFix.
Shadow Mode — solo lectura de datos.
No ejecuta órdenes reales.
"""

import logging
from edge_framework.connectors.mt5 import MT5Connector

logger = logging.getLogger(__name__)


class EdgeFixShadowConnector(MT5Connector):
    """
    Conector Shadow para EdgeFix.
    Lee datos reales de MT5 pero NO ejecuta órdenes.
    Permite comparar señales del framework vs EdgeFix real.
    """

    def __init__(self):
        import json
        from pathlib import Path

        # Leer config de EdgeFix
        config_path = Path(
            r"REDACTED"
            r"\Bots2026\Bot5Ultra_EdgeFix_20240604"
            r"\config\config_aggressive.json"
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        mt5_cfg = cfg.get('mt5', cfg)
        super().__init__(
            login=mt5_cfg.get('login'),
            password=mt5_cfg.get('password'),
            server=mt5_cfg.get('server'),
            path=mt5_cfg.get('terminal_path')
        )
        self._shadow_mode = True
        self._shadow_positions = {}
        logger.info("[EdgeFixShadow] Iniciado en modo lectura")

    def place_order(self, order):
        from edge_framework.connectors.base import Position, OrderResult
        price = self.get_price(order.symbol)
        fill_price = price.get('ask') if order.direction.value == 'buy' else price.get('bid')
        pos = Position(
            ticket=99999,
            symbol=order.symbol,
            direction=order.direction,
            volume=order.volume,
            open_price=fill_price,
            current_price=fill_price,
            profit=0.0
        )
        self._shadow_positions[order.symbol] = pos
        logger.info(f"[SHADOW] Orden simulada: {order.symbol} {order.direction.value} @ {fill_price}")
        return OrderResult(success=True, ticket=99999, fill_price=fill_price)

    def get_positions(self, symbol=None):
        positions = list(self._shadow_positions.values())
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        return positions

    def close_position(self, ticket):
        closed = [s for s, p in self._shadow_positions.items() if p.ticket == ticket]
        for s in closed:
            del self._shadow_positions[s]
            logger.info(f"[SHADOW] Posición cerrada: {s}")
        return True

    def modify_sl(self, ticket, new_sl):
        """Shadow mode — NO modifica SL reales."""
        logger.info(f"[SHADOW] SL simulado: ticket={ticket} sl={new_sl}")
        return True