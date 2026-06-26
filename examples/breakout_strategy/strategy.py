import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edge_framework import ExecutionEngine, StrategySignal

def breakout_strategy(symbol, candles):
    if candles is None or len(candles) < 22:
        return None
    high_20 = candles['high'].iloc[-21:-2].max()
    low_20 = candles['low'].iloc[-21:-2].min()
    current = candles['close'].iloc[-2]
    atr = float((candles['high'] - candles['low']).rolling(14).mean().iloc[-2])
    if current > high_20:
        return StrategySignal(symbol, 'buy', 'BREAKOUT_001', 0.75,
                             sl_distance=atr, tp_distance=atr*2,
                             metadata={'breakout': 'high', 'level': float(high_20)})
    if current < low_20:
        return StrategySignal(symbol, 'sell', 'BREAKOUT_001', 0.75,
                             sl_distance=atr, tp_distance=atr*2,
                             metadata={'breakout': 'low', 'level': float(low_20)})
    return None

if __name__ == '__main__':
    engine = ExecutionEngine(config='config.yaml')
    engine.add_strategy(breakout_strategy)
    engine.start_from_config()