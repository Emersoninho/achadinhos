from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

class SyncResult(NamedTuple):
    price: Optional[float]
    original_price: Optional[float]
    in_stock: bool
    error: str = ""

class BasePlatformSync(ABC):
    @abstractmethod
    def fetch_price_and_stock(self, external_id: str) -> SyncResult:
        """Busca o preço atualizado e status de estoque da plataforma."""
        pass