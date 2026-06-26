"""
EdgeFramework — BrokerConnector
Interfaz abstracta para conectores de broker.

El framework NO sabe qué broker usas.
Solo sabe que el conector implementa esta interfaz.

Implementaciones disponibles:
- MT5Connector (MetaTrader 5)
- TopstepConnector (Topstep API)
- PaperConnector (paper trading sin broker)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class OrderDirection(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Candle:
    """Vela OHLCV estándar."""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class OrderRequest:
    """Solicitud de orden — agnóstica de broker."""
    symbol: str
    direction: OrderDirection
    volume: float
    sl_distance: Optional[float] = None  # distancia en puntos
    tp_distance: Optional[float] = None  # distancia en puntos
    comment: str = ""
    magic: int = 0


@dataclass
class OrderResult:
    """Resultado de una orden ejecutada."""
    success: bool
    ticket: Optional[int] = None
    fill_price: Optional[float] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class Position:
    """Posición abierta."""
    ticket: int
    symbol: str
    direction: OrderDirection
    volume: float
    open_price: float
    current_price: float
    profit: float
    sl: Optional[float] = None
    tp: Optional[float] = None


@dataclass
class AccountInfo:
    """Información de la cuenta."""
    balance: float
    equity: float
    margin_free: float
    currency: str = "USD"


class BrokerConnector(ABC):
    """
    Interfaz abstracta para conectores de broker.
    
    Implementa esta clase para conectar cualquier broker
    al EdgeFramework sin modificar el motor principal.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Conectar al broker. Devuelve True si éxito."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Desconectar limpiamente."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Verificar si la conexión está activa."""
        pass

    @abstractmethod
    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 500
    ) -> List[Candle]:
        """
        Obtener velas históricas.
        timeframe: "M1", "M5", "M15", "H1", "H4", "D1"
        """
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> Dict[str, float]:
        """
        Obtener precio actual.
        Devuelve: {"bid": X, "ask": X, "spread": X}
        """
        pass

    @abstractmethod
    def place_order(self, order: OrderRequest) -> OrderResult:
        """
        Coloca una orden de mercado.

        Args:
            order: OrderRequest con todos los parámetros
                   symbol, direction, volume, sl_distance,
                   tp_distance, comment, magic

        Returns:
            OrderResult con success, ticket, fill_price
        """
        pass

    @abstractmethod
    def close_position(self, ticket: int) -> bool:
        """Cerrar una posición por ticket."""
        pass

    @abstractmethod
    def get_positions(self, symbol: str = None) -> List[Position]:
        """
        Obtener posiciones abiertas.
        Si symbol=None devuelve todas.
        """
        pass

    @abstractmethod
    def get_account(self) -> AccountInfo:
        """Obtener información de la cuenta."""
        pass

    @abstractmethod
    def modify_sl(self, ticket: int, new_sl: float) -> bool:
        """Modificar el Stop Loss de una posición."""
        pass