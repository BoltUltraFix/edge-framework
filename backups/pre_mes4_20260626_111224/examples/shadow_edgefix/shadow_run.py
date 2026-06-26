"""
EdgeFramework Shadow Mode — EdgeFix
Corre el framework en paralelo con EdgeFix real.
Compara señales sin ejecutar órdenes reales.
Lee datos reales de MT5 (velas, precio, cuenta).
"""

import sys
import logging
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Solo escribir en archivo — sin output en pantalla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SHADOW] %(message)s',
    handlers=[
        logging.FileHandler('logs/shadow_edgefix.log', encoding='utf-8'),
    ]
)
# Silenciar todos los loggers en consola
logging.getLogger().handlers = [
    logging.FileHandler('logs/shadow_edgefix.log', encoding='utf-8')
]
logger = logging.getLogger(__name__)

from edge_framework import ExecutionEngine, StrategySignal
from edge_framework.connectors.mt5_edgefix import EdgeFixShadowConnector
from edge_framework.risk import RiskManager
from edge_framework.audit import AuditLogger
from edge_framework.core.loop import _cycle


# Estrategia simple EMA para comparar
def ema_trend_strategy(symbol: str, candles) -> StrategySignal:
    """
    Estrategia básica de referencia.
    Compara su comportamiento vs EdgeFix real.
    """
    if candles is None or len(candles) < 51:
        return None

    close = candles['close']
    ema20 = close.ewm(span=20).mean().iloc[-2]
    ema50 = close.ewm(span=50).mean().iloc[-2]
    price = close.iloc[-2]

    if ema20 > ema50 and price > ema20:
        return StrategySignal(
            symbol=symbol,
            direction='buy',
            strategy_id='SHADOW_EMA_001',
            confidence=0.7,
            sl_distance=15.0,
            tp_distance=30.0
        )
    if ema20 < ema50 and price < ema20:
        return StrategySignal(
            symbol=symbol,
            direction='sell',
            strategy_id='SHADOW_EMA_001',
            confidence=0.7,
            sl_distance=15.0,
            tp_distance=30.0
        )
    return None


def main():
    logger.info("="*50)
    logger.info("SHADOW MODE — EdgeFramework vs EdgeFix")
    logger.info(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)

    config = {
        'framework': {
            'mode': 'shadow',
            'interval_seconds': 30
        },
        'risk': {
            'risk_per_trade': 0.01,
            'max_daily_drawdown': 0.05,
            'max_trades_per_day': 10,
            'circuit_breaker_pct': 0.08,
            'min_volume': 0.01,
            'max_volume': 2.0
        },
        'connector': {
            'symbols': ['XAUUSD', 'US30.cash', 'US100.cash']
        }
    }

    # Inicializar
    engine = ExecutionEngine(config_dict=config)
    connector = EdgeFixShadowConnector()
    engine.set_connector(connector)
    engine._risk_manager = RiskManager(config=config)
    engine._auditor = AuditLogger(log_path='logs/shadow')
    engine.add_strategy(ema_trend_strategy)

    # Conectar
    if not connector.connect():
        logger.error("No se pudo conectar a MT5")
        return

    account = connector.get_account()
    logger.info(f"Cuenta: ${account.balance:,.2f} (SHADOW — sin órdenes reales)")

    # Loop Shadow
    symbols = config['connector']['symbols']
    cycle_count = 0

    logger.info("Iniciando ciclos Shadow (Ctrl+C para detener)...")

    while True:
        try:
            cycle_count += 1
            cycle_start = time.time()

            # Header del ciclo
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n{'='*55}")
            print(f"   SHADOW MODE | Ciclo {cycle_count} | {now}")
            print(f"{'='*55}")

            # Estado cuenta
            account = connector.get_account()
            positions = connector.get_positions()
            print(f"   Balance:    ${account.balance:,.2f}")
            print(f"   Posiciones: {len(positions)} abiertas")

            # Evaluar ciclo
            _cycle(engine, symbols)

            # Stats del ciclo
            stats = engine._auditor.get_daily_stats()
            print(f"\n   SEÑALES HOY:")
            print(f"     Evaluadas:  {stats['signals_evaluated']}")
            print(f"     Aprobadas:  {stats['signals_approved']}")
            print(f"     Rechazadas: {stats['signals_rejected']}")
            print(f"     Trades:     {stats['trades_opened']}")

            # Posiciones abiertas
            if positions:
                print(f"\n   POSICIONES SHADOW:")
                for p in positions:
                    dir_icon = " BUY" if p.direction.value == 'buy' else " SELL"
                    print(f"     {dir_icon} {p.symbol} @ {p.open_price:.2f} vol={p.volume}")

            # Rechazos
            reasons = stats.get('rejection_reasons', {})
            if reasons:
                print(f"\n  ❌ RECHAZOS:")
                for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
                    print(f"     {reason}: {count}")

            # Tiempo de ciclo
            cycle_time = time.time() - cycle_start
            print(f"\n  ⏱️  Ciclo completado en {cycle_time:.2f}s")
            print(f"  ⏳ Próximo ciclo en 30s...")

            time.sleep(max(0, 30 - cycle_time))

        except KeyboardInterrupt:
            print(f"\n{'='*55}")
            print(f"   Shadow Mode detenido")
            print(f"   Total ciclos: {cycle_count}")
            print(f"   Total señales: {engine._auditor.get_daily_stats()['signals_evaluated']}")
            print(f"{'='*55}\n")
            break
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            time.sleep(30)

    connector.disconnect()
    logger.info("Shadow Mode finalizado")


if __name__ == '__main__':
    main()