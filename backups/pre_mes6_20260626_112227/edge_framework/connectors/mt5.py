"""
EdgeFramework — MT5Connector
Conector real para MetaTrader 5.

Implementa BrokerConnector usando la API oficial
de Python para MetaTrader 5.

Características:
- Retry con precio fresco en cada intento
- Spread check antes de reenviar
- Guard len(df) < 3 en velas
- Lot 0.0 bloqueado
- Timeout implícito via health check
"""

import logging
import time
from typing import List, Dict, Optional
from edge_framework.connectors.base import (
    BrokerConnector, Candle, OrderRequest, OrderResult,
    OrderDirection, Position, AccountInfo
)

logger = logging.getLogger(__name__)

# Intentar importar MT5 — opcional
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("[MT5Connector] MetaTrader5 no instalado — modo simulado")

# Mapa de timeframes
TIMEFRAME_MAP = {
    "M1":  mt5.TIMEFRAME_M1  if MT5_AVAILABLE else 1,
    "M5":  mt5.TIMEFRAME_M5  if MT5_AVAILABLE else 5,
    "M15": mt5.TIMEFRAME_M15 if MT5_AVAILABLE else 15,
    "H1":  mt5.TIMEFRAME_H1  if MT5_AVAILABLE else 60,
    "H4":  mt5.TIMEFRAME_H4  if MT5_AVAILABLE else 240,
    "D1":  mt5.TIMEFRAME_D1  if MT5_AVAILABLE else 1440,
}

# Códigos de retry
RETRY_CODES = [10004, 10006, 10014, 10016]  # REQUOTE, PRICE_CHANGED, PRICE_OFF, INVALID_STOPS
NO_RETRY_CODES = [10019, 10022]              # NO_MONEY, TRADE_DISABLED

MAX_RETRIES = 3
RETRY_DELAY = 0.3  # 300ms entre reintentos


