# products/management/commands/check_seo.py
from django.core.management.base import BaseCommand
from products.models import Product, Category
from django.db.models import Q


class Command(BaseCommand):
    help = 'Verifica problemas de SEO nos produtos e categorias'
    
    def handle(self, *args, **options):
        self.stdout.write('Verificando SEO...\n')
        
        # Produtos sem meta description
        products_no_meta = Product.objects.filter(
            Q(meta_description='') | Q(meta_description__isnull=True),
            status='active'
        )
        
        if products_no_meta.exists():
            self.stdout.write(self.style.WARNING(
                f'⚠️ {products_no_meta.count()} produtos sem meta description'
            ))
        
        # Produtos sem imagem
        products_no_image = Product.objects.filter(
            Q(main_image='') | Q(main_image__isnull=True),
            status='active'
        )
        
        if products_no_image.exists():
            self.stdout.write(self.style.WARNING(
                f'⚠️ {products_no_image.count()} produtos sem imagem'
            ))
        
        # Produtos sem preço
        products_no_price = Product.objects.filter(
            current_price__isnull=True,
            status='active'
        )
        
        if products_no_price.exists():
            self.stdout.write(self.style.WARNING(
                f'⚠️ {products_no_price.count()} produtos sem preço'
            ))
        
        # Categorias sem meta description
        categories_no_meta = Category.objects.filter(
            Q(meta_description='') | Q(meta_description__isnull=True),
            is_active=True
        )
        
        if categories_no_meta.exists():
            self.stdout.write(self.style.WARNING(
                f'⚠️ {categories_no_meta.count()} categorias sem meta description'
            ))
        
        # Resumo
        total_products = Product.objects.filter(status='active').count()
        total_categories = Category.objects.filter(is_active=True).count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {total_products} produtos ativos'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'✅ {total_categories} categorias ativas'
        ))