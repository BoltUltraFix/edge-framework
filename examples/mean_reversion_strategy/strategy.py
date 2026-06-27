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
    import time
    from datetime import datetime
    from edge_framework.connectors.paper import PaperConnector
    from edge_framework.risk import RiskManager
    from edge_framework.audit import AuditLogger
    from edge_framework.core.loop import _cycle

    config_path = Path(__file__).parent / 'config.yaml'
    engine = ExecutionEngine(config=str(config_path))
    engine.add_strategy(mean_reversion_strategy)

    # Construir conector desde config
    connector = engine._build_connector_from_config()
    engine.set_connector(connector)
    engine._risk_manager = RiskManager(config=engine._config)
    engine._auditor = AuditLogger(log_path='logs')

    connector.connect()
    account = connector.get_account()
    symbols = engine._config.get('connector', {}).get('symbols', ['XAUUSD'])
    cycle_count = 0

    print(f"\n{'='*55}")
    print(f"  EdgeFramework v0.2.0 — Mean Reversion Strategy")
    print(f"  Balance: ${account.balance:,.2f}")
    print(f"  Simbolos: {', '.join(symbols)}")
    print(f"  Modo: PAPER (sin ordenes reales)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    while True:
        try:
            cycle_count += 1
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n{'='*55}")
            print(f"  Ciclo {cycle_count} | {now}")
            print(f"{'='*55}")

            positions = connector.get_positions()
            print(f"  Balance:    ${account.balance:,.2f}")
            print(f"  Posiciones: {len(positions)} abiertas")

            _cycle(engine, symbols)

            stats = engine._auditor.get_daily_stats()
            print(f"\n  SENALES HOY:")
            print(f"     Evaluadas:  {stats['signals_evaluated']}")
            print(f"     Aprobadas:  {stats['signals_approved']}")
            print(f"     Rechazadas: {stats['signals_rejected']}")
            print(f"     Trades:     {stats['trades_opened']}")

            if positions:
                print(f"\n  POSICIONES:")
                for p in positions:
                    icon = "BUY" if p.direction.value == 'buy' else "SELL"
                    print(f"     {icon} {p.symbol} @ {p.open_price:.2f}")

            reasons = stats.get('rejection_reasons', {})
            if reasons:
                print(f"\n  RECHAZOS:")
                for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
                    print(f"     {reason}: {count}")

            print(f"\n  Proximo ciclo en 30s... (Ctrl+C para parar)")
            time.sleep(30)

        except KeyboardInterrupt:
            print(f"\n  Bot parado — {cycle_count} ciclos completados")
            break
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(30)

    connector.disconnect()