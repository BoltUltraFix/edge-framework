# EdgeFramework — Roadmap 12 Meses
### De bot personal a producto SaaS institucional
**Inicio:** Junio 2026

---

## ESTADO ACTUAL

```
Bot EdgeFix en producción:
✅ PF 1.64 | WR 57% | +$2,358 en 10 días
✅ Modulador institucional activo
✅ Trade Intelligence Layer completo
✅ Signal Funnel Audit activo
✅ 3 plataformas: FTMO + Topstep + Demo2
```

---

# TRIMESTRE 1 — DECOUPLING
### Separar el motor del chasis sin romper nada
**Objetivo:** EdgeFramework funciona. EdgeFix lo usa internamente.

---

## MES 1 — BASE DEL FRAMEWORK ✅ COMPLETADO

### Lo que se construyó:
```
✅ edge_framework/engine.py
   → ExecutionEngine (motor principal)
   → StrategySignal (contrato del cliente)
   → add_strategy(), set_connector(), start()

✅ edge_framework/connectors/base.py
   → BrokerConnector (interfaz abstracta)
   → OrderRequest, OrderResult, Position
   → Candle, AccountInfo

✅ edge_framework/connectors/paper.py
   → PaperConnector (paper trading sin broker)
   → Velas sintéticas para testing
   → Órdenes simuladas con tickets reales

✅ edge_framework/risk/manager.py
   → RiskManager (5 capas Early Return)
   → CircuitBreaker
   → DailyDrawdownGuard
   → TradeCounter
   → RiskCalculator (volumen por ATR)

✅ edge_framework/audit/logger.py
   → AuditLogger completo
   → log_signal() → signals_audit.jsonl
   → log_trade_open() → trades_audit.jsonl
   → log_trade_close() con WIN/LOSS/BE/R
   → daily_summary.jsonl automático

✅ edge_framework/core/loop.py
   → Loop principal completo
   → Health Check ciclo >35s
   → Evaluación por símbolo
   → Integración Risk + Audit + Connector

✅ examples/simple_ema_strategy/
   → Ejemplo funcional en 30 líneas
   → EMA Cross con gestión de riesgo
   → README del cliente

✅ README.md, requirements.txt, .gitignore
```

### Verificación:
```
✅ Import OK
✅ PaperConnector operativo
✅ RiskManager: CircuitBreaker funciona
✅ AuditLogger: signals + trades generados
✅ Loop: 3 ciclos, 4 señales, 2 trades
✅ ast.parse() OK en todos los archivos
```

---

## MES 2 — CONECTORES REALES ⏳ PENDIENTE

### Tareas:

```
[ ] MT5Connector
    ARCHIVO: edge_framework/connectors/mt5.py
    → connect() via MetaTrader5 Python API
    → get_candles() → copy_rates_from_pos()
      con timeout y guard len < 3
    → get_price() → symbol_info_tick()
    → place_order() → _order_send_with_retry()
      (precio fresco en cada intento)
    → close_position() → order_send() SELL/BUY
    → get_positions() → positions_get()
    → modify_sl() → order_send() SLTP
    → Spread check antes de retry
    → Lot 0.0 bloqueado

[ ] TopstepConnector
    ARCHIVO: edge_framework/connectors/topstep.py
    → Portar conector_topstep.py al framework
    → HTTP directo (no SDK)
    → modify_sl() via /api/Order/modify
    → cancel_open_orders() en close
    → Tick alignment (get_point_value)
    → Split TP1/TP2 50/50

[ ] Verificación MT5Connector:
    → Conectar a cuenta FTMO Demo
    → get_candles() devuelve datos reales
    → place_order() ejecuta en MT5
    → Resultado en MetaTrader visible

[ ] Verificación TopstepConnector:
    → Conectar a Practice $150K
    → Trade ejecutado con SL+TP1+TP2
    → Cleanup huérfanas al cerrar
```

### Criterio de éxito:
```
MT5: engine.set_connector(MT5Connector()) → trade real en MT5
Topstep: engine.set_connector(TopstepConnector()) → trade real en Topstep
```

---

## MES 3 — MIGRACIÓN SILENCIOSA ⏳ PENDIENTE

### Tareas:

