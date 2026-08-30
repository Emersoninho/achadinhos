# products/context_processors.py
from .services import CategoryService


def seo_context(request):
    """Adiciona dados SEO globais ao contexto"""
    context = {
        'site_name': 'Achadinhos',
        'site_description': 'Melhores ofertas e descontos na Amazon, Mercado Livre e Shopee',
        'site_url': f'{request.scheme}://{request.get_host()}',
    }
    
    # Categorias para menu (cache)
    try:
        context['menu_categories'] = CategoryService.get_menu_categories()
    except:
        context['menu_categories'] = []
    
    # Página atual para canonical
    context['current_url'] = request.build_absolute_uri()
    
    return context