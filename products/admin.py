# products/admin.py
from datetime import timezone

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Min, Q
from .models import Category, Product
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
import requests
from bs4 import BeautifulSoup
from .scraper import ProductScraper


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'product_count', 'is_active', 'updated_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'parent', 'description', 'image')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'noindex', 'nofollow'),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('order', 'is_active', 'featured', 'schema_type')
        }),
        ('Métricas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.filter(status='active').count()
        return count
    product_count.short_description = 'Produtos Ativos'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _product_count=Count('products', filter=Q(products__status='active'))
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'thumbnail', 'name', 'category', 'current_price', 'original_price',
        'discount_badge', 'status', 'featured', 'view_count', 'updated_at'
    ]
    list_filter = [
        'status', 'featured', 'is_bestseller', 'category',
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'slug', 'description', 'brand', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'created_at', 'updated_at', 'view_count', 'click_count',
        'conversion_rate', 'price_updated_at'
    ]
    list_select_related = ['category']
    list_per_page = 50
    actions = ['make_active', 'make_draft', 'mark_featured', 'unmark_featured']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'name', 'slug', 'category', 'brand', 'sku',
                'short_description', 'description'
            )
        }),
        ('Mídia', {
            'fields': ('main_image', 'image_alt', 'gallery')
        }),
        ('Preços', {
            'fields': ('original_price', 'current_price', 'price_updated_at')
        }),
        ('Avaliações', {
            'fields': ('rating', 'review_count')
        }),
        ('Status', {
            'fields': (
                'status', 'featured', 'is_bestseller', 
                'published_at', 'related_products'
            )
        }),
        ('SEO', {
            'fields': (
                'meta_title', 'meta_description', 'keywords',
                'canonical_url', 'noindex', 'nofollow'
            ),
            'classes': ('wide',)
        }),
        ('Schema.org', {
            'fields': ('schema_type', 'gtin'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': (
                'view_count', 'click_count', 'conversion_rate',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.main_image
            )
        return "Sem imagem"
    thumbnail.short_description = 'Foto'
    
    def discount_badge(self, obj):
        discount = obj.get_discount_percentage()
        if discount > 0:
            color = 'red' if discount >= 30 else 'orange' if discount >= 15 else 'green'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-weight: bold;">-{}%</span>',
                color, int(discount)
            )
        return "-"
    discount_badge.short_description = 'Desconto'
    
    def make_active(self, request, queryset):
        updated = queryset.update(status='active', published_at=timezone.now())
        self.message_user(request, f'{updated} produto(s) ativado(s) com sucesso!')
    make_active.short_description = 'Ativar produtos selecionados'
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} produto(s) movido(s) para rascunho!')
    make_draft.short_description = 'Mover para rascunho'
    
    def mark_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} produto(s) marcado(s) como destaque!')
    mark_featured.short_description = 'Marcar como destaque'
    
    def unmark_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} produto(s) removido(s) dos destaques!')
    unmark_featured.short_description = 'Remover destaque'

    change_list_template = 'admin/products_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('importar/', self.admin_site.admin_view(import_product), name='import_product'),
        ]
        return custom_urls + urls


class ImportProductForm(forms.Form):
    url = forms.URLField(label="Link do Produto", widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'Cole o link do produto aqui...'
    }))
    platform = forms.ChoiceField(choices=[
        ('amazon', 'Amazon'),
        ('mercado_livre', 'Mercado Livre'),
        ('shopee', 'Shopee'),
    ], widget=forms.Select(attrs={'class': 'form-control'}))


def import_product(request):
    if request.method == 'POST':
        form = ImportProductForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            platform = form.cleaned_data['platform']
            
            # Scraping dos dados
            scraper = ProductScraper(url, platform)
            data = scraper.scrape()
            
            if 'error' in data:
                messages.error(request, f"Erro ao importar: {data['error']}")
            else:
                # Mostra os dados extraídos
                if data:
                    messages.success(request, "Dados extraídos:")
                    for key, value in data.items():
                        messages.info(request, f"{key}: {value}")
                else:
                    messages.warning(request, "Nenhum dado encontrado. O site pode ter bloqueado o scraping.")
                
            return redirect('admin:products_product_changelist')
    else:
        form = ImportProductForm()
    
    context = {
        'form': form,
        'title': 'Importar Produto',
    }
    return render(request, 'admin/import_product.html', context)   