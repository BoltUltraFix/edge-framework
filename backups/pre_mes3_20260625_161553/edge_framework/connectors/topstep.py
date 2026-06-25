"""
EdgeFramework — TopstepConnector
Conector para TopstepX via project-x-py y/o API HTTP.

Credenciales: TOPSTEP_USERNAME, TOPSTEP_API_KEY, TOPSTEP_ACCOUNT (.env)
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Dict, List, Optional

from edge_framework.connectors.base import (
    BrokerConnector,
    Candle,
    OrderRequest,
    OrderResult,
    OrderDirection,
    Position,
    AccountInfo,
)

logger = logging.getLogger(__name__)

API_BASE = "https://api.topstepx.com/api"

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

try:
    from project_x_py import ProjectX
    from project_x_py.models import ProjectXConfig
    _SDK_AVAILABLE = True
except ImportError:
    ProjectX = None
    ProjectXConfig = None
    _SDK_AVAILABLE = False


class _AsyncBridge:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="edge-topstep-async",
        )
        self._thread.start()

    def run(self, coro, timeout: float = 30.0):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)


class TopstepConnector(BrokerConnector):
    """Conector TopstepX para EdgeFramework."""

    def __init__(
        self,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
        account_id: Optional[str] = None,
    ):
        self._username = username or os.environ.get("TOPSTEP_USERNAME", "")
        self._api_key = api_key or os.environ.get("TOPSTEP_API_KEY", "")
        self._account_id_str = account_id or os.environ.get("TOPSTEP_ACCOUNT", "")
        self._connected = False
        self._client = None
        self._bridge: Optional[_AsyncBridge] = None
        self._http_token: Optional[str] = None
        self._account_id: Optional[int] = None
        self._account_data: Optional[dict] = None

    def connect(self) -> bool:
        if not self._username or not self._api_key:
            logger.error("[TopstepConnector] Credenciales no configuradas")
            return False

        if not _REQUESTS_OK:
            logger.error("[TopstepConnector] requests no instalado")
            return False

        try:
            if _SDK_AVAILABLE:
                try:
                    self._bridge = _AsyncBridge()
                    px_config = ProjectXConfig()
                    self._client = ProjectX(
                        username=self._username,
                        api_key=self._api_key,
                        config=px_config,
                        account_name=self._account_id_str or None,
                    )
                    self._bridge.run(self._client.authenticate())
                    logger.info("[TopstepConnector] Autenticado via SDK")
                except Exception as sdk_exc:
                    logger.warning(
                        f"[TopstepConnector] SDK auth falló — continuando con HTTP: {sdk_exc}"
                    )
                    if self._bridge:
                        self._bridge.stop()
                    self._bridge = None
                    self._client = None

            r = requests.post(
                f"{API_BASE}/Auth/loginKey",
                json={"userName": self._username, "apiKey": self._api_key},
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            r.raise_for_status()
            self._http_token = r.json().get("token")
            if not self._http_token:
                logger.error("[TopstepConnector] loginKey sin token")
                return False

            r2 = requests.post(
                f"{API_BASE}/Account/search",
                json={"onlyActiveAccounts": True},
                headers={
                    "Authorization": f"Bearer {self._http_token}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            r2.raise_for_status()
            accounts = r2.json().get("accounts", [])
            match = [
                a for a in accounts
                if self._account_id_str and self._account_id_str in a.get("name", "")
            ]
            selected = match[0] if match else (accounts[0] if accounts else None)
            if not selected:
                logger.error("[TopstepConnector] Sin cuentas activas")
                return False

            self._account_id = selected.get("id")
            self._account_data = selected
            self._connected = True
            logger.info(f"[TopstepConnector] Conectado — account_id={self._account_id}")
            return True
        except Exception as exc:
            logger.error(f"[TopstepConnector] connect error: {exc}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        try:
            if self._client and self._bridge and hasattr(self._client, "close"):
                self._bridge.run(self._client.close())
        except Exception:
            pass
        finally:
            if self._bridge:
                self._bridge.stop()
            self._client = None
            self._bridge = None
            self._http_token = None
            self._connected = False
            logger.info("[TopstepConnector] Desconectado")

    def is_connected(self) -> bool:
        return self._connected

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 500,
    ) -> List[Candle]:
        if not self._connected or not self._client or not self._bridge:
            return []
        tf_map = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}
        tf = tf_map.get(timeframe.upper(), 5)
        try:
            bars = self._bridge.run(
                self._client.get_bars(symbol, interval=tf, limit=count)
            )
            if bars is None:
                return []
            if hasattr(bars, "to_pandas"):
                df = bars.to_pandas()
            else:
                import pandas as pd
                df = pd.DataFrame(bars)
            if df is None or len(df) < 3:
                return []
            candles = []
            for _, row in df.iterrows():
                candles.append(Candle(
                    timestamp=float(row.get("time", row.get("t", 0))),
                    open=float(row.get("open", row.get("o", 0))),
                    high=float(row.get("high", row.get("h", 0))),
                    low=float(row.get("low", row.get("l", 0))),
                    close=float(row.get("close", row.get("c", 0))),
                    volume=float(row.get("volume", row.get("v", 0))),
                ))
            return candles
        except Exception as exc:
            logger.warning(f"[TopstepConnector] get_candles {symbol}: {exc}")
            return []

    def get_price(self, symbol: str) -> Dict[str, float]:
        candles = self.get_candles(symbol, "M1", 3)
        if not candles:
            return {"bid": 0.0, "ask": 0.0, "spread": 0.0}
        close = candles[-2].close
        spread = close * 0.0001
        return {"bid": close - spread / 2, "ask": close + spread / 2, "spread": spread}

    def place_order(self, order: OrderRequest) -> OrderResult:
        if order.volume is None or float(order.volume) <= 0.0:
            return OrderResult(False, error_message="lot_zero")
        return OrderResult(False, error_message="place_order no implementado aún en TopstepConnector")

    def close_position(self, ticket: int) -> bool:
        return False

    def get_positions(self, symbol: str = None) -> List[Position]:
        if not self._connected or not self._http_token or not self._account_id:
            return []
        try:
            r = requests.post(
                f"{API_BASE}/Position/searchOpen",
                json={"accountId": self._account_id},
                headers={
                    "Authorization": f"Bearer {self._http_token}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            if r.status_code != 200:
                return []
            raw_positions = r.json().get("positions", [])
            result = []
            for pos in raw_positions:
                mapped = self._map_position(pos)
                if mapped and (symbol is None or mapped.symbol == symbol):
                    result.append(mapped)
            return result
        except Exception as exc:
            logger.warning(f"[TopstepConnector] get_positions: {exc}")
            return []

    def get_account(self) -> AccountInfo:
        if not self._connected:
            return AccountInfo(0, 0, 0)

        if self._client and self._bridge:
            try:
                raw = self._client.get_account_info()
                if asyncio.iscoroutine(raw):
                    acc = self._bridge.run(raw)
                else:
                    acc = raw
                if acc:
                    balance = float(getattr(acc, "balance", 0.0))
                    equity = float(getattr(acc, "equity", balance))
                    margin_free = float(getattr(acc, "free_margin", equity))
                    return AccountInfo(balance, equity, margin_free)
            except Exception:
                pass

        if self._account_data:
            balance = float(
                self._account_data.get("balance", 0.0)
                or self._account_data.get("startingBalance", 0.0)
            )
            equity = float(self._account_data.get("equity", balance) or balance)
            return AccountInfo(balance, equity, equity)

        return AccountInfo(0, 0, 0)

    def modify_sl(self, ticket: int, new_sl: float) -> bool:
        return False

    @staticmethod
    def _map_position(d: dict) -> Optional[Position]:
        try:
            pos_type = int(d.get("type", 0))
            direction = OrderDirection.BUY if pos_type == 1 else OrderDirection.SELL
            symbol = str(
                d.get("contractDisplayName", "")
                or d.get("contractId", "")
                or d.get("symbol", "")
            )
            return Position(
                ticket=int(d.get("id", 0)),
                symbol=symbol,
                direction=direction,
                volume=float(d.get("size", 0) or d.get("netPos", 0) or 0),
                open_price=float(d.get("averagePrice", 0.0) or 0.0),
                current_price=float(d.get("averagePrice", 0.0) or 0.0),
                profit=float(d.get("unrealizedPnl", 0.0) or 0.0),
            )
        except Exception:
            return None