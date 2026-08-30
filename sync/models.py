# sync/models.py
from django.db import models
from django.utils import timezone


class SyncLog(models.Model):
    """Registro de sincronizações realizadas"""
    
    class Status(models.TextChoices):
        RUNNING = 'running', 'Em execução'
        SUCCESS = 'success', 'Sucesso'
        FAILED = 'failed', 'Falhou'
        PARTIAL = 'partial', 'Parcial'
    
    task_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_products = models.IntegerField(default=0)
    updated_products = models.IntegerField(default=0)
    failed_products = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Log de Sincronização'
        verbose_name_plural = 'Logs de Sincronização'
    
    def __str__(self):
        return f"{self.task_name} - {self.status} - {self.started_at}"


class ProductSync(models.Model):
    """Controle de sincronização por produto"""
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='syncs'
    )
    platform = models.ForeignKey(
        'affiliates.Platform',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    last_synced = models.DateTimeField(null=True, blank=True)
    next_sync = models.DateTimeField(null=True, blank=True)
    sync_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-last_synced']
        verbose_name = 'Sincronização de Produto'
        verbose_name_plural = 'Sincronizações de Produtos'
    
    def __str__(self):
        return f"{self.product.name} - {self.last_synced}"