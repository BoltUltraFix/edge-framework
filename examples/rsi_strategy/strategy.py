import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edge_framework import ExecutionEngine, StrategySignal

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def rsi_strategy(symbol, candles):
    if candles is None or len(candles) < 20:
        return None
    rsi_val = rsi(candles['close']).iloc[-2]
    if rsi_val < 30:
        return StrategySignal(symbol, 'buy', 'RSI_001', 0.8,
                             sl_distance=20.0, tp_distance=40.0,
                             metadata={'rsi': round(float(rsi_val), 2)})
    if rsi_val > 70:
        return StrategySignal(symbol, 'sell', 'RSI_001', 0.8,
                             sl_distance=20.0, tp_distance=40.0,
                             metadata={'rsi': round(float(rsi_val), 2)})
    return None

if __name__ == '__main__':
    engine = ExecutionEngine(config='config.yaml')
    engine.add_strategy(rsi_strategy)
    engine.start_from_config()