```
[ ] Inventario Alpha vs SaaS
    → Tabla exacta módulo por módulo
    → Qué va al framework (SaaS)
    → Qué se queda en EdgeFix (Alpha)
    → Verificar que signal_funnel no revela
      nombres de estrategias

[ ] EdgeFix migrado al framework
    → bots/bot5_multi_split.py usa
      EdgeFramework internamente
    → MT5Connector como conector
    → RiskManager del framework
    → AuditLogger del framework
    → Modulador institucional = plugin Alpha
      (no expuesto en el framework)

[ ] Bot5Multi migrado al framework
    → TopstepConnector del framework
    → Mismo RiskManager
    → Mismo AuditLogger

[ ] Validación 2 semanas:
    → EdgeFix sigue operando igual
    → PF igual o mejor
    → Sin errores nuevos
    → Trade Intelligence con datos reales

[ ] Git tags:
    → v0.1.0 (hoy — base)
    → v0.2.0 (conectores reales)
    → v0.3.0 (migración EdgeFix)
```

### Criterio de éxito:
```
EdgeFix opera sobre EdgeFramework
PF real ≥ 1.4 durante 2 semanas
Sin regresiones en comportamiento
```

---

# TRIMESTRE 2 — PRODUCTIZACIÓN
### Que no parezca tuyo. Que funcione para cualquiera.
**Objetivo:** Cualquier developer puede usar EdgeFramework con su propia estrategia.

---

## MES 4 — CONFIGURACIÓN POR YAML ⏳ PENDIENTE

```
[ ] Todo configurable sin tocar código:
    → Símbolos en config.yaml
    → Riesgo en config.yaml
    → Sesiones en config.yaml
    → Conector en config.yaml

[ ] CLI básico:
    edge-framework start --config mi_config.yaml
    edge-framework status
    edge-framework stop

[ ] Validación de config al arrancar:
    → Campos obligatorios
    → Tipos correctos
    → Valores dentro de rangos seguros
    → Error claro si algo falta

[ ] Ejemplo con config.yaml completo:
    → Comentado línea a línea
    → Para un novato que nunca vio el código
```

---

## MES 5 — AGNÓSTICO DE BROKER/SÍMBOLO ⏳ PENDIENTE

```
[ ] Sin hardcoding de símbolos:
    → No "XAUUSD" en el código del framework
    → El cliente define sus símbolos en config
    → Framework los mapea al conector

[ ] Sin hardcoding de valores:
    → ATR mínimos en config, no en código
    → Timeframes en config
    → Sesiones en config

[ ] Conector genérico para cualquier broker:
    → Interface limpia que acepta cualquier
      implementación de BrokerConnector
    → El cliente puede escribir su propio
      conector en 1 hora

[ ] Test con símbolo inventado:
    → engine.set_connector(PaperConnector())
    → config: symbols: ["PEPINO_FUTURES"]
    → Framework funciona sin cambiar código
```

---

## MES 6 — TUTORIAL Y DOCUMENTACIÓN ⏳ PENDIENTE

```
[ ] Tutorial "Hola Mundo del Quant":
    → Instalar EdgeFramework (5 min)
    → Escribir estrategia EMA (10 min)
    → Ver primer trade en logs (5 min)
    → Total: 20 minutos de cero a trading

[ ] Documentación GitBook:
    → Introducción y conceptos
    → BrokerConnector: cómo implementar
    → RiskManager: parámetros explicados
    → AuditLogger: cómo leer los JSONL
    → Ejemplos por caso de uso

[ ] 3 ejemplos adicionales:
    → RSI Oversold/Overbought
    → Breakout de rango
    → Mean Reversion simple

[ ] API Reference completa:
    → Cada clase documentada
    → Cada método con tipos y ejemplos
    → Docstrings en inglés
```

---

# TRIMESTRE 3 — DOCKERIZACIÓN Y BETA
### Que un cliente pueda instalarlo sin saber Python.
**Objetivo:** docker run edge-framework → funciona.

---

## MES 7 — DOCKER ⏳ PENDIENTE

```
[ ] Dockerfile:
    FROM python:3.12-slim
    → Instala dependencias
    → Copia el framework
    → Expone puerto para API status

[ ] docker-compose.yaml:
    → edge-framework (motor)
    → volumen para logs/
    → volumen para config/

[ ] Comando final del cliente:
    docker run -v ./config:/config \
               -v ./logs:/logs \
               -v ./strategies:/strategies \
               edge-framework

[ ] Test en Windows + Linux + Mac:
    → Mismo comando funciona en los 3
    → Sin instalar Python
    → Sin instalar pandas/numpy

[ ] API de status HTTP básica:
    GET /status → { running, trades_today, pnl_today }
    GET /positions → posiciones abiertas
    POST /stop → para el bot limpiamente
```

---

