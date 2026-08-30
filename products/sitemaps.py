# products/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from .models import Product, Category


class ProductSitemap(Sitemap):
    """Sitemap para produtos - atualizado dinamicamente"""
    changefreq = "hourly"
    priority = 0.8
    protocol = "https"
    limit = 1000
    
    def items(self):
        return Product.objects.filter(
            Q(status='active') | Q(status='out_of_stock')
        ).select_related('category').order_by(
            '-featured',
            '-updated_at',
            '-view_count',
        )
    
    def location(self, obj):
        return obj.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def priority(self, obj):
        priority = 0.5
        
        if obj.featured:
            priority += 0.2
        
        if obj.get_discount_percentage() > 30:
            priority += 0.2
        
        if obj.view_count > 1000:
            priority += 0.1
        
        if obj.created_at >= timezone.now() - timezone.timedelta(days=7):
            priority += 0.1
        
        return min(priority, 1.0)
    
    def changefreq(self, obj):
        if obj.featured:
            return "hourly"
        elif obj.get_discount_percentage() > 0:
            return "daily"
        else:
            return "weekly"


class CategorySitemap(Sitemap):
    """Sitemap para categorias"""
    changefreq = "daily"
    priority = 0.9
    protocol = "https"
    
    def items(self):
        return Category.objects.filter(is_active=True)
    
    def location(self, obj):
        return obj.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def priority(self, obj):
        if obj.parent is None:
            return 0.9
        else:
            return 0.7


class StaticSitemap(Sitemap):
    """Sitemap para páginas estáticas"""
    priority = 1.0
    changefreq = "daily"
    protocol = "https"
    
    def items(self):
        return [
            'products:list',
            'products:price_drops',
            'blog:list',
        ]
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, item):
        return timezone.now()


class ProductImageSitemap(Sitemap):
    """Sitemap específico para imagens (Google Images SEO)"""
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"
    
    def items(self):
        return Product.objects.filter(
            status='active',
            main_image__isnull=False
        ).exclude(main_image='')
    
    def location(self, obj):
        return obj.get_absolute_url()
    
    def images(self, obj):
        images = []
        
        if obj.main_image:
            images.append({
                'loc': obj.main_image,
                'title': obj.image_alt or obj.name,
                'caption': obj.short_description or obj.name,
            })
        
        if obj.gallery:
            for img_url in obj.gallery[:5]:
                images.append({
                    'loc': img_url,
                    'title': f"{obj.name} - Imagem adicional",
                })
        
        return images