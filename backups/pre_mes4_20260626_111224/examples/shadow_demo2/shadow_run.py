import sys
import logging
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [DEMO2_SHADOW] %(message)s',
    handlers=[
        logging.FileHandler('logs/shadow_demo2.log', encoding='utf-8'),
    ]
)

from edge_framework import ExecutionEngine, StrategySignal
from edge_framework.connectors.mt5_demo2 import Demo2ShadowConnector
from edge_framework.risk import RiskManager
from edge_framework.audit import AuditLogger
from edge_framework.core.loop import _cycle


def ema_trend_strategy(symbol: str, candles) -> StrategySignal:
    if candles is None or len(candles) < 51:
        return None
    close = candles['close']
    ema20 = close.ewm(span=20).mean().iloc[-2]
    ema50 = close.ewm(span=50).mean().iloc[-2]
    price = close.iloc[-2]
    if ema20 > ema50 and price > ema20:
        return StrategySignal(symbol, 'buy', 'DEMO2_EMA_001', 0.7, sl_distance=15.0, tp_distance=30.0)
    if ema20 < ema50 and price < ema20:
        return StrategySignal(symbol, 'sell', 'DEMO2_EMA_001', 0.7, sl_distance=15.0, tp_distance=30.0)
    return None


def main():
    config = {
        'framework': {'mode': 'shadow', 'interval_seconds': 30},
        'risk': {
            'risk_per_trade': 0.01,
            'max_daily_drawdown': 0.05,
            'max_trades_per_day': 10,
            'circuit_breaker_pct': 0.08,
            'min_volume': 0.01,
            'max_volume': 2.0
        },
        'connector': {'symbols': ['XAUUSD', 'US30.cash', 'US100.cash']}
    }

    engine = ExecutionEngine(config_dict=config)
    connector = Demo2ShadowConnector()
    engine.set_connector(connector)
    engine._risk_manager = RiskManager(config=config)
    engine._auditor = AuditLogger(log_path='logs/shadow')
    engine.add_strategy(ema_trend_strategy)

    if not connector.connect():
        print("❌ No se pudo conectar a MT5 Demo2")
        return

    account = connector.get_account()
    symbols = config['connector']['symbols']
    cycle_count = 0

    print(f"\n{'='*55}")
    print(f"   DEMO2 SHADOW MODE iniciado")
    print(f"   Balance: ${account.balance:,.2f}")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    while True:
        try:
            cycle_count += 1
            cycle_start = time.time()
            now = datetime.now().strftime('%H:%M:%S')

            print(f"\n{'='*55}")
            print(f"   DEMO2 SHADOW | Ciclo {cycle_count} | {now}")
            print(f"{'='*55}")

            account = connector.get_account()
            positions = connector.get_positions()
            print(f"   Balance:    ${account.balance:,.2f}")
            print(f"   Posiciones: {len(positions)} abiertas")

            _cycle(engine, symbols)

            stats = engine._auditor.get_daily_stats()
            print(f"\n   SEÑALES HOY:")
            print(f"     Evaluadas:  {stats['signals_evaluated']}")
            print(f"     Aprobadas:  {stats['signals_approved']}")
            print(f"     Rechazadas: {stats['signals_rejected']}")
            print(f"     Trades:     {stats['trades_opened']}")

            if positions:
                print(f"\n   POSICIONES SHADOW:")
                for p in positions:
                    icon = " BUY" if p.direction.value == 'buy' else " SELL"
                    print(f"     {icon} {p.symbol} @ {p.open_price:.2f} vol={p.volume}")

            reasons = stats.get('rejection_reasons', {})
            if reasons:
                print(f"\n  ❌ RECHAZOS:")
                for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
                    print(f"     {reason}: {count}")

            cycle_time = time.time() - cycle_start
            print(f"\n  ⏱️  Ciclo en {cycle_time:.2f}s | Próximo en 30s...")

            time.sleep(max(0, 30 - cycle_time))

        except KeyboardInterrupt:
            print(f"\n   Demo2 Shadow detenido — {cycle_count} ciclos")
            break
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            time.sleep(30)

    connector.disconnect()


if __name__ == '__main__':
    main()