from datetime import timedelta
from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html

from .models import AffiliateLink, ClickLog, Platform


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "code",
        "colored_badge",
        "active",
        "total_links",
        "total_clicks",
    )
    list_filter = ("active",)
    search_fields = ("display_name", "code")

    @admin.display(description="Cor")
    def colored_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            obj.highlight_color,
            obj.highlight_color,
        )

    @admin.display(description="Total de Links")
    def total_links(self, obj):
        return obj.links.count()

    @admin.display(description="Total de Cliques")
    def total_clicks(self, obj):
        result = obj.links.aggregate(total=Sum("clicks"))["total"] or 0
        return f"{result:,}"


class ClickLogInline(admin.TabularInline):
    model = ClickLog
    extra = 0
    readonly_fields = ("created_at", "ip_hash", "user_agent", "source")
    can_delete = False
    max_num = 10


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'platform', 'current_price', 'original_price',
        'clicks', 'last_synced_at', 'active'
    )
    list_filter = ("platform", "active", "in_stock", "last_synced_at")
    search_fields = ("product__name", "external_id", "affiliate_url")
    autocomplete_fields = ("product",)
    ordering = ("-clicks",)

    @admin.display(description="Produto", ordering="product__name")
    def product_name(self, obj):
        return obj.product.name

    @admin.display(description="Plataforma", ordering="platform__display_name")
    def platform_badge(self, obj):
        return format_html(
            '<span style="border-left: 4px solid {}; padding-left: 6px; font-weight: bold;">{}</span>',
            obj.platform.highlight_color,
            obj.platform.display_name,
        )

    @admin.display(description="Preço Atual", ordering="current_price")
    def current_price_display(self, obj):
        if obj.current_price:
            if obj.has_discount:
                return format_html(
                    '<strong style="color: #2e7d32;">R$ {}</strong> <small style="text-decoration: line-through; color: #888;">R$ {}</small>',
                    obj.current_price,
                    obj.original_price,
                )
            return f"R$ {obj.current_price}"
        return "-"

    @admin.display(description="Total Cliques", ordering="clicks")
    def clicks_badge(self, obj):
        return format_html(
            '<strong style="background-color: #e3f2fd; color: #0d47a1; padding: 4px 10px; border-radius: 12px;">🔥 {}</strong>',
            obj.clicks,
        )

    @admin.display(description="Status Celery")
    def sync_status_badge(self, obj):
        if obj.sync_error:
            return format_html(
                '<span title="{}" style="background-color: #ffebee; color: #c62828; padding: 3px 8px; border-radius: 4px; font-weight: bold; cursor: help;">⚠️ Erro</span>',
                obj.sync_error,
            )
        # Considera sincronizado se atualizado nas últimas 2 horas
        if obj.last_synced_at and obj.last_synced_at >= timezone.now() - timedelta(hours=2):
            return format_html(
                '<span style="background-color: #e8f5e9; color: #2e7d32; padding: 3px 8px; border-radius: 4px; font-weight: bold;">Sincronizado</span>'
            )
        return format_html(
            '<span style="background-color: #fff3e0; color: #ef6c00; padding: 3px 8px; border-radius: 4px; font-weight: bold;">Pendente</span>'
        )


@admin.register(ClickLog)
class ClickLogAdmin(admin.ModelAdmin):
    list_display = ('link', 'created_at', 'source')
    list_filter = ("link__platform", "created_at")
    search_fields = ("link__product__name", "source")
    readonly_fields = ("link", "created_at", "ip_hash", "user_agent", "source")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    @admin.display(description="Produto", ordering="link__product__name")
    def link_info(self, obj):
        return obj.link.product.name

    @admin.display(description="Plataforma", ordering="link__platform__display_name")
    def platform_info(self, obj):
        return obj.link.platform.display_name

    @admin.display(description="Navegador/User Agent")
    def short_user_agent(self, obj):
        return (
            obj.user_agent[:40] + "..."
            if len(obj.user_agent) > 40
            else obj.user_agent
        )