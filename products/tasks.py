# products/tasks.py
from celery import shared_task
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_sitemap_cache():
    """Atualiza cache do sitemap periodicamente"""
    try:
        # Força atualização do cache
        cache.delete('sitemap_cache')
        
        # Nota: ping_google foi removido no Django 6.1
        # Para notificar o Google, use a API manualmente:
        # https://developers.google.com/search/apis/indexing-api/v3/quickstart
        
        logger.info("Cache do sitemap atualizado")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar sitemap: {str(e)}")
        return False


@shared_task
def generate_product_schema(product_id):
    """Gera e cacheia schema.org para produto"""
    from products.models import Product
    
    try:
        product = Product.objects.get(pk=product_id)
        schema_data = product.get_schema_data()
        
        # Cache por 1 hora
        cache.set(f'product_{product_id}_schema', schema_data, 3600)
        
        return True
    except Product.DoesNotExist:
        return False


@shared_task
def update_product_prices(product_ids=None):
    """Atualiza preços dos produtos (chamado pelo app sync)"""
    from products.models import Product
    
    if product_ids:
        products = Product.objects.filter(pk__in=product_ids)
    else:
        # Produtos em destaque são atualizados com mais frequência
        products = Product.objects.filter(featured=True)
    
    for product in products:
        # Aqui será integrado com o app affiliates/sync
        pass
    
    return len(products)