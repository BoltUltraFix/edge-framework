# EdgeFramework

> Infraestructura algorítmica para traders de prop firms.
> Conecta tu estrategia a FTMO, Topstep o cualquier broker en minutos.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-orange.svg)](CHANGELOG.md)

---

 **[edgeframework.netlify.app](https://edgeframework.netlify.app)** — Landing page y lista de espera

 **[Discord](https://discord.gg/gzPNgVcx8)** — Comunidad y soporte

---

---

## El problema

El 90% del tiempo de un trader algorítmico no se gasta en la estrategia. Se gasta en infraestructura.

- Reconectar MT5 cuando se cae
- Gestionar riesgo manualmente
- Reescribir el mismo código para cada broker
- Depurar logs a las 3am

## La solución

```python
engine = ExecutionEngine(config='config.yaml')
engine.add_strategy(mi_estrategia)
engine.start_from_config()
# Eso es todo.
```

EdgeFramework hace el resto: conexión al broker, riesgo automático, logs, reconexiones y circuit breaker.

---

## Instalación

```bash
git clone https://github.com/BoltUltraFix/edge-framework
cd edge-framework
pip install -r requirements.txt
```

---

## Inicio rápido

1. Copia un ejemplo:

```bash
cp -r examples/simple_ema_strategy mi_bot/
cd mi_bot/
```

2. Edita `config.yaml` con tu broker:

```yaml
connector:
  type: "mt5"
  mt5:
    login: TU_LOGIN
    password: "TU_PASSWORD"
    server: "FTMO-Demo"
```

3. Ejecuta:

```bash
python strategy.py
```

---

## Brokers soportados

| Broker | Tipo | Estado |
|--------|------|--------|
| FTMO | MT5 | Produccion |
| Topstep | API REST | Produccion |
| Paper | Simulado | Incluido |
| Shadow | Solo lectura MT5 | Avanzado |

---

## Ejemplos incluidos

| Ejemplo | Estrategia | Nivel |
|---------|-----------|-------|
| simple_ema_strategy | Cruce EMA | Principiante |
| rsi_strategy | RSI Oversold/Overbought | Intermedio |
| breakout_strategy | Breakout de rango | Intermedio |
| mean_reversion_strategy | Reversión a la media | Avanzado |
| agnostic_strategy | Momentum multi-broker | Intermedio |

---

## Documentación

- [Guía de inicio rápido](docs/GETTING_STARTED.md)
- [Referencia de API](docs/API_REFERENCE.md)
- [Roadmap](ROADMAP.md)

---

## Arquitectura

```
edge_framework/
├── engine.py              # ExecutionEngine — orquestador principal
├── cli.py                 # CLI: start / status / version
├── core/loop.py           # Ciclo de trading (señal → riesgo → ejecución)
├── connectors/
│   ├── base.py            # Interfaz BrokerConnector
│   ├── mt5.py             # MetaTrader 5
│   ├── topstep.py         # Topstep API
│   ├── paper.py           # Paper trading
│   └── instrument_mapper.py
├── risk/manager.py        # Circuit breaker, DD, position sizing
├── audit/logger.py        # Auditoría JSONL
└── api/status.py          # FastAPI /health /status /metrics

examples/                  # Estrategias de referencia
docs/                      # Documentación
```

Flujo por ciclo:

```
YAML config → Connector → Velas → Estrategia → RiskManager → Orden → AuditLogger
```

---

## CLI

```bash
python -m edge_framework.cli version
python -m edge_framework.cli start --config config.yaml
```

---

## Docker

```bash
docker build -t edge-framework .
docker-compose up
```

---

## Licencia

MIT — ver [LICENSE](LICENSE).

---

## Contribuir

1. Fork del repositorio
2. Crea una rama (`git checkout -b feature/mi-mejora`)
3. Commit (`git commit -m 'Añade mi mejora'`)
4. Push y abre un Pull Request

---

**EdgeFramework v0.2.0** — Infraestructura para traders serios.