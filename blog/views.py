# blog/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Prefetch
from django.core.cache import cache
from django.utils import timezone
from .models import Post, PostCategory, ProductMention


class PostListView(ListView):
    """Lista de posts do blog"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Post.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category')
        
        # Filtro por categoria
        category_slug = self.kwargs.get('slug') or self.request.GET.get('categoria')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filtro por tipo
        post_type = self.request.GET.get('tipo')
        if post_type:
            queryset = queryset.filter(post_type=post_type)
        
        # Busca
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categorias do blog
        context['categories'] = PostCategory.objects.all()
        
        # SEO
        context['meta_title'] = 'Blog | Achadinhos - Dicas e Reviews'
        context['meta_description'] = 'Dicas, reviews e guias de compra para você economizar. Os melhores achadinhos analisados por especialistas.'
        
        return context


class PostDetailView(DetailView):
    """Detalhe do post"""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related(
            Prefetch(
                'productmention_set',
                queryset=ProductMention.objects.select_related('product', 'recommended_link__platform')
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Posts relacionados (mesma categoria)
        if post.category:
            related_posts = Post.objects.filter(
                category=post.category,
                status='published',
                published_at__lte=timezone.now()
            ).exclude(pk=post.pk)[:4]
            context['related_posts'] = related_posts
        
        # Produtos mencionados
        context['product_mentions'] = post.productmention_set.select_related(
            'product', 'recommended_link__platform'
        )
        
        # SEO
        context['meta_title'] = post.meta_title or post.title
        context['meta_description'] = post.meta_description or post.summary
        context['canonical_url'] = post.get_absolute_url()
        
        # Schema.org para BlogPosting
        context['schema_data'] = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.summary,
            "image": post.cover_image,
            "datePublished": post.published_at.isoformat() if post.published_at else None,
            "dateModified": post.updated_at.isoformat(),
            "author": {
                "@type": "Person",
                "name": post.author.get_full_name() or post.author.username if post.author else "Equipe Achadinhos"
            }
        }
        
        return context


class CategoryPostListView(ListView):
    """Posts por categoria"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(PostCategory, slug=self.kwargs.get('slug'))
        
        return Post.objects.filter(
            category=self.category,
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PostCategory.objects.all()
        context['current_category'] = self.category
        
        # SEO
        context['meta_title'] = f'{self.category.name} | Blog Achadinhos'
        context['meta_description'] = f'Artigos sobre {self.category.name}. Dicas e reviews exclusivos.'
        
        return context