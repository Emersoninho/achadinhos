from django.db import models


class Platform(models.Model):
    """Shopee, Mercado Livre, Amazon, Magalu"""
    class Code(models.TextChoices):
        SHOPEE = "shopee", "Shopee"
        MERCADO_LIVRE = "mercado_livre", "Mercado Livre"
        AMAZON = "amazon", "Amazon"
        MAGALU = "magalu", "Magazine Luiza"

    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    display_name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="platforms/", blank=True, null=True)
    highlight_color = models.CharField(max_length=7, default="#000000")
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Platform"
        verbose_name_plural = "Platforms"

    def __str__(self):
        return self.display_name

    @property
    def name(self):
        return self.display_name

    


class AffiliateLink(models.Model):
    """Links a Product (products app) to a Platform, with price synced via API"""
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="links"
    )
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="links")

    external_id = models.CharField(max_length=100, help_text="SKU/ASIN/item ID on the platform")
    affiliate_url = models.URLField(max_length=1000, help_text="Link already containing your affiliate code")

    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    in_stock = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.CharField(max_length=255, blank=True)

    active = models.BooleanField(default=True)
    clicks = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("platform", "external_id")
        indexes = [
            models.Index(fields=["product", "platform"]),
        ]

    @property
    def has_discount(self):
        return bool(self.original_price and self.current_price and self.original_price > self.current_price)

    @property
    def discount_percentage(self):
        if self.has_discount:
            return round((1 - self.current_price / self.original_price) * 100)
        return 0

    def __str__(self):
        return f"{self.product.name} @ {self.platform.display_name}"

    def get_affiliate_url(self):
            return self.affiliate_url

class ClickLog(models.Model):
    """Detailed record of each click, for in-house analytics (separate from the aggregate AffiliateLink.clicks)"""
    link = models.ForeignKey(AffiliateLink, on_delete=models.CASCADE, related_name="click_logs")
    created_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64, blank=True)  # hashed IP, never raw IP (LGPD)
    user_agent = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255, blank=True, help_text="Referrer: blog post, category, search...")

    class Meta:
        indexes = [
            models.Index(fields=["link", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Click on {self.link} - {self.created_at:%d/%m/%Y %H:%M}"

    