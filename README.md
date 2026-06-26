# EdgeFramework

Infraestructura de ejecución algorítmica institucional.

## Qué es

EdgeFramework es un framework de ejecución para trading algorítmico que gestiona automáticamente:

- Ejecución de órdenes con retry inteligente
- Pipeline de riesgo multi-capa
- Auditoría completa de señales y trades
- Conexión agnóstica a brokers (MT5, Topstep, paper, shadow)

## Qué NO es

EdgeFramework **no** incluye estrategias de trading. Tú traes tu estrategia; EdgeFramework se encarga del resto.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso básico

```python
from edge_framework import ExecutionEngine, StrategySignal

engine = ExecutionEngine(config='config.yaml')
engine.add_strategy(mi_estrategia)
engine.start_from_config()
```

## Ejemplos incluidos

| Ejemplo | Estrategia | Dificultad |
|---------|-----------|------------|
| simple_ema_strategy | Cruce de medias EMA | Principiante |
| rsi_strategy | RSI Oversold/Overbought | Intermedio |
| breakout_strategy | Breakout de rango | Intermedio |
| mean_reversion_strategy | Reversión a la media | Avanzado |
| agnostic_strategy | Momentum (cualquier broker) | Intermedio |

## Documentación

- [Guía de inicio rápido](docs/GETTING_STARTED.md)
- [Referencia de API](docs/API_REFERENCE.md)
- [Roadmap](ROADMAP.md)

## CLI

```bash
python -m edge_framework.cli version
python -m edge_framework.cli start --config config.yaml
```

Versión actual: **0.2.0**