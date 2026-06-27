# EdgeFramework — Guía de inicio rápido

## De cero a tu primer trade en 20 minutos

EdgeFramework es infraestructura de ejecución para trading algorítmico. **Tú escribes la estrategia**; el framework gestiona riesgo, ejecución, auditoría y conexión al broker.

---

### Paso 1: Instalación (5 min)

```bash
pip install pandas numpy pyyaml
# Opcional — solo si usas MT5 real:
pip install MetaTrader5

cd C:\Users\Bot5U\Desktop\EdgeFramework
pip install -r requirements.txt
```

Requisitos: Python 3.10+.

---

### Paso 2: Tu primera estrategia (10 min)

Crea un archivo `mi_estrategia.py`:

```python
from edge_framework import ExecutionEngine, StrategySignal

def mi_estrategia(symbol, candles):
    if candles is None or len(candles) < 20:
        return None
    close = candles['close']
    ema20 = close.ewm(span=20).mean().iloc[-2]
    price = close.iloc[-2]
    if price > ema20:
        return StrategySignal(symbol, 'buy', 'MI_001', 0.7,
                             sl_distance=15.0, tp_distance=30.0)
    return None

engine = ExecutionEngine(config='config.yaml')
engine.add_strategy(mi_estrategia)
engine.start_from_config()
```

Crea un archivo `config.yaml`:

```yaml
framework:
  mode: "paper"
  interval_seconds: 30

connector:
  type: "paper"
  symbols:
    - "XAUUSD"

risk:
  risk_per_trade: 0.01
  max_daily_drawdown: 0.05
  max_trades_per_day: 5
  circuit_breaker_pct: 0.08
  min_volume: 0.01
  max_volume: 2.0

audit:
  enabled: true
  log_path: "logs"
```

---

### Paso 3: Ejecutar (5 min)

```bash
python mi_estrategia.py
```

Verás en pantalla algo como:

```
INFO EdgeFramework iniciado — modo: paper
INFO [InstrumentMapper] 0 instrumentos configurados
INFO Estrategia añadida: mi_estrategia
INFO [PaperConnector] Conectado — paper trading activo
INFO Conectado: balance=$10,000.00 modo=paper
INFO Motor iniciado con 1 estrategia(s)
INFO [Loop] Iniciado — símbolos: ['XAUUSD'] | intervalo: 30s
```

Cuando haya señal aprobada:

```
INFO [XAUUSD] ✅ Trade ejecutado: BUY vol=0.01 ticket=1000 fill=...
```

Los logs de auditoría se guardan en `logs/`:

| Archivo | Contenido |
|---------|-----------|
| `signals_audit.jsonl` | Cada señal evaluada (aprobada o rechazada) |
| `trades_audit.jsonl` | Cada trade ejecutado con contexto |
| `daily_summary.jsonl` | Resumen diario |

`Ctrl+C` detiene el bot limpiamente.

---

### Paso 4: Usar el CLI (opcional)

```bash
python -m edge_framework.cli version
python -m edge_framework.cli start --config config.yaml
python -m edge_framework.cli status
```

---

### Paso 5: Cambiar de broker sin tocar código

Solo edita `config.yaml`:

| Modo | `connector.type` |
|------|------------------|
| Paper (testing) | `paper` |
| MT5 real | `mt5` |
| Topstep | `topstep` |
| Shadow (solo lectura MT5) | `shadow` |

Ejemplo MT5:

```yaml
connector:
  type: "mt5"
  symbols:
    - "XAUUSD"
    - "US30"
  instrument_map:
    XAUUSD: "XAUUSD"
    US30: "US30.cash"
  mt5:
    login: 12345678
    password: "tu_password"
    server: "FTMO-Demo"
    terminal_path: "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
```

La estrategia **no cambia** — solo el YAML.

### Conectar a MT5 (cuando estés listo)

Cambia solo el `config.yaml`:

```yaml
connector:
  type: "mt5"
  symbols:
    - "XAUUSD"
  mt5:
    login: TU_LOGIN
    password: "TU_PASSWORD"
    server: "TU_BROKER"
    terminal_path: "C:\\...\\terminal64.exe"
```

Tu estrategia no cambia. Solo el config.

---

### Ejemplos incluidos

| Carpeta | Descripción |
|---------|-------------|
| `examples/simple_ema_strategy/` | Cruce EMA20/EMA50 en paper |
| `examples/rsi_strategy/` | RSI oversold/overbought |
| `examples/breakout_strategy/` | Breakout de rango 20 velas |
| `examples/mean_reversion_strategy/` | Reversión a la media (Bollinger simple) |
| `examples/agnostic_strategy/` | Momentum agnóstico de broker |

```bash
cd examples/simple_ema_strategy
python strategy.py
```

---

### Reglas de oro

1. **Estrategias usan `iloc[-2]`** — vela cerrada, sin repainting.
2. **Devuelve `StrategySignal` o `None`** — el framework decide si ejecutar.
3. **Todo en YAML** — símbolos, riesgo, broker, auditoría.
4. **`instrument_map`** — traduce nombres genéricos (`US30`) a nombres del broker (`US30.cash`, `MYM`, etc.).

---

### Siguiente paso

- Config completa: `edge_framework/config/default_config.yaml`
- Roadmap: `ROADMAP.md`
- Versión actual: `0.2.0`