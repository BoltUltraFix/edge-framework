"""
EdgeFramework — Ejemplo Agnóstico
La estrategia no sabe qué broker usa.
El mismo código funciona en MT5 y Topstep.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edge_framework import ExecutionEngine, StrategySignal


def momentum_strategy(symbol: str, candles) -> StrategySignal:
    """
    Estrategia de momentum simple.
    Funciona en cualquier símbolo/broker
    sin cambiar una línea de código.
    """
    if candles is None or len(candles) < 20:
        return None

    close = candles['close']
    ema10 = close.ewm(span=10).mean().iloc[-2]
    ema20 = close.ewm(span=20).mean().iloc[-2]
    prev_ema10 = close.ewm(span=10).mean().iloc[-3]
    prev_ema20 = close.ewm(span=20).mean().iloc[-3]

    # Cruce alcista
    if prev_ema10 <= prev_ema20 and ema10 > ema20:
        return StrategySignal(
            symbol=symbol,
            direction='buy',
            strategy_id='MOMENTUM_001',
            confidence=0.75,
            sl_distance=20.0,
            tp_distance=40.0,
            metadata={'signal': 'ema_cross_bullish'}
        )

    # Cruce bajista
    if prev_ema10 >= prev_ema20 and ema10 < ema20:
        return StrategySignal(
            symbol=symbol,
            direction='sell',
            strategy_id='MOMENTUM_001',
            confidence=0.75,
            sl_distance=20.0,
            tp_distance=40.0,
            metadata={'signal': 'ema_cross_bearish'}
        )

    return None


if __name__ == '__main__':
    config_path = Path(__file__).parent / 'config.yaml'
    engine = ExecutionEngine(config=str(config_path))
    engine.add_strategy(momentum_strategy)
    engine.start_from_config()