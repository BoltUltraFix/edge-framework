"""
EdgeFramework — AuditLogger
Auditoría completa de señales y trades.

Registra:
- Cada señal evaluada (aprobada o rechazada)
- Cada trade ejecutado con snapshot de mercado
- Cada trade cerrado con resultado real
- Estadísticas diarias automáticas

Los datos se guardan en JSONL para análisis posterior.
El cliente puede conectar su propio analizador
o usar el TradeIntelligence incluido.
"""

import json
import logging
import time
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SignalAuditRecord:
    """Registro de una señal evaluada."""
    timestamp: str
    symbol: str
    strategy_id: str
    direction: str
    confidence: float
    approved: bool
    rejection_reason: Optional[str]
    risk_multiplier: float
    suggested_volume: float
    sl_distance: Optional[float]
    tp_distance: Optional[float]
    metadata: Dict = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['metadata'] = self.metadata or {}
        return d


@dataclass
class TradeAuditRecord:
    """Registro completo de un trade."""
    trade_id: str
    timestamp_open: str
    symbol: str
    strategy_id: str
    direction: str
    volume: float
    fill_price: float
    sl: Optional[float]
    tp: Optional[float]
    sl_distance: Optional[float]
    rr_expected: Optional[float]
    market_snapshot: Dict
    # Campos de cierre (se rellenan después)
    timestamp_close: Optional[str] = None
    close_price: Optional[float] = None
    result: Optional[str] = None  # WIN | LOSS | BE | PARTIAL
    pnl_real: Optional[float] = None
    r_multiple: Optional[float] = None
    exit_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class AuditLogger:
    """
    Sistema de auditoría completo para EdgeFramework.

    Genera automáticamente:
    - logs/signals_audit.jsonl
    - logs/trades_audit.jsonl
    - logs/daily_summary.jsonl
    """

    def __init__(self, log_path: str = "logs", enabled: bool = True):
        self.enabled = enabled
        self._log_path = Path(log_path)
        self._log_path.mkdir(parents=True, exist_ok=True)

        self._signals_file = self._log_path / "signals_audit.jsonl"
        self._trades_file = self._log_path / "trades_audit.jsonl"
        self._summary_file = self._log_path / "daily_summary.jsonl"

        # Índice en memoria: trade_id → TradeAuditRecord
        self._open_trades: Dict[str, TradeAuditRecord] = {}
        # Índice: ticket → trade_id
        self._ticket_to_trade: Dict[int, str] = {}

        # Contadores diarios
        self._daily_stats = self._reset_daily_stats()
        self._current_day: Optional[date] = None

        logger.info(f"[AuditLogger] Iniciado — logs en: {self._log_path}")

    def _reset_daily_stats(self) -> Dict:
        return {
            "date": str(date.today()),
            "signals_evaluated": 0,
            "signals_approved": 0,
            "signals_rejected": 0,
            "trades_opened": 0,
            "trades_closed": 0,
            "wins": 0,
            "losses": 0,
            "pnl_total": 0.0,
            "rejection_reasons": {}
        }

    def _check_new_day(self) -> None:
        today = date.today()
        if self._current_day != today:
            if self._current_day is not None:
                self._flush_daily_summary()
            self._current_day = today
            self._daily_stats = self._reset_daily_stats()

    def _write_jsonl(self, filepath: Path, record: Dict) -> None:
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"[AuditLogger] Error escribiendo {filepath}: {e}")

    def log_signal(
        self,
        symbol: str,
        strategy_id: str,
        direction: str,
        confidence: float,
        approved: bool,
        rejection_reason: Optional[str] = None,
        risk_multiplier: float = 1.0,
        suggested_volume: float = 0.0,
        sl_distance: Optional[float] = None,
        tp_distance: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        if not self.enabled:
            return
        self._check_new_day()

        record = SignalAuditRecord(
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            strategy_id=strategy_id,
            direction=direction,
            confidence=confidence,
            approved=approved,
            rejection_reason=rejection_reason,
            risk_multiplier=risk_multiplier,
            suggested_volume=suggested_volume,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
            metadata=metadata,
        )

        self._daily_stats["signals_evaluated"] += 1
        if approved:
            self._daily_stats["signals_approved"] += 1
        else:
            self._daily_stats["signals_rejected"] += 1
            if rejection_reason:
                reasons = self._daily_stats["rejection_reasons"]
                reasons[rejection_reason] = reasons.get(rejection_reason, 0) + 1

        self._write_jsonl(self._signals_file, record.to_dict())
        logger.debug(
            f"[AuditLogger] Señal {symbol} {direction} — "
            f"{'aprobada' if approved else 'rechazada: ' + str(rejection_reason)}"
        )

    def log_trade_open(
        self,
        *,
        ticket: int,
        symbol: str,
        strategy_id: str,
        direction: str,
        volume: float,
        fill_price: float,
        sl_distance: Optional[float] = None,
        rr_expected: Optional[float] = None,
        market_snapshot: Optional[Dict[str, Any]] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> str:
        """Registra apertura de trade. Devuelve trade_id."""
        if not self.enabled:
            return ""
        self._check_new_day()

        trade_id = f"T-{symbol}-{uuid.uuid4().hex[:8]}"
        if rr_expected is None and sl is not None and tp is not None and fill_price:
            risk = abs(fill_price - sl)
            reward = abs(tp - fill_price)
            if risk > 0:
                rr_expected = round(reward / risk, 2)

        record = TradeAuditRecord(
            trade_id=trade_id,
            timestamp_open=datetime.utcnow().isoformat(),
            symbol=symbol,
            strategy_id=strategy_id,
            direction=direction,
            volume=volume,
            fill_price=fill_price,
            sl=sl,
            tp=tp,
            sl_distance=sl_distance,
            rr_expected=rr_expected,
            market_snapshot=market_snapshot or {},
        )

        self._open_trades[trade_id] = record
        self._ticket_to_trade[ticket] = trade_id
        self._daily_stats["trades_opened"] += 1
        self._write_jsonl(self._trades_file, record.to_dict())
        logger.info(f"[AuditLogger] Trade abierto: {trade_id} {symbol} {direction} @ {fill_price}")
        return trade_id

    def log_trade_close(
        self,
        ticket: int,
        close_price: float,
        pnl_real: float,
        exit_reason: str = "manual",
    ) -> None:
        """Registra cierre de trade por ticket."""
        if not self.enabled:
            return
        self._check_new_day()

        trade_id = self._ticket_to_trade.get(ticket)
        if not trade_id:
            logger.warning(f"[AuditLogger] Cierre sin trade_id para ticket={ticket}")
            return

        record = self._open_trades.get(trade_id)
        if not record:
            logger.warning(f"[AuditLogger] Cierre sin registro abierto: {trade_id}")
            return

        record.timestamp_close = datetime.utcnow().isoformat()
        record.close_price = close_price
        record.pnl_real = round(pnl_real, 2)
        record.exit_reason = exit_reason
        record.result = self._classify_result(pnl_real)

        if record.sl_distance and record.sl_distance > 0:
            record.r_multiple = round(pnl_real / (record.sl_distance * record.volume), 2)

        self._daily_stats["trades_closed"] += 1
        self._daily_stats["pnl_total"] = round(
            self._daily_stats["pnl_total"] + pnl_real, 2
        )
        if record.result == "WIN":
            self._daily_stats["wins"] += 1
        elif record.result == "LOSS":
            self._daily_stats["losses"] += 1

        self._write_jsonl(self._trades_file, record.to_dict())
        self._open_trades.pop(trade_id, None)
        self._ticket_to_trade.pop(ticket, None)
        logger.info(
            f"[AuditLogger] Trade cerrado: {trade_id} "
            f"pnl={pnl_real:.2f} result={record.result}"
        )

    @staticmethod
    def _classify_result(pnl: float) -> str:
        if pnl > 1.0:
            return "WIN"
        if pnl < -1.0:
            return "LOSS"
        return "BE"

    def _flush_daily_summary(self) -> None:
        self._write_jsonl(self._summary_file, dict(self._daily_stats))
        logger.info(f"[AuditLogger] Resumen diario guardado: {self._daily_stats['date']}")

    def flush(self) -> None:
        """Fuerza escritura del resumen diario (llamar al apagar el motor)."""
        if self.enabled:
            self._flush_daily_summary()

    @property
    def daily_stats(self) -> Dict:
        self._check_new_day()
        return dict(self._daily_stats)

    def get_daily_stats(self) -> Dict:
        """Alias de daily_stats para compatibilidad con el loop."""
        return self.daily_stats

    @property
    def open_trades_count(self) -> int:
        return len(self._open_trades)