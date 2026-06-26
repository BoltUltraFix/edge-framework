from edge_framework.connectors.mt5 import MT5Connector
from edge_framework.connectors.base import OrderResult, Position
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class Demo2ShadowConnector(MT5Connector):
    """
    Conector Shadow para Demo2.
    Lee datos reales de MT5 pero NO ejecuta órdenes.
    """

    def __init__(self):
        config_path = Path(
            r"REDACTED"
            r"\Bots2026\Bot5Ultra_Demo2"
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
        self._shadow_positions = {}
        self._shadow_mode = True
        logger.info("[Demo2Shadow] Iniciado en modo lectura")

    def place_order(self, order):
        price = self.get_price(order.symbol)
        fill_price = price.get('ask') if order.direction.value == 'buy' else price.get('bid')
        pos = Position(
            ticket=99998,
            symbol=order.symbol,
            direction=order.direction,
            volume=order.volume,
            open_price=fill_price,
            current_price=fill_price,
            profit=0.0
        )
        self._shadow_positions[order.symbol] = pos
        logger.info(f"[Demo2Shadow] Orden simulada: {order.symbol} {order.direction.value} @ {fill_price}")
        return OrderResult(success=True, ticket=99998, fill_price=fill_price)

    def get_positions(self, symbol=None):
        positions = list(self._shadow_positions.values())
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        return positions

    def close_position(self, ticket):
        closed = [s for s, p in self._shadow_positions.items() if p.ticket == ticket]
        for s in closed:
            del self._shadow_positions[s]
            logger.info(f"[Demo2Shadow] Posición cerrada: {s}")
        return True