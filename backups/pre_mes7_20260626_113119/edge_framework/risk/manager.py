"""
EdgeFramework — RiskManager
Gestión de riesgo institucional multi-capa.

El RiskManager decide si una señal puede ejecutarse
y calcula el tamaño de posición correcto.

Capas de riesgo (en orden de prioridad):
1. CircuitBreaker — para todo si hay pérdida grave
2. DailyDrawdown — límite de pérdida diaria
3. MaxTrades — límite de trades por día
4. PositionExists — evita doble entrada
5. RiskCalculator — calcula lote correcto
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import logging
import time
from datetime import datetime, date

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    suggested_volume: float = 0.0
    risk_multiplier: float = 1.0


class CircuitBreaker:
    """
    Para TODA operación si las pérdidas
    superan el umbral configurado.
    """
    def __init__(self, max_loss_pct: float = 0.05):
        self.max_loss_pct = max_loss_pct
        self._triggered = False
        self._trigger_time: Optional[float] = None

    def check(self, equity: float, balance: float) -> Tuple[bool, str]:
        loss_pct = (balance - equity) / balance if balance > 0 else 0
        if loss_pct >= self.max_loss_pct:
            if not self._triggered:
                self._triggered = True
                self._trigger_time = time.time()
                logger.warning(
                    f"[CircuitBreaker] ACTIVADO — pérdida {loss_pct:.1%} "
                    f"supera límite {self.max_loss_pct:.1%}"
                )
            return False, f"circuit_breaker_loss_{loss_pct:.1%}"
        self._triggered = False
        return True, "ok"

    @property
    def is_triggered(self) -> bool:
        return self._triggered


class DailyDrawdownGuard:
    """
    Bloquea operaciones si el DD diario
    supera el límite configurado.
    """
    def __init__(self, max_daily_dd_pct: float = 0.05):
        self.max_daily_dd_pct = max_daily_dd_pct
        self._day_start_equity: Optional[float] = None
        self._current_day: Optional[date] = None

    def update(self, equity: float) -> None:
        today = date.today()
        if self._current_day != today:
            self._current_day = today
            self._day_start_equity = equity
            logger.info(f"[DailyDD] Nuevo día — equity inicio: {equity:.2f}")

    def check(self, equity: float) -> Tuple[bool, str]:
        if not self._day_start_equity:
            return True, "ok"
        dd_pct = (self._day_start_equity - equity) / self._day_start_equity
        if dd_pct >= self.max_daily_dd_pct:
            return False, f"daily_dd_{dd_pct:.1%}"
        return True, "ok"


class TradeCounter:
    """
    Limita el número de trades por día.
    """
    def __init__(self, max_trades_per_day: int = 10):
        self.max_trades = max_trades_per_day
        self._count = 0
        self._current_day: Optional[date] = None

    def _reset_if_new_day(self) -> None:
        today = date.today()
        if self._current_day != today:
            self._current_day = today
            self._count = 0

    def check(self) -> Tuple[bool, str]:
        self._reset_if_new_day()
        if self._count >= self.max_trades:
            return False, f"max_trades_{self._count}/{self.max_trades}"
        return True, "ok"

    def register_trade(self) -> None:
        self._reset_if_new_day()
        self._count += 1

    @property
    def count_today(self) -> int:
        self._reset_if_new_day()
        return self._count


class RiskCalculator:
    """
    Calcula el tamaño de posición correcto
    basado en riesgo por trade y distancia SL.
    """
    def __init__(
        self,
        risk_per_trade: float = 0.01,
        min_volume: float = 0.01,
        max_volume: float = 10.0
    ):
        self.risk_per_trade = risk_per_trade
        self.min_volume = min_volume
        self.max_volume = max_volume

    def calculate(
        self,
        balance: float,
        sl_distance: float,
        point_value: float = 1.0,
        risk_multiplier: float = 1.0
    ) -> float:
        """
        Calcula el volumen correcto.

        volume = (balance * risk_pct * multiplier) / (sl_distance * point_value)
        """
        if sl_distance <= 0 or point_value <= 0:
            return 0.0

        risk_amount = balance * self.risk_per_trade * risk_multiplier
        volume = risk_amount / (sl_distance * point_value)
        volume = round(volume, 2)
        volume = max(self.min_volume, min(self.max_volume, volume))

        if volume <= 0:
            logger.warning(f"[RiskCalculator] Volumen calculado = {volume} — bloqueado")
            return 0.0

        return volume


class RiskManager:
    """
    Gestión de riesgo multi-capa con Early Return.

    Orden de verificación:
    1. CircuitBreaker (más alto — para todo)
    2. DailyDrawdown
    3. MaxTrades
    4. PositionExists
    5. RiskCalculator (calcula lote)
    """

    def __init__(self, config: Dict = None):
        cfg = config or {}
        risk_cfg = cfg.get("risk", {})

        self._circuit_breaker = CircuitBreaker(
            max_loss_pct=risk_cfg.get("circuit_breaker_pct", 0.08)
        )
        self._daily_dd = DailyDrawdownGuard(
            max_daily_dd_pct=risk_cfg.get("max_daily_drawdown", 0.05)
        )
        self._trade_counter = TradeCounter(
            max_trades_per_day=risk_cfg.get("max_trades_per_day", 10)
        )
        self._calculator = RiskCalculator(
            risk_per_trade=risk_cfg.get("risk_per_trade", 0.01),
            min_volume=risk_cfg.get("min_volume", 0.01),
            max_volume=risk_cfg.get("max_volume", 10.0)
        )

    def evaluate(
        self,
        signal,
        account,
        open_positions: list,
        risk_multiplier: float = 1.0
    ) -> RiskDecision:
        """
        Pipeline de riesgo con Early Return.
        Si cualquier capa falla → return inmediato.
        """

        # NIVEL 1 — CircuitBreaker
        self._daily_dd.update(account.equity)
        ok, reason = self._circuit_breaker.check(account.equity, account.balance)
        if not ok:
            return RiskDecision(False, reason)

        # NIVEL 2 — Daily Drawdown
        ok, reason = self._daily_dd.check(account.equity)
        if not ok:
            return RiskDecision(False, reason)

        # NIVEL 3 — Max Trades
        ok, reason = self._trade_counter.check()
        if not ok:
            return RiskDecision(False, reason)

        # NIVEL 4 — Position exists
        broker_symbol = (signal.metadata or {}).get('broker_symbol')
        match_symbols = {signal.symbol}
        if broker_symbol:
            match_symbols.add(broker_symbol)
        symbol_positions = [p for p in open_positions if p.symbol in match_symbols]
        if symbol_positions:
            return RiskDecision(False, "position_exists")

        # NIVEL 5 — Calcular volumen
        sl_distance = signal.sl_distance or 10.0
        volume = self._calculator.calculate(
            balance=account.balance,
            sl_distance=sl_distance,
            risk_multiplier=risk_multiplier * signal.confidence
        )

        if volume <= 0:
            return RiskDecision(False, "lot_zero")

        return RiskDecision(
            approved=True,
            reason="approved",
            suggested_volume=volume,
            risk_multiplier=risk_multiplier
        )

    def register_trade(self) -> None:
        """Llamar después de ejecutar un trade."""
        self._trade_counter.register_trade()

    @property
    def trades_today(self) -> int:
        return self._trade_counter.count_today

    @property
    def circuit_breaker_active(self) -> bool:
        return self._circuit_breaker.is_triggered