## MES 8 — DOCUMENTACIÓN Y VIDEOS ⏳ PENDIENTE

```
[ ] GitBook publicado:
    → docs.edgeframework.io (o similar)
    → Dominio propio

[ ] 3 videos de 10 minutos:
    → Video 1: Instalación con Docker
    → Video 2: Conectar mi estrategia
    → Video 3: Entender los logs y auditoría

[ ] Landing page básica:
    → Webflow o Framer
    → Qué es EdgeFramework (30 segundos)
    → Ejemplo de código (30 líneas)
    → Precio visible
    → CTA: "Empezar gratis"

[ ] Discord de la comunidad:
    → Canal #general
    → Canal #soporte (tickets)
    → Canal #showcase (usuarios comparten)
    → Bot de bienvenida
```

---

## MES 9 — BETA CERRADA ⏳ PENDIENTE

```
[ ] Reclutar 3-5 beta testers:
    → Foros de algo trading (r/algotrading)
    → Discord de Python trading
    → Comunidades MT5/MQL5
    → Tu red personal

[ ] Propuesta para beta:
    "Tengo un framework de ejecución para MT5
     en Python. Gratis 3 meses a cambio de
     feedback detallado. ¿Te interesa?"

[ ] Proceso de beta:
    → Semana 1: instalación y primer trade
    → Semana 2: estrategia propia conectada
    → Semana 3: feedback de bugs y mejoras
    → Semana 4: fixes y re-test

[ ] Métricas de éxito beta:
    → 3/5 usuarios llegan al primer trade
    → 0 bugs críticos sin solución
    → NPS > 7/10 promedio

[ ] Fixes post-beta:
    → Lista priorizada de bugs
    → Solo arreglar los críticos
    → No añadir features nuevas aún
```

---

# TRIMESTRE 4 — LANZAMIENTO
### Primer dólar recurrente.
**Objetivo:** 10-20 clientes pagando. MRR establecido.

---

## MES 10 — PRICING Y LANDING PAGE ⏳ PENDIENTE

```
[ ] Modelo de pricing:
    GRATIS (open source):
    → ExecutionEngine básico
    → PaperConnector
    → RiskManager básico
    → 1 símbolo

    PRO ($99/mes o $999/año):
    → MT5Connector + TopstepConnector
    → RiskManager completo (5 capas)
    → AuditLogger completo
    → Trade Intelligence
    → Símbolos ilimitados
    → Soporte Discord prioritario

    ENTERPRISE ($499/mes):
    → Todo lo anterior
    → Onboarding 1:1
    → SLA de soporte 24h
    → Acceso anticipado a nuevas features

[ ] Landing page (Webflow/Framer):
    → Hero: "Tu estrategia. Nuestra infraestructura."
    → Demo en video (30 segundos)
    → Ejemplo de código (30 líneas)
    → Tabla de precios
    → Testimonios (beta testers)
    → FAQ
    → CTA: "Empezar gratis"

[ ] Sistema de pagos:
    → Stripe integrado
    → Trial 14 días PRO gratis
    → Facturación automática mensual/anual
    → Portal de cliente (Stripe Portal)
```

---

## MES 11 — MARKETING TÉCNICO ⏳ PENDIENTE

```
[ ] Hilo en Twitter/X:
    "Por qué el 99% de los bots en MT5
     fallan al enviar órdenes
     (y cómo el retry con precio fresco
     lo soluciona)"
    → Thread técnico de 10 tweets
    → Al final: link a EdgeFramework
    → Sin revelar Alpha ni valores exactos

[ ] Post en Reddit:
    → r/algotrading
    → r/Python
    → "Construí un framework open-source
       de ejecución para MT5"
    → Código del ejemplo visible
    → GitHub link

[ ] GitHub público:
    → Solo la capa SaaS (sin Alpha)
    → Stars = validación social
    → Issues = feedback gratuito
    → README con ejemplo funcional

[ ] Estrategia "Mostrar, no contar":
    → Publicar logs reales (anonimizados)
    → Mostrar signals_audit.jsonl real
    → Demostrar que el AuditLogger funciona
    → NO publicar PnL ni estrategias
```

---

## MES 12 — ITERACIÓN Y ESCALA ⏳ PENDIENTE

