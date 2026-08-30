# products/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.db.models import F, Q
from django.utils import timezone
from django.conf import settings
from .models import Product, Category
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    """Executado antes de salvar o produto"""
    
    if instance.pk:
        try:
            old_product = Product.objects.get(pk=instance.pk)
            
            if old_product.current_price != instance.current_price:
                if instance.current_price and old_product.current_price:
                    variation = ((instance.current_price - old_product.current_price) / old_product.current_price) * 100
                    
                    if variation <= -20:
                        logger.info(f"Queda de preço detectada: {instance.name} - {variation:.1f}%")
            
            if old_product.status != instance.status:
                if instance.status == 'active' and not instance.published_at:
                    instance.published_at = timezone.now()
                    logger.info(f"Produto publicado: {instance.name}")
        
        except Product.DoesNotExist:
            pass
    else:
        if instance.status == 'active':
            instance.published_at = timezone.now()
    
    if not instance.meta_title:
        instance.meta_title = f"{instance.name} | Melhor Preço e Ofertas"
    
    if not instance.meta_description:
        if instance.short_description:
            instance.meta_description = instance.short_description[:160]
        elif instance.description:
            import re
            clean_text = re.sub(r'<[^>]+>', '', instance.description)
            instance.meta_description = clean_text[:160]
    
    if not instance.image_alt:
        instance.image_alt = f"{instance.name} - melhor preço e oferta"


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    """Executado após salvar o produto"""
    
    # Limpa cache simples (funciona com LocMemCache)
    cache.delete('featured_products_12')
    cache.delete('best_discounts_12_30')
    cache.delete('popular_products_12')
    cache.delete(f'product_{instance.pk}_schema')
    
    if instance.category:
        cache.delete(f'category_products_{instance.category.pk}')
    
    cache.delete('sitemap_cache')
    
    if created:
        logger.info(f"Novo produto criado: {instance.name}")
    else:
        logger.debug(f"Produto atualizado: {instance.name}")


@receiver(post_save, sender=Category)
def category_post_save(sender, instance, created, **kwargs):
    """Executado após salvar categoria"""
    
    cache.delete('menu_categories')
    cache.delete('product_categories_menu')
    cache.delete('sitemap_cache')
    
    if created:
        logger.info(f"Nova categoria criada: {instance.name}")


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    """Executado após deletar produto"""
    
    cache.delete('featured_products_12')
    cache.delete('best_discounts_12_30')
    cache.delete('popular_products_12')
    
    logger.warning(f"Produto deletado: {instance.name}")


@receiver(post_delete, sender=Category)
def category_post_delete(sender, instance, **kwargs):
    """Executado após deletar categoria"""
    
    cache.delete('menu_categories')
    
    logger.warning(f"Categoria deletada: {instance.name}")