"""
EdgeFramework — Ejemplo: EMA Cross Strategy
Estrategia simple de cruce de medias móviles.

Este ejemplo muestra cómo conectar cualquier
estrategia al EdgeFramework en menos de 30 líneas.

El framework se encarga de:
✅ Gestión de riesgo (circuit breaker, DD, lotes)
✅ Ejecución con retry inteligente
✅ Auditoría completa de trades
✅ Health monitoring

Tú solo escribes la lógica de tu estrategia.
"""

import sys
sys.path.insert(0, '../../')

from edge_framework import ExecutionEngine, StrategySignal
from edge_framework.connectors import PaperConnector
from edge_framework.risk import RiskManager
from edge_framework.audit import AuditLogger


# ════════════════════════════════════
# TU ESTRATEGIA (esto es todo lo que escribes tú)
# ════════════════════════════════════

def ema_cross_strategy(symbol: str, candles) -> StrategySignal:
    """
    Estrategia simple: BUY cuando EMA20 > EMA50
    Siempre usa iloc[-2] (vela cerrada, sin repainting)
    """
    if len(candles) < 51:
        return None

    close = candles['close']
    ema20 = close.ewm(span=20).mean().iloc[-2]
    ema50 = close.ewm(span=50).mean().iloc[-2]
    price = close.iloc[-2]

    if ema20 > ema50 and price > ema20:
        return StrategySignal(
            symbol=symbol,
            direction='buy',
            strategy_id='EMA_CROSS_001',
            confidence=0.75,
            sl_distance=15.0,
            tp_distance=30.0
        )

    if ema20 < ema50 and price < ema20:
        return StrategySignal(
            symbol=symbol,
            direction='sell',
            strategy_id='EMA_CROSS_001',
            confidence=0.75,
            sl_distance=15.0,
            tp_distance=30.0
        )

    return None


# ════════════════════════════════════
# CONFIGURACIÓN DEL FRAMEWORK
# ════════════════════════════════════

config = {
    'framework': {
        'mode': 'demo',
        'interval_seconds': 30
    },
    'risk': {
        'risk_per_trade': 0.01,        # 1% por trade
        'max_daily_drawdown': 0.05,    # 5% DD máximo diario
        'max_trades_per_day': 5,       # máx 5 trades/día
        'circuit_breaker_pct': 0.08,   # para todo si -8%
        'min_volume': 0.01,
        'max_volume': 2.0
    },
    'connector': {
        'symbols': ['XAUUSD', 'US30']
    }
}


# ════════════════════════════════════
# ARRANQUE (3 líneas)
# ════════════════════════════════════

if __name__ == '__main__':
    engine = ExecutionEngine(config_dict=config)
    engine.set_connector(PaperConnector(initial_balance=10000.0))
    engine._risk_manager = RiskManager(config=config)
    engine._auditor = AuditLogger(log_path='logs')
    engine.add_strategy(ema_cross_strategy)
    engine._connector.connect()

    print("EdgeFramework iniciado — estrategia EMA Cross activa")
    print("Logs en: examples/simple_ema_strategy/logs/")
    print("Ctrl+C para detener")

    engine.start()