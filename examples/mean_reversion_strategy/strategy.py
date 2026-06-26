import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edge_framework import ExecutionEngine, StrategySignal

def mean_reversion_strategy(symbol, candles):
    if candles is None or len(candles) < 22:
        return None
    close = candles['close']
    sma20 = float(close.rolling(20).mean().iloc[-2])
    std20 = float(close.rolling(20).std().iloc[-2])
    price = float(close.iloc[-2])
    if std20 == 0:
        return None
    upper = sma20 + 2 * std20
    lower = sma20 - 2 * std20
    if price < lower:
        return StrategySignal(symbol, 'buy', 'MEAN_REV_001', 0.7,
                             sl_distance=std20*1.5, tp_distance=std20*3,
                             metadata={'distance': round(sma20-price, 2)})
    if price > upper:
        return StrategySignal(symbol, 'sell', 'MEAN_REV_001', 0.7,
                             sl_distance=std20*1.5, tp_distance=std20*3,
                             metadata={'distance': round(price-sma20, 2)})
    return None

if __name__ == '__main__':
    engine = ExecutionEngine(config='config.yaml')
    engine.add_strategy(mean_reversion_strategy)
    engine.start_from_config()