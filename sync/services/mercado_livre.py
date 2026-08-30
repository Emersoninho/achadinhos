import requests
from sync.services.base import BasePlatformSync, SyncResult


class MercadoLivreSyncService(BasePlatformSync):
    """
    Integrador para a API pública do Mercado Livre.
    Endpoint: https://api.mercadolibre.com/items/{item_id}
    """

    def fetch_price_and_stock(self, external_id: str) -> SyncResult:
        # Garante o formato padrão com prefixo MLB (ex: MLB12345678)
        ext_id = external_id.strip().upper()
        if not ext_id.startswith("MLB"):
            ext_id = f"MLB{ext_id}"

        url = f"https://api.mercadolibre.com/items/{ext_id}"
        headers = {"User-Agent": "AchadinhosApp/1.0"}

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 404:
                return SyncResult(
                    price=None,
                    original_price=None,
                    in_stock=False,
                    error="Anúncio não encontrado (404)",
                )

            if response.status_code != 200:
                return SyncResult(
                    price=None,
                    original_price=None,
                    in_stock=False,
                    error=f"HTTP {response.status_code}",
                )

            data = response.json()

            # Extração de preço e desconto
            price = data.get("price")
            original_price = data.get("original_price") or price

            # Checagem de disponibilidade e status do anúncio
            status = data.get("status")
            available_qty = data.get("available_quantity", 0)
            in_stock = bool(status == "active" and available_qty > 0)

            return SyncResult(
                price=price,
                original_price=original_price,
                in_stock=in_stock,
                error="",
            )

        except requests.RequestException as exc:
            return SyncResult(
                price=None,
                original_price=None,
                in_stock=False,
                error=str(exc)[:255],
            )