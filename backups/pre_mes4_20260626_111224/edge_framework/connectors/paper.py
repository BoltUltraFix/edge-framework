"""
EdgeFramework — PaperConnector
Conector de paper trading para testing sin broker real.
Perfecto para probar estrategias antes de ir a live.
"""

import time
import logging
import random
from typing import List, Dict, Optional
from edge_framework.connectors.base import (
    BrokerConnector, Candle, OrderRequest, OrderResult,
    OrderDirection, Position, AccountInfo, OrderStatus
)

logger = logging.getLogger(__name__)


class PaperConnector(BrokerConnector):
    """
    Conector de paper trading.
    Simula ejecución sin broker real.
    Ideal para desarrollo y testing.
    """

    def __init__(self, initial_balance: float = 10000.0):
        self._balance = initial_balance
        self._equity = initial_balance
        self._positions: Dict[int, Position] = {}
        self._ticket_counter = 1000
        self._connected = False
        self._prices = {
            "XAUUSD": 2350.0,
            "US100":  19500.0,
            "US30":   39000.0,
            "XAGUSD": 28.0,
        }

    def connect(self) -> bool:
        self._connected = True
        logger.info("[PaperConnector] Conectado — paper trading activo")
        return True

    def disconnect(self) -> None:
        self._connected = False
        logger.info("[PaperConnector] Desconectado")

    def is_connected(self) -> bool:
        return self._connected

    def get_candles(self, symbol: str, timeframe: str, count: int = 500) -> List[Candle]:
        """Genera velas sintéticas para testing."""
        candles = []
        base = self._prices.get(symbol, 100.0)
        ts = time.time() - count * 300
        for i in range(count):
            noise = random.gauss(0, base * 0.001)
            o = base + noise
            h = o + abs(random.gauss(0, base * 0.0005))
            l = o - abs(random.gauss(0, base * 0.0005))
            c = o + random.gauss(0, base * 0.0003)
            candles.append(Candle(ts + i*300, o, h, l, c, random.uniform(100, 1000)))
            base = c
        return candles

    def get_price(self, symbol: str) -> Dict[str, float]:
        price = self._prices.get(symbol, 100.0)
        spread = price * 0.0001
        return {"bid": price - spread/2, "ask": price + spread/2, "spread": spread}

    def place_order(self, order: OrderRequest) -> OrderResult:
        price_info = self.get_price(order.symbol)
        fill_price = price_info["ask"] if order.direction == OrderDirection.BUY else price_info["bid"]
        ticket = self._ticket_counter
        self._ticket_counter += 1

        sl = None
        tp = None
        if order.sl_distance:
            sl = fill_price - order.sl_distance if order.direction == OrderDirection.BUY else fill_price + order.sl_distance
        if order.tp_distance:
            tp = fill_price + order.tp_distance if order.direction == OrderDirection.BUY else fill_price - order.tp_distance

        position = Position(
            ticket=ticket,
            symbol=order.symbol,
            direction=order.direction,
            volume=order.volume,
            open_price=fill_price,
            current_price=fill_price,
            profit=0.0,
            sl=sl,
            tp=tp
        )
        self._positions[ticket] = position
        logger.info(f"[PaperConnector] Orden ejecutada: {order.symbol} {order.direction.value} @ {fill_price:.5f} ticket={ticket}")
        return OrderResult(success=True, ticket=ticket, fill_price=fill_price)

    def close_position(self, ticket: int) -> bool:
        if ticket in self._positions:
            pos = self._positions.pop(ticket)
            logger.info(f"[PaperConnector] Posición cerrada: ticket={ticket} {pos.symbol}")
            return True
        return False

    def get_positions(self, symbol: str = None) -> List[Position]:
        positions = list(self._positions.values())
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        return positions

    def get_account(self) -> AccountInfo:
        return AccountInfo(
            balance=self._balance,
            equity=self._equity,
            margin_free=self._equity * 0.9
        )

    def modify_sl(self, ticket: int, new_sl: float) -> bool:
        if ticket in self._positions:
            self._positions[ticket].sl = new_sl
            logger.info(f"[PaperConnector] SL modificado: ticket={ticket} nuevo_sl={new_sl}")
            return True
        return False