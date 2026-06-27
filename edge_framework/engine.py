"""
EdgeFramework — ExecutionEngine
Motor de ejecución algorítmica institucional.

Uso básico:
    from edge_framework import ExecutionEngine

    engine = ExecutionEngine(config="mi_config.yaml")
    engine.add_strategy(mi_estrategia)
    engine.start()
"""

from typing import Callable, Optional, Dict, Any
import yaml
import logging
from pathlib import Path

from edge_framework.connectors.instrument_mapper import InstrumentMapper

logger = logging.getLogger(__name__)


class StrategySignal:
    """
    Señal que devuelve una estrategia del cliente.
    El cliente NO necesita saber nada del framework
    para crear señales — solo rellenar este objeto.
    """
    def __init__(
        self,
        symbol: str,
        direction: str,          # "buy" | "sell" | "none"
        strategy_id: str,        # ID arbitrario del cliente
        confidence: float = 1.0, # 0.0 a 1.0
        sl_distance: Optional[float] = None,  # distancia SL en puntos
        tp_distance: Optional[float] = None,  # distancia TP en puntos
        metadata: Optional[Dict] = None       # datos extra del cliente
    ):
        self.symbol = symbol
        self.direction = direction
        self.strategy_id = strategy_id
        self.confidence = confidence
        self.sl_distance = sl_distance
        self.tp_distance = tp_distance
        self.metadata = metadata or {}

    def is_valid(self) -> bool:
        return (
            self.symbol
            and self.direction in ("buy", "sell")
            and 0.0 <= self.confidence <= 1.0
        )


class ExecutionEngine:
    """
    Motor principal de EdgeFramework.
    Gestiona la ejecución, riesgo y auditoría.
    El cliente solo añade estrategias y llama start().
    """

    def __init__(self, config: str = None, config_dict: Dict = None):
        """
        config: ruta al archivo YAML de configuración
        config_dict: dict de configuración directo (alternativo)
        """
        self._config = self._load_config(config, config_dict)
        self._strategies: list = []
        self._running = False
        self._connector = None
        self._risk_manager = None
        self._auditor = None
        self._instrument_mapper = InstrumentMapper(self._config)
        logger.info(f"EdgeFramework iniciado — modo: {self._config.get('framework', {}).get('mode', 'demo')}")

    def _load_config(self, config_path: str, config_dict: Dict) -> Dict:
        if config_dict:
            return config_dict
        if config_path:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
        # Config por defecto
        default = Path(__file__).parent / "config" / "default_config.yaml"
        if default.exists():
            with open(default, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def add_strategy(self, strategy_fn: Callable) -> "ExecutionEngine":
        """
        Añade una estrategia al motor.

        La estrategia debe ser una función o clase con método __call__
        que recibe (symbol, candles) y devuelve StrategySignal o None.

        Ejemplo:
            def mi_estrategia(symbol, candles):
                if candles['close'].iloc[-2] > candles['ema50'].iloc[-2]:
                    return StrategySignal(symbol, "buy", "mi_ema_cross", confidence=0.8)
                return None

            engine.add_strategy(mi_estrategia)
        """
        self._strategies.append(strategy_fn)
        logger.info(f"Estrategia añadida: {getattr(strategy_fn, '__name__', str(strategy_fn))}")
        return self  # permite chaining: engine.add_strategy(A).add_strategy(B)

    def set_connector(self, connector) -> "ExecutionEngine":
        """
        Conecta un broker/plataforma.
        connector debe implementar la interfaz BrokerConnector.
        """
        self._connector = connector
        return self

    def _build_connector_from_config(self):
        conn_type = self._config.get('connector', {}).get('type', 'paper')

        if conn_type == 'paper':
            from edge_framework.connectors.paper import PaperConnector
            return PaperConnector()

        elif conn_type == 'mt5':
            from edge_framework.connectors.mt5 import MT5Connector
            mt5_cfg = self._config.get('connector', {}).get('mt5', {})
            return MT5Connector(
                login=mt5_cfg.get('login'),
                password=mt5_cfg.get('password'),
                server=mt5_cfg.get('server'),
                path=mt5_cfg.get('terminal_path')
            )

        elif conn_type == 'topstep':
            from edge_framework.connectors.topstep import TopstepConnector
            ts_cfg = self._config.get('connector', {}).get('topstep', {})
            return TopstepConnector(
                username=ts_cfg.get('username'),
                api_key=ts_cfg.get('api_key'),
                account_id=ts_cfg.get('account_id')
            )

        else:
            from edge_framework.connectors.paper import PaperConnector
            logger.warning(f"Conector desconocido: {conn_type} — usando paper")
            return PaperConnector()

    def start_from_config(self):
        """
        Arranca el framework completamente desde el YAML.
        El cliente solo necesita:
            engine = ExecutionEngine(config='mi_config.yaml')
            engine.add_strategy(mi_estrategia)
            engine.start_from_config()
        """
        from edge_framework.risk import RiskManager
        from edge_framework.audit import AuditLogger

        if not self._connector:
            self._connector = self._build_connector_from_config()

        if not self._risk_manager:
            self._risk_manager = RiskManager(config=self._config)

        if not self._auditor:
            audit_cfg = self._config.get('audit', {})
            self._auditor = AuditLogger(
                log_path=audit_cfg.get('log_path', 'logs'),
                enabled=audit_cfg.get('enabled', True)
            )

        if not self._connector.connect():
            raise RuntimeError("No se pudo conectar al broker")

        account = self._connector.get_account()
        logger.info(
            f"Conectado: balance=${account.balance:,.2f} "
            f"modo={self._config.get('framework', {}).get('mode', 'live')}"
        )

        self.start()

    def start(self) -> None:
        """Arranca el motor en modo live."""
        if not self._strategies:
            raise ValueError("No hay estrategias añadidas. Usa engine.add_strategy()")
        self._running = True
        logger.info(f"Motor iniciado con {len(self._strategies)} estrategia(s)")
        # Loop principal — implementado en core/loop.py
        from edge_framework.core.loop import run_loop
        run_loop(self)

    def stop(self) -> None:
        """Para el motor limpiamente."""
        self._running = False
        logger.info("Motor detenido")

    @property
    def config(self) -> Dict:
        return self._config

    @property
    def strategies(self) -> list:
        return self._strategies

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def instrument_mapper(self):
        return self._instrument_mapper