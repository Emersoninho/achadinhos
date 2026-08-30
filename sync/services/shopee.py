import requests
import hashlib
import time
from django.conf import settings
from sync.services.base import BasePlatformSync, SyncResult

class ShopeeSyncService(BasePlatformSync):
    def fetch_price_and_stock(self, external_id: str) -> SyncResult:
        """
        Exemplo utilizando a API de Afiliados / OpenAPI da Shopee (GraphQL / REST)
        ou endpoint público de item.
        """
        try:
            # Exemplo via endpoint REST da Shopee (Substitua pela sua lógica/chaves API)
            url = f"https://shopee.com.br/api/v4/item/get?itemid={external_id}&shopid={external_id}" 
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return SyncResult(price=None, original_price=None, in_stock=False, error=f"HTTP {response.status_code}")

            data = response.json().get("data", {})
            if not data:
                return SyncResult(price=None, original_price=None, in_stock=False, error="Produto não encontrado")

            # A Shopee entrega os preços em centavos (divide por 100.000)
            raw_price = data.get("price", 0) / 100000.0
            raw_original_price = (data.get("price_before_discount") or data.get("price")) / 100000.0
            stock = data.get("stock", 0)

            return SyncResult(
                price=raw_price,
                original_price=raw_original_price,
                in_stock=bool(stock > 0 and data.get("item_status") == "NORMAL"),
            )
        except Exception as exc:
            return SyncResult(price=None, original_price=None, in_stock=False, error=str(exc)[:255])