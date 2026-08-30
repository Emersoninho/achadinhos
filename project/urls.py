# urls.py (principal)
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from products.sitemaps import (
    ProductSitemap, 
    CategorySitemap, 
    StaticSitemap,
    ProductImageSitemap
)
from blog.sitemaps import PostSitemap, PostCategorySitemap  # Adicione esta linha

# Configuração dos sitemaps
sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticSitemap,
    'product-images': ProductImageSitemap,
    'posts': PostSitemap,  # Adicione
    'post-categories': PostCategorySitemap,  # Adicione
}

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Apps
    path('', include('products.urls')),
    path('blog/', include('blog.urls')),
    
    # Sitemaps
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # Robots.txt
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', 
        content_type='text/plain'
    ), name='robots'),
]