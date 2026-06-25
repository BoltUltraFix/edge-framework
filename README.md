# EdgeFramework

Infraestructura de ejecución algorítmica institucional.

## Qué es
EdgeFramework es un framework de ejecución para trading algorítmico
que gestiona automáticamente:
- Ejecución de órdenes con retry inteligente
- Pipeline de riesgo multi-capa
- Auditoría completa de señales y trades
- Trade Intelligence con análisis estadístico

## Qué NO es
EdgeFramework NO incluye estrategias de trading.
Tú traes tu estrategia. EdgeFramework se encarga del resto.

## Instalación
docker run edge-framework (próximamente)

## Uso básico
from edge_framework import ExecutionEngine, RiskManager

engine = ExecutionEngine(config='mi_config.yaml')
engine.add_strategy(mi_estrategia)
engine.start()
