from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import json
from affiliates.models import AffiliateLink 

class Category(models.Model):
    """Categoria hierárquica otimizada para SEO"""
    
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(unique=True, max_length=120, blank=True, db_index=True)
    parent = models.ForeignKey(
        "self", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name="subcategories",
        verbose_name="Categoria Pai"
    )
    description = models.TextField(blank=True, help_text="Descrição única para a página da categoria")
    image = models.ImageField(upload_to="categories/%Y/%m/", blank=True, null=True)
    
    # SEO Avançado
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(blank=True, help_text="URL canônica se diferente da atual")
    noindex = models.BooleanField(default=False, help_text="Marque para não indexar")
    nofollow = models.BooleanField(default=False, help_text="Marque para não seguir links")
    
    # Ordenação e Status
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False, help_text="Exibir na página inicial")
    
    # Analytics e Schema
    schema_type = models.CharField(
        max_length=50, 
        default="CollectionPage",
        choices=[
            ("CollectionPage", "Collection Page"),
            ("ItemList", "Item List"),
            ("FAQPage", "FAQ Page"),
        ]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["slug", "is_active"]),
            models.Index(fields=["parent", "order"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:category_detail", kwargs={"slug": self.slug})

    def get_full_path(self):
        """Retorna o caminho completo da categoria"""
        path = [self]
        parent = self.parent
        while parent:
            path.append(parent)
            parent = parent.parent
        return "/".join([cat.slug for cat in reversed(path)])

    def get_schema_data(self):
        """Gera dados estruturados para a categoria"""
        return {
            "@context": "https://schema.org",
            "@type": self.schema_type,
            "name": self.name,
            "description": self.meta_description or self.description,
            "url": self.get_absolute_url(),
            "numberOfItems": self.products.filter(active=True).count()
        }

    def __str__(self):
        return self.get_full_path() if self.parent else self.name


class Product(models.Model):
    """Produto canônico com foco em SEO e performance"""
    
    # Status Choices
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', 'Rascunho'
        ACTIVE = 'active', 'Ativo'
        OUT_OF_STOCK = 'out_of_stock', 'Esgotado'
        DISCONTINUED = 'discontinued', 'Descontinuado'
        PRICE_DROP = 'price_drop', 'Queda de Preço'
    
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True, max_length=280, blank=True, db_index=True)
    short_description = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Descrição curta para cards e meta description"
    )
    description = models.TextField(
        blank=True, 
        help_text="Conteúdo ORIGINAL - mínimo 300 palavras para SEO"
    )
    
    # Relacionamentos
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="products",
        verbose_name="Categoria"
    )
    related_products = models.ManyToManyField(
        'self', 
        blank=True,
        symmetrical=False,
        help_text="Produtos relacionados manualmente"
    )
    
    # Mídia
    main_image = models.URLField(max_length=500, blank=True)
    image_alt = models.CharField(max_length=200, blank=True, help_text="Alt text para SEO")
    gallery = models.JSONField(default=list, blank=True, help_text="Lista de URLs de imagens")
    
    # Status e Flags
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.ACTIVE,
        db_index=True
    )
    featured = models.BooleanField(default=False, db_index=True, help_text="Sincroniza preço a cada 1h")
    is_bestseller = models.BooleanField(default=False, help_text="Marcar como mais vendido")
    
    # Preços e Avaliações
    original_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    current_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    price_updated_at = models.DateTimeField(null=True, blank=True)
    
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))]
    )
    review_count = models.PositiveIntegerField(default=0)
    
    # SEO Avançado
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    keywords = models.CharField(max_length=255, blank=True, help_text="Separadas por vírgula")
    canonical_url = models.URLField(blank=True)
    noindex = models.BooleanField(default=False)
    nofollow = models.BooleanField(default=False)
    
    # Schema.org
    schema_type = models.CharField(
        max_length=50,
        default="Product",
        choices=[
            ("Product", "Product"),
            ("ProductGroup", "Product Group"),
        ]
    )
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True)
    gtin = models.CharField(max_length=14, blank=True, help_text="EAN/UPC para schema.org")
    
    # Performance e Cache
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0'),
        help_text="Taxa de conversão em %"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug", "status"]),
            models.Index(fields=["category", "status", "-created_at"]),
            models.Index(fields=["featured", "status"]),
            models.Index(fields=["current_price", "status"]),
            models.Index(fields=["view_count"]),
            models.Index(fields=["-updated_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(current_price__isnull=True) | models.Q(current_price__gte=0),
                name="current_price_non_negative"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:250]
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Gera meta description automaticamente se vazia
        if not self.meta_description and self.short_description:
            self.meta_description = self.short_description[:160]
        elif not self.meta_description and self.description:
            self.meta_description = self.description[:160]
        
        # Gera meta title automaticamente se vazio
        if not self.meta_title:
            self.meta_title = f"{self.name} | Melhor Preço e Ofertas"
        
        # Gera alt text se vazio
        if not self.image_alt:
            self.image_alt = f"{self.name} - melhor preço e oferta"
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    def get_discount_percentage(self):
        """Calcula percentual de desconto"""
        if self.original_price and self.current_price and self.original_price > 0:
            discount = ((self.original_price - self.current_price) / self.original_price) * 100
            return round(discount, 1)
        return 0

    def best_link(self):
        """Retorna o melhor link de afiliado baseado em preço"""
        return self.links.filter(
            active=True, 
            current_price__isnull=False
        ).order_by('current_price').first()

    def get_schema_data(self):
        """Gera dados estruturados Schema.org para Product"""
        schema = {
            "@context": "https://schema.org",
            "@type": self.schema_type,
            "name": self.name,
            "description": self.meta_description or self.short_description,
            "image": self.main_image,
            "url": self.get_absolute_url(),
            "sku": self.sku,
            "brand": {"@type": "Brand", "name": self.brand} if self.brand else None,
        }
        
        # Adiciona ofertas se houver
        if self.current_price:
            offers = []
            for link in self.links.filter(active=True, current_price__isnull=False):
                offer = {
                    "@type": "Offer",
                    "price": str(link.current_price),
                    "priceCurrency": "BRL",
                    "availability": "https://schema.org/InStock" if link.in_stock else "https://schema.org/OutOfStock",
                    "url": link.get_affiliate_url(),
                    "seller": {
                        "@type": "Organization",
                        "name": link.platform.name
                    }
                }
                offers.append(offer)
            if offers:
                schema["offers"] = offers[0] if len(offers) == 1 else offers
        
        # Adiciona avaliações
        if self.rating and self.review_count > 0:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(self.rating),
                "reviewCount": str(self.review_count),
                "bestRating": "5",
                "worstRating": "0"
            }
        
        return schema

    def get_price_history(self, days=30):
        """Retorna histórico de preços dos últimos X dias"""
        from affiliates.models import PriceHistory
        return PriceHistory.objects.filter(
            link__product=self,
            created_at__gte=timezone.now() - timezone.timedelta(days=days)
        ).order_by('created_at')

    def track_view(self):
        """Incrementa contador de views (usar com cache/async)"""
        Product.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )

    def __str__(self):
        return self.name