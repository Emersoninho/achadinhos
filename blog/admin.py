# blog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Post, PostCategory, ProductMention


class ProductMentionInline(admin.TabularInline):
    """Inline para gerenciar produtos mencionados no post"""
    model = ProductMention
    extra = 1
    fields = ['product', 'position', 'score', 'recommended_link', 'editor_notes']
    autocomplete_fields = ['product', 'recommended_link']
    classes = ['collapse']


@admin.register(PostCategory)
class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    
    def post_count(self, obj):
        return obj.posts.filter(status='published').count()
    post_count.short_description = 'Posts Publicados'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'post_type', 'status', 'category', 'author',
        'published_at', 'product_count', 'created_at'
    ]
    list_filter = ['status', 'post_type', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'slug', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['category', 'author']
    inlines = [ProductMentionInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'post_type', 'status', 'author')
        }),
        ('Conteúdo', {
            'fields': ('summary', 'content', 'cover_image')
        }),
        ('Categorização', {
            'fields': ('category',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('wide', 'collapse')
        }),
        ('Publicação', {
            'fields': ('published_at', 'created_at', 'updated_at')
        }),
    )
    
    def product_count(self, obj):
        return obj.productmention_set.count()
    product_count.short_description = 'Produtos'
    
    actions = ['publish_posts', 'archive_posts', 'make_draft']
    
    def publish_posts(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} post(s) publicado(s) com sucesso!')
    publish_posts.short_description = 'Publicar posts selecionados'
    
    def archive_posts(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} post(s) arquivado(s)!')
    archive_posts.short_description = 'Arquivar posts selecionados'
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} post(s) movido(s) para rascunho!')
    make_draft.short_description = 'Mover para rascunho'


@admin.register(ProductMention)
class ProductMentionAdmin(admin.ModelAdmin):
    list_display = ['post', 'product', 'position', 'score', 'recommended_link']
    list_filter = ['post', 'position']
    search_fields = ['post__title', 'product__name']
    autocomplete_fields = ['post', 'product', 'recommended_link']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'post', 'product', 'recommended_link__platform'
        )