```
[ ] Primeros 10-20 clientes:
    → Objetivo MRR: $1,000-2,000
    → ($99/mes × 10-20 clientes)

[ ] Análisis de churn:
    → ¿Quién cancela y por qué?
    → ¿Qué feature piden más?
    → Solo construir lo que piden 3+ clientes

[ ] Roadmap público:
    → Votar por features en Discord
    → Transparencia sobre qué viene

[ ] Decisión estratégica:
    → ¿Seguir como SaaS individual?
    → ¿Buscar co-fundador técnico?
    → ¿Levantar inversión pequeña?
    → ¿Mantener como negocio lifestyle?

[ ] Métricas objetivo Mes 12:
    MRR: $1,000-2,000
    Clientes activos: 10-20
    Churn mensual: < 10%
    NPS: > 8/10
    Tiempo soporte: < 2h/semana
```

---

# REGLAS DE ORO (no negociables en los 12 meses)

```
1. ALPHA NUNCA AL SAAS
   → strategies/, modulador, scoring → NUNCA expuestos
   → Revisión línea por línea antes de subir a GitHub
   → Si dudas → no lo subas

2. SOPORTE ASÍNCRONO
   → Discord tickets, no Telegram personal
   → SLA: respuesta en 24h (no en 2 minutos)
   → El SaaS no puede interrumpir tu operación

3. MVP SIEMPRE PRIMERO
   → Lanzar lo más simple que funcione
   → No añadir features hasta que las pidan
   → Un cliente con el MVP vale más que
     zero clientes con el producto perfecto

4. BOT PRIMERO, SAAS SEGUNDO
   → EdgeFix sigue operando y ganando
   → El SaaS no puede degradar el bot
   → Si hay conflicto → el bot gana
```

---

# MÉTRICAS OBJETIVO POR TRIMESTRE

```
T1 (Meses 1-3):
→ Framework funciona en producción
→ EdgeFix migrado sin degradación
→ PF EdgeFix ≥ 1.4 con framework

T2 (Meses 4-6):
→ Tutorial en < 20 minutos
→ 0 dependencias hardcodeadas
→ Documentación completa

T3 (Meses 7-9):
→ Docker funciona en 3 OS
→ 3-5 beta testers activos
→ 0 bugs críticos

T4 (Meses 10-12):
→ MRR: $1,000-2,000
→ 10-20 clientes activos
→ Churn < 10%
→ Tiempo soporte < 2h/semana
```

---

# INGRESOS PROYECTADOS

```
Fuente 1 — Prop Firms (ya activo):
→ EdgeFix + Bot5Multi
→ $3,000-6,000/mes (2-4 cuentas funded)
→ Crece con más cuentas

Fuente 2 — EdgeFramework SaaS (mes 10+):
→ $99/mes × 10 clientes = $990/mes
→ $99/mes × 20 clientes = $1,980/mes
→ $499/mes × 2 enterprise = $998/mes

Total proyectado Mes 12:
→ Prop Firms: $4,000-6,000/mes
→ SaaS: $1,000-3,000/mes
→ TOTAL: $5,000-9,000/mes
```

---

# STACK TECNOLÓGICO

```
FRAMEWORK:
→ Python 3.12
→ pandas, numpy, pyyaml
→ asyncio (futuro)

CONECTORES:
→ MetaTrader5 (MT5)
→ requests HTTP (Topstep)
→ paper (testing)

INFRAESTRUCTURA:
→ Docker (distribución)
→ GitHub (código)
→ GitBook (docs)
→ Stripe (pagos)
→ Discord (comunidad/soporte)
→ Webflow/Framer (landing)

MONITORING:
→ Telegram Bot (alertas)
→ JSONL logs (auditoría)
→ Trade Intelligence (análisis)
```

---

# RESUMEN EJECUTIVO

```
MES 1:  Base del framework ✅ HECHO HOY
MES 2:  MT5Connector + TopstepConnector
MES 3:  EdgeFix migrado al framework
MES 4:  Todo por YAML, CLI básico
MES 5:  Agnóstico de broker/símbolo
MES 6:  Docs + tutorial + 3 ejemplos
MES 7:  Docker — funciona en cualquier OS
MES 8:  Videos + landing page + Discord
MES 9:  Beta cerrada 3-5 usuarios
MES 10: Pricing + Stripe + landing final
MES 11: Marketing técnico + GitHub público
MES 12: 10-20 clientes, MRR $1K-2K

PARALELO (todo el año):
→ EdgeFix operando en FTMO
→ Bot5Multi en Topstep
→ Escalar cuentas funded
→ Ingresos prop firms: $3K-6K/mes
```

---

*EdgeFramework v0.1.0 — Junio 2026*
*"Tú traes tu estrategia. Nosotros el resto."*
