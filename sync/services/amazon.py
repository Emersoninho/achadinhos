import requests
from bs4 import BeautifulSoup
from sync.services.base import BasePlatformSync, SyncResult

class AmazonSyncService(BasePlatformSync):
    def fetch_price_and_stock(self, external_id: str) -> SyncResult:
        """
        Scraping básico com BeautifulSoup (Exemplo) ou chamada à PA-API 5.0.
        `external_id` na Amazon costuma ser o ASIN (ex: B08N5WRWNW).
        """
        asin = external_id.strip()
        url = f"https://www.amazon.com.br/dp/{asin}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code != 200:
                return SyncResult(price=None, original_price=None, in_stock=False, error=f"Amazon HTTP {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")

            # Verifica disponibilidade
            availability = soup.find("id", "availability")
            in_stock = True
            if availability and "não disponível" in availability.text.lower():
                in_stock = False

            # Tenta extrair preço no formato padrão Amazon (.a-price-whole e .a-price-fraction)
            price_elem = soup.find("span", {"class": "a-offscreen"})
            if not price_elem:
                return SyncResult(price=None, original_price=None, in_stock=in_stock, error="Preço não localizado")

            raw_price = price_elem.text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            price = float(raw_price)

            return SyncResult(price=price, original_price=price, in_stock=in_stock)

        except Exception as exc:
            return SyncResult(price=None, original_price=None, in_stock=False, error=str(exc)[:255])