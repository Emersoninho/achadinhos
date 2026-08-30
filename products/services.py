# products/services.py
from django.db.models import F, Q, Avg, Count
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category


class ProductService:
    """Serviço para lógica de negócios dos produtos"""
    
    @staticmethod
    def get_featured_products(limit=12):
        """Produtos em destaque com cache"""
        cache_key = f'featured_products_{limit}'
        products = cache.get(cache_key)
        
        if products is None:
            products = list(Product.objects.filter(
                status='active',
                featured=True
            ).select_related('category')[:limit])
            cache.set(cache_key, products, 300)  # 5 minutos
        
        return products
    
    @staticmethod
    def get_best_discounts(limit=12, min_discount=30):
        """Produtos com melhores descontos"""
        cache_key = f'best_discounts_{limit}_{min_discount}'
        products = cache.get(cache_key)
        
        if products is None:
            products = list(Product.objects.filter(
                status='active',
                original_price__isnull=False,
                current_price__isnull=False,
                current_price__lt=F('original_price')
            ).annotate(
                discount=((F('original_price') - F('current_price')) / F('original_price') * 100)
            ).filter(
                discount__gte=min_discount
            ).order_by('-discount')[:limit])
            cache.set(cache_key, products, 600)  # 10 minutos
        
        return products
    
    @staticmethod
    def get_popular_products(limit=12, days=7):
        """Produtos mais visualizados"""
        cache_key = f'popular_products_{limit}'
        products = cache.get(cache_key)
        
        if products is None:
            products = list(Product.objects.filter(
                status='active',
                created_at__gte=timezone.now() - timedelta(days=days)
            ).select_related('category').order_by('-view_count')[:limit])
            cache.set(cache_key, products, 1800)  # 30 minutos
        
        return products
    
    @staticmethod
    def get_related_products(product, limit=6):
        """Produtos relacionados por categoria"""
        if not product.category:
            return []
        
        cache_key = f'related_products_{product.pk}_{limit}'
        related = cache.get(cache_key)
        
        if related is None:
            related = list(Product.objects.filter(
                category=product.category,
                status='active'
            ).exclude(pk=product.pk)[:limit])
            cache.set(cache_key, related, 3600)  # 1 hora
        
        return related


class CategoryService:
    """Serviço para categorias"""
    
    @staticmethod
    def get_menu_categories():
        """Categorias para o menu principal"""
        cache_key = 'menu_categories'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(Category.objects.filter(
                is_active=True,
                parent__isnull=True
            ).prefetch_related('subcategories'))
            cache.set(cache_key, categories, 3600)
        
        return categories
    
    @staticmethod
    def get_breadcrumb(category):
        """Gera breadcrumb para navegação"""
        breadcrumb = []
        current = category
        
        while current:
            breadcrumb.append({
                'name': current.name,
                'url': current.get_absolute_url()
            })
            current = current.parent
        
        breadcrumb.reverse()
        return breadcrumb