# EdgeFramework — Referencia de API

## ExecutionEngine

```python
engine = ExecutionEngine(config='config.yaml')
```

### Métodos

| Método | Descripción |
|--------|-------------|
| add_strategy(fn) | Añade estrategia al motor |
| set_connector(c) | Conecta broker manualmente |
| start_from_config() | Arranca todo desde YAML |
| start() | Arranca loop principal |
| stop() | Para el motor |

### Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| config | dict | Config cargada |
| is_running | bool | Estado del motor |
| instrument_mapper | InstrumentMapper | Mapeador símbolos |

---

## StrategySignal

```python
signal = StrategySignal(
    symbol='XAUUSD',
    direction='buy',
    strategy_id='MI_001',
    confidence=0.8,
    sl_distance=15.0,
    tp_distance=30.0,
    metadata={'key': 'value'}
)
```

---

## BrokerConnector

```python
from edge_framework.connectors.base import BrokerConnector

class MiConector(BrokerConnector):
    def connect(self) -> bool: ...
    def get_candles(self, symbol, timeframe, count) -> list: ...
    def get_price(self, symbol) -> dict: ...
    def place_order(self, order) -> OrderResult: ...
    def close_position(self, ticket) -> bool: ...
    def get_positions(self, symbol=None) -> list: ...
    def get_account(self) -> AccountInfo: ...
    def modify_sl(self, ticket, new_sl) -> bool: ...
```

---

## RiskManager

```python
from edge_framework.risk import RiskManager

risk = RiskManager(config={'risk': {
    'risk_per_trade': 0.01,
    'max_daily_drawdown': 0.05,
    'max_trades_per_day': 10,
    'circuit_breaker_pct': 0.08
}})

decision = risk.evaluate(signal, account, positions)
if decision.approved:
    print(f'Volumen: {decision.suggested_volume}')
```

---

## AuditLogger

```python
from edge_framework.audit import AuditLogger

auditor = AuditLogger(log_path='logs')
trade_id = auditor.log_trade_open(ticket=1000, symbol='XAUUSD',
    strategy_id='S001', direction='buy', volume=0.1, fill_price=2350.0)
auditor.log_trade_close(ticket=1000, close_price=2380.0, pnl_real=30.0)
stats = auditor.get_daily_stats()
```

---

## InstrumentMapper

```python
from edge_framework import InstrumentMapper

mapper = InstrumentMapper(config)
broker_symbol = mapper.to_broker('US30')    # 'US30.cash'
generic = mapper.from_broker('US30.cash')   # 'US30'
```