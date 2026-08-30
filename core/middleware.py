# core/middleware.py
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SEOMiddleware:
    """Middleware para otimizações SEO automáticas"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Adiciona headers de segurança e SEO
        if hasattr(response, 'content'):
            # X-Robots-Tag para páginas de admin
            if request.path.startswith('/admin/'):
                response['X-Robots-Tag'] = 'noindex, nofollow'
            
            # Headers de segurança
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Cache para páginas públicas
            if request.method == 'GET' and not request.user.is_authenticated:
                if not request.path.startswith('/admin/'):
                    response['Cache-Control'] = 'public, max-age=300'  # 5 minutos
        
        return response
    
    def process_exception(self, request, exception):
        """Log de erros para monitoramento"""
        logger.error(f"Erro na página {request.path}: {str(exception)}")
        return None


class RedirectWWWMiddleware:
    """Redireciona www para non-www (ou vice-versa) para evitar conteúdo duplicado"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        host = request.get_host()
        
        # Redireciona www para non-www
        if host.startswith('www.'):
            from django.shortcuts import redirect
            url = request.build_absolute_uri().replace('://www.', '://', 1)
            return redirect(url, permanent=True)
        
        return self.get_response(request)