# Ejemplo: EMA Cross Strategy

Estrategia de cruce de medias móviles conectada a EdgeFramework.

## Qué hace
- BUY cuando EMA20 > EMA50 y precio > EMA20
- SELL cuando EMA20 < EMA50 y precio < EMA20
- Gestión de riesgo automática (1% por trade)
- Auditoría completa en logs/

## Cómo ejecutar
```bash
cd examples/simple_ema_strategy
python strategy.py
```

## Logs generados
- `logs/signals_audit.jsonl` — cada señal evaluada
- `logs/trades_audit.jsonl` — cada trade con contexto
- `logs/daily_summary.jsonl` — resumen diario

## Cómo adaptar al tu estrategia
1. Reemplaza `ema_cross_strategy()` con tu lógica
2. Devuelve `StrategySignal` con tu dirección
3. El framework gestiona el resto