class MT5Connector(BrokerConnector):
    """
    Conector para MetaTrader 5.
    Implementa la interfaz BrokerConnector completa.
    """

    def __init__(
        self,
        login: int = None,
        password: str = None,
        server: str = None,
        path: str = None
    ):
        self._login = login
        self._password = password
        self._server = server
        self._path = path
        self._connected = False

    def connect(self) -> bool:
        if not MT5_AVAILABLE:
            logger.error("[MT5Connector] MetaTrader5 no disponible")
            return False

        kwargs = {}
        if self._path:
            kwargs['path'] = self._path

        if not mt5.initialize(**kwargs):
            logger.error(f"[MT5Connector] initialize() falló: {mt5.last_error()}")
            return False

        if self._login:
            ok = mt5.login(
                login=self._login,
                password=self._password,
                server=self._server
            )
            if not ok:
                logger.error(f"[MT5Connector] login() falló: {mt5.last_error()}")
                return False

        info = mt5.account_info()
        if not info:
            logger.error("[MT5Connector] Sin info de cuenta")
            return False

        self._connected = True
        logger.info(
            f"[MT5Connector] Conectado — "
            f"login={info.login} balance={info.balance:.2f} "
            f"server={info.server}"
        )
        return True

    def disconnect(self) -> None:
        if MT5_AVAILABLE:
            mt5.shutdown()
        self._connected = False
        logger.info("[MT5Connector] Desconectado")

    def is_connected(self) -> bool:
        if not MT5_AVAILABLE or not self._connected:
            return False
        try:
            return mt5.account_info() is not None
        except Exception:
            return False

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 500
    ) -> List[Candle]:
        if not MT5_AVAILABLE:
            return []

        tf = TIMEFRAME_MAP.get(timeframe, TIMEFRAME_MAP["M5"])
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)

        if rates is None or len(rates) < 3:
            logger.warning(f"[{symbol}] Velas insuficientes: {len(rates) if rates is not None else 0}")
            return []

        return [
            Candle(
                timestamp=float(r['time']),
                open=float(r['open']),
                high=float(r['high']),
                low=float(r['low']),
                close=float(r['close']),
                volume=float(r['tick_volume'])
            )
            for r in rates
        ]

    def get_price(self, symbol: str) -> Dict[str, float]:
        if not MT5_AVAILABLE:
            return {"bid": 0.0, "ask": 0.0, "spread": 0.0}

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {"bid": 0.0, "ask": 0.0, "spread": 0.0}

        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": tick.ask - tick.bid
        }

    def place_order(self, order: OrderRequest) -> OrderResult:
        if not MT5_AVAILABLE:
            return OrderResult(False, error_message="MT5 no disponible")

        if order.volume is None or float(order.volume) <= 0.0:
            logger.warning(f"[{order.symbol}] Lote calculado = {order.volume} — bloqueado")
            return OrderResult(False, error_message="lot_zero")

        info = mt5.symbol_info(order.symbol)
        if not info:
            return OrderResult(False, error_message=f"Símbolo no encontrado: {order.symbol}")

        point = info.point
        last_error = None

        for attempt in range(MAX_RETRIES):
            # Precio FRESCO en cada intento
            tick = mt5.symbol_info_tick(order.symbol)
            if not tick:
                break

            is_buy = order.direction == OrderDirection.BUY
            price = tick.ask if is_buy else tick.bid
            spread = tick.ask - tick.bid

            # Calcular SL/TP con distancia fija
            sl = None
            tp = None

            if order.sl_distance:
                sl_dist = order.sl_distance * point
                # Spread check — no reintentar si spread > SL distance
                if sl_dist <= spread:
                    logger.warning(
                        f"[{order.symbol}] Spread {spread:.5f} > "
                        f"SL dist {sl_dist:.5f} — cancelando"
                    )
                    break
                sl = price - sl_dist if is_buy else price + sl_dist

            if order.tp_distance:
                tp_dist = order.tp_distance * point
                tp = price + tp_dist if is_buy else price - tp_dist

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": order.symbol,
                "volume": float(order.volume),
                "type": mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 20,
                "magic": order.magic or 20260101,
                "comment": order.comment or "EdgeFramework",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if sl:
                request["sl"] = round(sl, info.digits)
            if tp:
                request["tp"] = round(tp, info.digits)

            result = mt5.order_send(request)

            if result is None:
                last_error = str(mt5.last_error())
                time.sleep(RETRY_DELAY)
                continue

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(
                    f"[MT5Connector] ✅ Orden ejecutada: "
                    f"{order.symbol} {order.direction.value} "
                    f"vol={order.volume} @ {result.price} "
                    f"ticket={result.order}"
                )
                return OrderResult(
                    success=True,
                    ticket=result.order,
                    fill_price=result.price
                )

            if result.retcode in NO_RETRY_CODES:
                logger.error(f"[MT5Connector] No retry: {result.retcode} {result.comment}")
                return OrderResult(
                    False,
                    error_code=result.retcode,
                    error_message=result.comment
                )

            if result.retcode in RETRY_CODES:
                logger.warning(
                    f"[MT5Connector] Retry {attempt+1}/{MAX_RETRIES}: "
                    f"{result.retcode} — precio fresco en siguiente intento"
                )
                time.sleep(RETRY_DELAY)
                continue

            # Otro error — no reintentar
            return OrderResult(
                False,
                error_code=result.retcode,
                error_message=result.comment
            )

        return OrderResult(
            False,
            error_message=f"Falló tras {MAX_RETRIES} intentos. Último error: {last_error}"
        )

    def close_position(self, ticket: int) -> bool:
        if not MT5_AVAILABLE:
            return False

        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.warning(f"[MT5Connector] Posición no encontrada: ticket={ticket}")
            return False

        pos = positions[0]
        is_buy = pos.type == mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        if not tick:
            return False

        price = tick.bid if is_buy else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": pos.magic,
            "comment": "EdgeFramework close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"[MT5Connector] ✅ Posición cerrada: ticket={ticket}")
            return True

        logger.error(f"[MT5Connector] Error cerrando {ticket}: {result.retcode if result else 'None'}")
        return False

    def get_positions(self, symbol: str = None) -> List[Position]:
        if not MT5_AVAILABLE:
            return []

        if symbol:
            raw = mt5.positions_get(symbol=symbol)
        else:
            raw = mt5.positions_get()

        if not raw:
            return []

        positions = []
        for p in raw:
            direction = OrderDirection.BUY if p.type == 0 else OrderDirection.SELL
            positions.append(Position(
                ticket=p.ticket,
                symbol=p.symbol,
                direction=direction,
                volume=p.volume,
                open_price=p.price_open,
                current_price=p.price_current,
                profit=p.profit,
                sl=p.sl if p.sl > 0 else None,
                tp=p.tp if p.tp > 0 else None
            ))

        return positions

    def get_account(self) -> AccountInfo:
        if not MT5_AVAILABLE:
            return AccountInfo(0, 0, 0)

        info = mt5.account_info()
        if not info:
            return AccountInfo(0, 0, 0)

        return AccountInfo(
            balance=info.balance,
            equity=info.equity,
            margin_free=info.margin_free,
            currency=info.currency
        )

    def modify_sl(self, ticket: int, new_sl: float) -> bool:
        if not MT5_AVAILABLE:
            return False

        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return False

        pos = positions[0]
        info = mt5.symbol_info(pos.symbol)
        if not info:
            return False

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": ticket,
            "sl": round(new_sl, info.digits),
            "tp": pos.tp
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"[MT5Connector] ✅ SL modificado: ticket={ticket} sl={new_sl}")
            return True

        logger.error(f"[MT5Connector] Error modify_sl {ticket}: {result.retcode if result else 'None'}")
        return False