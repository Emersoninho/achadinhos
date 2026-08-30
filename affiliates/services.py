import requests
import logging

logger = logging.getLogger(__name__)

def fetch_mercadolivre_item(external_id: str) -> dict:
    """
    Busca detalhes de um produto no Mercado Livre pelo MLB ID (ex: MLB123456789).
    Retorna um dicionário com os dados processados ou lança uma exceção em caso de erro.
    """
    # Garante o formato correto do ID (ex: MLB12345678)
    formatted_id = external_id.strip().upper()
    if not formatted_id.startswith("MLB"):
        formatted_id = f"MLB{formatted_id}"

    url = f"https://api.mercadolibre.com/items/{formatted_id}"
    headers = {"User-Agent": "AchadinhosApp/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extrai preço atual, preço original (se houver desconto) e estoque
        current_price = data.get("price")
        original_price = data.get("original_price") or current_price
        available_quantity = data.get("available_quantity", 0)
        status = data.get("status")

        return {
            "current_price": current_price,
            "original_price": original_price,
            "in_stock": status == "active" and available_quantity > 0,
            "error": None
        }

    except requests.RequestException as exc:
        logger.error(f"Erro ao consultar Mercado Livre ({formatted_id}): {exc}")
        return {
            "current_price": None,
            "original_price": None,
            "in_stock": False,
            "error": f"Erro de API: {str(exc)}"
        }