"""
EdgeFramework — Loop Principal
Ciclo de trading que une todos los módulos.

Flujo por ciclo:
1. Obtener cuenta y posiciones
2. Para cada símbolo configurado:
   a. Obtener velas (iloc[-2] — vela cerrada)
   b. Evaluar cada estrategia
   c. Si hay señal → RiskManager.evaluate()
   d. Si aprobado → Ejecutar orden
   e. AuditLogger.log_signal() siempre
   f. AuditLogger.log_trade_open() si ejecutado
3. Health Check del ciclo
4. Sleep hasta próximo ciclo
"""

import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edge_framework.engine import ExecutionEngine

logger = logging.getLogger(__name__)

MAX_CYCLE_TIME = 35.0
_slow_cycles = 0


def run_loop(engine: "ExecutionEngine") -> None:
    """Loop principal del motor."""
    global _slow_cycles

    interval = engine.config.get("framework", {}).get("interval_seconds", 30)
    symbols = engine.config.get("connector", {}).get("symbols", [])

    logger.info(f"[Loop] Iniciado — símbolos: {symbols} | intervalo: {interval}s")

    while engine.is_running:
        cycle_start = time.time()
        try:
            _cycle(engine, symbols)
        except KeyboardInterrupt:
            logger.info("[Loop] Detenido por usuario")
            engine.stop()
            break
        except Exception as e:
            logger.error(f"[Loop] Error en ciclo: {e}")

        # Health Check
        cycle_duration = time.time() - cycle_start
        if cycle_duration > MAX_CYCLE_TIME:
            _slow_cycles += 1
            logger.warning(
                f"[Loop] ⚠️ CYCLE DEGRADATION: {cycle_duration:.2f}s "
                f"(límite {MAX_CYCLE_TIME}s) — ciclo lento {_slow_cycles}/3"
            )
            if _slow_cycles >= 3:
                if engine._connector:
                    pass  # notify via telegram si está configurado
                _slow_cycles = 0
        else:
            _slow_cycles = 0

        time.sleep(max(0, interval - cycle_duration))


def _cycle(engine: "ExecutionEngine", symbols: list) -> None:
    """Un ciclo completo de evaluación y ejecución."""

    connector = engine._connector
    risk = engine._risk_manager
    auditor = engine._auditor

    if not connector or not connector.is_connected():
        logger.warning("[Loop] Sin conector activo — saltando ciclo")
        return

    # Obtener estado de cuenta
    try:
        account = connector.get_account()
        all_positions = connector.get_positions()
    except Exception as e:
        logger.error(f"[Loop] Error obteniendo cuenta: {e}")
        return

    # Evaluar cada símbolo
    for symbol in symbols:
        try:
            _evaluate_symbol(engine, symbol, account, all_positions)
        except Exception as e:
            logger.error(f"[Loop] Error evaluando {symbol}: {e}")


def _evaluate_symbol(engine, symbol: str, account, all_positions: list) -> None:
    """Evalúa un símbolo con todas las estrategias."""

    connector = engine._connector
    risk = engine._risk_manager
    auditor = engine._auditor
    broker_symbol = engine.instrument_mapper.to_broker(symbol)

    # Obtener velas — siempre usar iloc[-2] (vela cerrada)
    try:
        candles = connector.get_candles(broker_symbol, "M5", count=500)
        if not candles or len(candles) < 3:
            logger.debug(f"[{symbol}] Velas insuficientes: {len(candles) if candles else 0}")
            return
    except Exception as e:
        logger.error(f"[{symbol}] Error obteniendo velas: {e}")
        return

    # Convertir a formato para estrategias
    import pandas as pd
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open, 'high': c.high,
        'low': c.low, 'close': c.close,
        'volume': c.volume
    } for c in candles])

    # Evaluar cada estrategia
    for strategy in engine.strategies:
        try:
            signal = strategy(symbol, df)
        except Exception as e:
            logger.error(f"[{symbol}] Error en estrategia: {e}")
            continue

        if signal is None or signal.direction == "none":
            continue

        if not signal.is_valid():
            logger.warning(f"[{symbol}] Señal inválida de {signal.strategy_id}")
            continue

        signal.metadata['broker_symbol'] = broker_symbol

        # Evaluar riesgo
        if risk:
            decision = risk.evaluate(signal, account, all_positions)
        else:
            # Sin RiskManager → aprobación básica
            from edge_framework.risk.manager import RiskDecision
            decision = RiskDecision(True, "no_risk_manager", suggested_volume=0.01)

        # Audit de la señal SIEMPRE
        if auditor:
            auditor.log_signal(
                symbol=symbol,
                strategy_id=signal.strategy_id,
                direction=signal.direction,
                confidence=signal.confidence,
                approved=decision.approved,
                rejection_reason=None if decision.approved else decision.reason,
                suggested_volume=decision.suggested_volume,
                sl_distance=signal.sl_distance,
                tp_distance=signal.tp_distance,
                metadata=signal.metadata
            )

        if not decision.approved:
            logger.debug(f"[{symbol}] Señal rechazada: {decision.reason}")
            continue

        # Ejecutar orden
        _execute_signal(engine, signal, decision, account, broker_symbol)
        break  # Un trade por símbolo por ciclo


def _execute_signal(engine, signal, decision, account, broker_symbol: str = None) -> None:
    """Ejecuta una señal aprobada."""
    from edge_framework.connectors.base import OrderRequest, OrderDirection

    connector = engine._connector
    risk = engine._risk_manager
    auditor = engine._auditor

    direction = OrderDirection.BUY if signal.direction == "buy" else OrderDirection.SELL
    order_symbol = broker_symbol or signal.metadata.get('broker_symbol') or engine.instrument_mapper.to_broker(signal.symbol)

    order = OrderRequest(
        symbol=order_symbol,
        direction=direction,
        volume=decision.suggested_volume,
        sl_distance=signal.sl_distance,
        tp_distance=signal.tp_distance,
        comment=f"EF_{signal.strategy_id}"
    )

    try:
        result = connector.place_order(order)
    except Exception as e:
        logger.error(f"[{signal.symbol}] Error ejecutando orden: {e}")
        return

    if not result.success:
        logger.error(
            f"[{signal.symbol}] Orden rechazada: "
            f"{result.error_code} {result.error_message}"
        )
        return

    # Registrar trade
    if risk:
        risk.register_trade()

    if auditor and result.ticket:
        # Snapshot de mercado
        try:
            price = connector.get_price(order_symbol)
            spread = price.get('spread', 0)
        except Exception:
            spread = 0

        auditor.log_trade_open(
            ticket=result.ticket,
            symbol=signal.symbol,
            strategy_id=signal.strategy_id,
            direction=signal.direction,
            volume=decision.suggested_volume,
            fill_price=result.fill_price or 0,
            sl_distance=signal.sl_distance,
            rr_expected=(signal.tp_distance / signal.sl_distance)
                if signal.sl_distance and signal.tp_distance else None,
            market_snapshot={
                "spread": spread,
                "confidence": signal.confidence,
                "balance": account.balance,
                "equity": account.equity,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    logger.info(
        f"[{signal.symbol}] ✅ Trade ejecutado: "
        f"{signal.direction.upper()} vol={decision.suggested_volume} "
        f"ticket={result.ticket} fill={result.fill_price}"
    )