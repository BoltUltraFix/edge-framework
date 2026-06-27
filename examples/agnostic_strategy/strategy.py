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
    import time
    from datetime import datetime
    from edge_framework.connectors.paper import PaperConnector
    from edge_framework.risk import RiskManager
    from edge_framework.audit import AuditLogger
    from edge_framework.core.loop import _cycle

    config_path = Path(__file__).parent / 'config.yaml'
    engine = ExecutionEngine(config=str(config_path))
    engine.add_strategy(momentum_strategy)

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
    print(f"  EdgeFramework v0.2.0 — Momentum Strategy")
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