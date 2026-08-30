# sync/admin.py
from django.contrib import admin
from .models import SyncLog, ProductSync


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'status', 'started_at', 'finished_at', 'total_products', 'updated_products', 'failed_products']
    list_filter = ['status', 'task_name', 'started_at']
    search_fields = ['task_name', 'error_message']
    readonly_fields = ['task_name', 'status', 'started_at', 'finished_at', 'total_products', 'updated_products', 'failed_products']
    
    def has_add_permission(self, request):
        return False


@admin.register(ProductSync)
class ProductSyncAdmin(admin.ModelAdmin):
    list_display = ['product', 'platform', 'last_synced', 'next_sync', 'sync_count']
    list_filter = ['platform', 'last_synced']
    search_fields = ['product__name']
    autocomplete_fields = ['product', 'platform']