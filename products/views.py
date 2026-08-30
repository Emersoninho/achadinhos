# products/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Prefetch, Q, F, Count
from django.core.cache import cache
from django.utils import timezone
from .models import Category, Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from django.contrib import messages
from products.admin import ImportProductForm  # Importa o form do admin


class ProductListView(ListView):
    """Lista de produtos com filtros e ordenação"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            status='active'
        ).select_related('category').prefetch_related('links')
        
        # Busca por termo
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(short_description__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        # Filtro por categoria
        category_slug = self.kwargs.get('slug') or self.request.GET.get('categoria')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            categories = [category] + list(category.subcategories.filter(is_active=True))
            queryset = queryset.filter(category__in=categories)
        
        # Filtro por desconto
        if self.request.GET.get('desconto'):
            min_discount = int(self.request.GET.get('desconto'))
            
            queryset = queryset.filter(
                original_price__isnull=False,
                current_price__isnull=False,
                current_price__lt=F('original_price')
            ).annotate(
                discount=(F('original_price') - F('current_price')) / F('original_price') * 100
            ).filter(
                discount__gte=min_discount
            )
        
        # Ordenação
        sort = self.request.GET.get('ordenar', '-created_at')
        sort_options = {
            '-created_at': '-created_at',
            'price_asc': 'current_price',
            'price_desc': '-current_price',
            'popular': '-view_count',
            'discount': '-discount',
        }
        # Se for ordenar por desconto, precisa anotar
        if sort == 'discount':
            queryset = queryset.annotate(
                discount=(F('original_price') - F('current_price')) / F('original_price') * 100
            ).order_by('-discount')
        else:
            queryset = queryset.order_by(sort_options.get(sort, '-created_at'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categorias para o menu/filtro
        cache_key = 'product_categories_menu'
        categories = cache.get(cache_key)
        if not categories:
            categories = Category.objects.filter(
                is_active=True, parent__isnull=True
            ).prefetch_related('subcategories')
            cache.set(cache_key, categories, 3600)
        
        context['categories'] = categories
        context['current_category'] = self.kwargs.get('slug')
        context['search_query'] = self.request.GET.get('q', '')

        # Banner - Top 3 produtos com maior desconto
        context['banner_products'] = Product.objects.filter(
            status='active',
            original_price__isnull=False,
            current_price__isnull=False,
            current_price__lt=F('original_price')
        ).annotate(
            discount=(F('original_price') - F('current_price')) / F('original_price') * 100
        ).order_by('-discount')[:3]
        
        # SEO
        if context['search_query']:
            context['meta_title'] = f'Busca: {context["search_query"]} | Achadinhos'
            context['meta_description'] = f'Resultados da busca por {context["search_query"]}. Encontre as melhores ofertas e descontos.'
        else:
            context['meta_title'] = 'Achadinhos | Melhores Ofertas e Descontos'
            context['meta_description'] = 'Descubra os melhores achadinhos com descontos imperdíveis na Amazon, Mercado Livre e Shopee. Atualizado diariamente!'
        
        return context


class ProductDetailView(DetailView):
    """Detalhe do produto otimizado para SEO"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(
            Q(status='active') | Q(status='out_of_stock')
        ).select_related('category')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.track_view()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        if product.category:
            related = Product.objects.filter(
                category=product.category,
                status='active'
            ).exclude(pk=product.pk)[:6]
            context['related_products'] = related
        
        context['best_link'] = product.best_link()
        context['schema_data'] = product.get_schema_data()
        
        context['meta_title'] = product.meta_title or f'{product.name} - Melhor Preço'
        context['meta_description'] = product.meta_description or product.short_description
        context['canonical_url'] = product.canonical_url or product.get_absolute_url()
        
        return context


class CategoryDetailView(ListView):
    """Página de categoria com SEO"""
    model = Product
    template_name = 'products/category_detail.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        self.category = get_object_or_404(
            Category, 
            slug=self.kwargs.get('slug'),
            is_active=True
        )
        
        categories = [self.category] + list(
            self.category.subcategories.filter(is_active=True)
        )
        
        return Product.objects.filter(
            category__in=categories,
            status='active'
        ).select_related('category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['subcategories'] = self.category.subcategories.filter(is_active=True)
        
        context['meta_title'] = self.category.meta_title or f'{self.category.name} - Achadinhos'
        context['meta_description'] = self.category.meta_description or f'Melhores ofertas em {self.category.name}. Descontos imperdíveis!'
        
        return context


class PriceDropListView(ListView):
    """Produtos com queda de preço"""
    model = Product
    template_name = 'products/price_drop_list.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        return Product.objects.filter(
            status='active',
            original_price__isnull=False,
            current_price__isnull=False,
            current_price__lt=F('original_price')
        ).select_related('category').annotate(
            discount=(F('original_price') - F('current_price')) / F('original_price') * 100
        ).order_by('-discount')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = 'Quedas de Preço | Achadinhos'
        context['meta_description'] = 'Produtos com queda de preço em tempo real. Aproveite os melhores descontos!'
        return context


class ImportProductView(LoginRequiredMixin, FormView):
    template_name = 'products/import_product.html'
    form_class = ImportProductForm
    success_url = '/admin/'
    
    def form_valid(self, form):
        url = form.cleaned_data['url']
        platform = form.cleaned_data['platform']
        # Lógica de importação aqui
        messages.success(self.request, 'Produto importado com sucesso!')
        return super().form_valid(form)