# sync/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def sync_featured_products():
    """Sincroniza produtos em destaque (mais frequentemente)"""
    from products.models import Product
    from sync.models import SyncLog
    
    log = SyncLog.objects.create(
        task_name='sync_featured_products',
        status='running'
    )
    
    try:
        # Busca produtos em destaque
        products = Product.objects.filter(
            featured=True,
            status='active'
        )
        
        log.total_products = products.count()
        updated = 0
        failed = 0
        
        for product in products:
            try:
                # Aqui você vai integrar com as APIs das plataformas
                # Por enquanto, só atualiza o timestamp
                product.price_updated_at = timezone.now()
                product.save(update_fields=['price_updated_at', 'updated_at'])
                updated += 1
                
            except Exception as e:
                failed += 1
                logger.error(f"Erro ao sincronizar {product.name}: {str(e)}")
        
        log.updated_products = updated
        log.failed_products = failed
        log.status = 'success'
        log.finished_at = timezone.now()
        log.save()
        
        return f"Sincronização concluída: {updated} atualizados, {failed} falhas"
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.finished_at = timezone.now()
        log.save()
        logger.error(f"Falha na sincronização: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def sync_general_catalog():
    """Sincroniza catálogo geral (menos frequente)"""
    from products.models import Product
    from sync.models import SyncLog
    
    log = SyncLog.objects.create(
        task_name='sync_general_catalog',
        status='running'
    )
    
    try:
        # Busca todos os produtos ativos
        products = Product.objects.filter(status='active')
        
        log.total_products = products.count()
        updated = 0
        
        for product in products:
            try:
                # Integração com APIs aqui
                product.price_updated_at = timezone.now()
                product.save(update_fields=['price_updated_at', 'updated_at'])
                updated += 1
                
            except Exception as e:
                logger.error(f"Erro ao sincronizar {product.name}: {str(e)}")
        
        log.updated_products = updated
        log.status = 'success'
        log.finished_at = timezone.now()
        log.save()
        
        return f"Catálogo sincronizado: {updated} produtos"
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.finished_at = timezone.now()
        log.save()
        return f"Erro: {str(e)}"


@shared_task
def sync_product_price(product_id):
    """Sincroniza preço de um produto específico"""
    from products.models import Product
    from sync.models import ProductSync
    
    try:
        product = Product.objects.get(pk=product_id)
        
        # Aqui você vai buscar o preço nas APIs
        # Por enquanto, só registra a sincronização
        
        sync, created = ProductSync.objects.get_or_create(
            product=product
        )
        
        sync.last_synced = timezone.now()
        sync.next_sync = timezone.now() + timedelta(hours=1)
        sync.sync_count += 1
        sync.save()
        
        return f"Produto {product.name} sincronizado"
        
    except Product.DoesNotExist:
        return f"Produto {product_id} não encontrado"


@shared_task
def clean_old_logs():
    """Limpa logs antigos (mais de 30 dias)"""
    from sync.models import SyncLog
    
    threshold = timezone.now() - timedelta(days=30)
    deleted, _ = SyncLog.objects.filter(started_at__lt=threshold).delete()
    
    return f"{deleted} logs removidos"