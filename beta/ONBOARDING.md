# EdgeFramework Beta — Guía de Onboarding
## Bienvenido al programa de beta cerrada

Gracias por unirte a la beta de EdgeFramework.
Eres uno de los 5 traders seleccionados para
probar el framework antes del lanzamiento público.

Tu feedback directo va a moldear el producto final.

---

## Lo que vas a probar

EdgeFramework es la infraestructura que conecta
tu estrategia a cualquier broker (FTMO, Topstep)
sin reescribir código.

Durante la beta vas a:
1. Instalar el framework en tu PC
2. Conectar tu cuenta FTMO o Topstep
3. Correr tu primera estrategia en Shadow Mode
4. Darnos feedback semanal

---

## Instalación (10 minutos)

### Requisitos
- Python 3.10 o superior
- MetaTrader 5 instalado (si usas FTMO)
- Cuenta activa en FTMO o Topstep

### Paso 1 — Descargar
Recibirás un enlace privado de descarga.
Descomprime en tu escritorio.

### Paso 2 — Instalar dependencias
Abre PowerShell en la carpeta y ejecuta:
pip install -r requirements.txt

### Paso 3 — Configurar tu broker
Abre config.yaml y edita:

Para FTMO (MT5):
connector:
  type: "mt5"
  mt5:
    login: TU_LOGIN
    password: "TU_PASSWORD"
    server: "FTMO-Demo"
    terminal_path: "C:\\...\\terminal64.exe"

Para Topstep:
connector:
  type: "topstep"
  topstep:
    username: "TU_EMAIL"
    api_key: "TU_API_KEY"
    account_id: "TU_ACCOUNT_ID"

### Paso 4 — Arrancar en Shadow Mode
Primero prueba sin riesgo real:

En config.yaml:
connector:
  type: "shadow_edgefix"

Luego ejecuta:
python mi_estrategia.py

Verás en pantalla:
  SHADOW MODE | Ciclo 1 | 10:30:00
  Balance: $25,000.00
  Posiciones: 0 abiertas

### Paso 5 — Tu primera estrategia
Copia uno de los ejemplos incluidos:
- examples/rsi_strategy/
- examples/breakout_strategy/
- examples/simple_ema_strategy/

Edita el config.yaml del ejemplo
con tus credenciales y ejecuta.

---

## Durante la beta (4 semanas)

### Semana 1: Instalación y Shadow Mode
Objetivo: Framework corriendo en tu PC
Reportar: ¿Algún error de instalación?
          ¿El Shadow Mode conecta bien?

### Semana 2: Primera estrategia real
Objetivo: Un trade real ejecutado
Reportar: ¿Funcionó la ejecución?
          ¿El riesgo se calculó bien?

### Semana 3: Prueba de estrés
Objetivo: Correr durante 5 días seguidos
Reportar: ¿Se cayó alguna vez?
          ¿Qué mejorarías?

### Semana 4: Feedback final
Objetivo: Formulario completo de feedback
Reportar: ¿Lo usarías en producción?
          ¿Cuánto pagarías por ello?

---

## Cómo reportar problemas

1. Copia el error completo de la consola
2. Indica qué broker usas (FTMO/Topstep)
3. Indica qué ejemplo estabas probando
4. Envía por Discord al canal #beta-soporte

Respondo en menos de 24 horas.

---

## Contacto directo

Discord: [tu usuario]
Email: [tu email]
Canal beta: #beta-privado en Discord

---

## Lo que obtienes por participar

- Acceso gratuito al PRO durante 3 meses
  cuando lancemos ($99/mes de valor)
- Tu nombre en los créditos del producto
- Influencia directa en el roadmap

Gracias por confiar en el proyecto.
Nos vemos en Discord.

---
EdgeFramework Beta v0.2.0 — Junio 2026