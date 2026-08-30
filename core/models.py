from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django.db.models import F

from affiliates.models import AffiliateLink

import requests
from celery import shared_task
from django.utils import timezone
from affiliates.models import AffiliateLink


class SiteConfig(models.Model):
    """
    Singleton — always a single row (pk=1).
    Holds global data used in base.html and SEO (default meta tags, analytics, etc.)
    """
    site_name = models.CharField(max_length=100, default="Meu Site de Ofertas")
    default_description = models.CharField(max_length=160, blank=True)
    logo = models.ImageField(upload_to="site/", blank=True, null=True)

    google_analytics_id = models.CharField(max_length=30, blank=True)
    google_search_console_verification = models.CharField(max_length=100, blank=True)

    # Affiliate IDs per platform — used when generating links (e.g. Amazon tracking tag)
    amazon_tracking_id = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1  # force singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # prevent accidental deletion

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.site_name




@require_GET
def go_to_affiliate(request, link_id):
    """
    Route: /go/<link_id>/
    Logs the click and redirects (302) to the real affiliate link.
    Keeps the affiliate link out of the public HTML, preventing scraping/commission theft.
    """
    link = get_object_or_404(AffiliateLink, id=link_id, active=True)

    # Atomic increment, avoids race conditions under high concurrency
    AffiliateLink.objects.filter(id=link.id).update(clicks=F("clicks") + 1)

    # Optional: log to a separate table for more detailed analytics
    # (product, platform, IP hash, user-agent, timestamp, referrer)

    return redirect(link.affiliate_url, permanent=False)




@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_mercado_livre_price(self, link_id):
    """
    Queries the ML public API for a specific item and updates the local price.
    Public API, no token required: https://api.mercadolibre.com/items/{id}
    """
    try:
        link = AffiliateLink.objects.select_related("platform").get(id=link_id)
        resp = requests.get(
            f"https://api.mercadolibre.com/items/{link.external_id}",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        link.current_price = data.get("price")
        link.original_price = data.get("original_price") or data.get("price")
        link.in_stock = data.get("available_quantity", 0) > 0
        link.last_synced_at = timezone.now()
        link.sync_error = ""
        link.save(update_fields=[
            "current_price", "original_price", "in_stock",
            "last_synced_at", "sync_error",
        ])

    except requests.RequestException as exc:
        link = AffiliateLink.objects.filter(id=link_id).first()
        if link:
            link.sync_error = str(exc)[:255]
            link.save(update_fields=["sync_error"])
        raise self.retry(exc=exc)


@shared_task
def sync_featured_products():
    """
    Scheduled task (Celery Beat) — runs every 1h for featured products.
    Dispatches one sub-task per link, routing to the right function per platform.
    """
    featured_links = AffiliateLink.objects.filter(
        active=True, product__featured=True
    ).select_related("platform")

    for link in featured_links:
        if link.platform.code == "mercado_livre":
            sync_mercado_livre_price.delay(link.id)
        # elif link.platform.code == "amazon":
        #     sync_amazon_price.delay(link.id)
        # elif link.platform.code == "shopee":
        #     sync_shopee_price.delay(link.id)
        # elif link.platform.code == "magalu":
        #     sync_magalu_price.delay(link.id)


@shared_task
def sync_general_catalog():
    """Scheduled task — runs every 6-12h for the rest of the catalog."""
    links = AffiliateLink.objects.filter(
        active=True, product__featured=False
    ).select_related("platform")

    for link in links:
        if link.platform.code == "mercado_livre":
            sync_mercado_livre_price.delay(link.id)
        # ... other platforms follow the same pattern