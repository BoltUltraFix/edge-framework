# EdgeFramework — Configurar Stripe

## Paso 1 — Crear cuenta Stripe
1. Ir a stripe.com
2. Crear cuenta con tu email
3. Completar datos de negocio

## Paso 2 — Crear productos
En Stripe Dashboard → Products → Add product:

PRODUCTO 1:
- Nombre: EdgeFramework PRO Monthly
- Precio: $99.00 / mes (recurring)
- Currency: USD

PRODUCTO 2:
- Nombre: EdgeFramework PRO Yearly
- Precio: $890.00 / año (recurring)
- Currency: USD

## Paso 3 — Obtener API keys
Settings → API keys:
- Publishable key: pk_live_...
- Secret key: sk_live_... (NUNCA compartir)

## Paso 4 — Configurar webhook
Developers → Webhooks → Add endpoint:
- URL: https://tu-dominio.com/webhook/stripe
- Eventos: customer.subscription.created,
           customer.subscription.deleted,
           invoice.payment_succeeded

## Paso 5 — Añadir al .env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...

## Paso 6 — Flujo de pago
Landing page → Botón PRO →
Stripe Checkout → Pago exitoso →
Webhook → Generar API key →
Email al usuario con API key →
Usuario añade a config.yaml

## Revenue estimado
5 clientes PRO:   $495/mes
10 clientes PRO:  $990/mes
20 clientes PRO:  $1,980/mes  ← objetivo Mes 12