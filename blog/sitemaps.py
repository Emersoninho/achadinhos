# blog/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from blog.models import Post, PostCategory


class PostSitemap(Sitemap):
    """Sitemap para posts do blog"""
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"
    limit = 1000
    
    def items(self):
        return Post.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('category', 'author')
    
    def location(self, obj):
        return obj.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def priority(self, obj):
        """Posts recentes ou reviews têm maior prioridade"""
        priority = 0.5
        
        # Reviews e comparações são mais importantes para SEO
        if obj.post_type in ['review', 'comparison']:
            priority += 0.2
        
        # Posts com produtos mencionados são mais valiosos
        if obj.productmention_set.exists():
            priority += 0.1
        
        # Posts recentes (últimos 30 dias)
        if obj.published_at and obj.published_at >= timezone.now() - timezone.timedelta(days=30):
            priority += 0.1
        
        return min(priority, 1.0)


class PostCategorySitemap(Sitemap):
    """Sitemap para categorias do blog"""
    changefreq = "daily"
    priority = 0.6
    protocol = "https"
    
    def items(self):
        return PostCategory.objects.all()
    
    def location(self, obj):
        from django.urls import reverse
        return reverse('blog:category', kwargs={'slug': obj.slug})