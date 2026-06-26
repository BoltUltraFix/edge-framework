"""
EdgeFramework — Stripe Integration
Gestión de suscripciones y licencias.

Flujo:
1. Usuario visita landing page
2. Elige plan PRO
3. Paga via Stripe
4. Recibe API key de licencia
5. Introduce API key en config.yaml
6. Framework valida licencia online
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Planes disponibles
PLANS = {
    'free': {
        'name': 'FREE',
        'price_monthly': 0,
        'price_yearly': 0,
        'max_brokers': 1,
        'max_strategies': 3,
        'shadow_mode': False,
        'api_status': False,
        'priority_support': False,
    },
    'pro': {
        'name': 'PRO',
        'price_monthly': 99,
        'price_yearly': 890,
        'max_brokers': 10,
        'max_strategies': 10,
        'shadow_mode': True,
        'api_status': True,
        'priority_support': True,
    },
    'enterprise': {
        'name': 'ENTERPRISE',
        'price_monthly': 0,  # precio a consultar
        'price_yearly': 0,
        'max_brokers': -1,   # ilimitado
        'max_strategies': -1,
        'shadow_mode': True,
        'api_status': True,
        'priority_support': True,
    }
}


class LicenseManager:
    """
    Gestiona licencias de EdgeFramework.
    La licencia se almacena en config.yaml:
        license:
          api_key: "EF-XXXX-XXXX-XXXX"
          plan: "pro"
    """

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._license_cfg = self._config.get('license', {})
        self._api_key = self._license_cfg.get('api_key', '')
        self._plan = self._license_cfg.get('plan', 'free')
        self._cached_plan = None
        self._cache_until = None

    @property
    def plan(self) -> str:
        return self._plan

    @property
    def plan_config(self) -> dict:
        return PLANS.get(self._plan, PLANS['free'])

    def is_feature_allowed(self, feature: str) -> bool:
        plan_cfg = self.plan_config
        allowed = plan_cfg.get(feature, False)
        if not allowed:
            logger.warning(
                f"[License] Feature '{feature}' no disponible en plan {self._plan}. "
                f"Actualiza a PRO en edgeframework.io/pricing"
            )
        return allowed

    def validate_local(self) -> bool:
        if not self._api_key:
            logger.info("[License] Sin API key — plan FREE activo")
            self._plan = 'free'
            return True
        if self._api_key.startswith('EF-') and len(self._api_key) > 10:
            logger.info(f"[License] API key válida — plan {self._plan}")
            return True
        logger.warning("[License] API key inválida — usando plan FREE")
        self._plan = 'free'
        return False

    def get_limits(self) -> dict:
        return {
            'plan': self._plan,
            'max_brokers': self.plan_config['max_brokers'],
            'max_strategies': self.plan_config['max_strategies'],
            'shadow_mode': self.plan_config['shadow_mode'],
            'api_status': self.plan_config['api_status'],
        }

    def __repr__(self):
        return f"LicenseManager(plan={self._plan}, key={self._api_key[:8]}...)"