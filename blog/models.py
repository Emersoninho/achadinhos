from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings


class PostCategory(models.Model):
    """Editorial blog category (may or may not match a products Category)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Post categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    class PostType(models.TextChoices):
        REVIEW = "review", "Product review"
        COMPARISON = "comparison", "Comparison (X vs Y)"
        GUIDE = "guide", "Buying guide"
        LIST = "list", "List (top 10, best of...)"
        NEWS = "news", "News/Deal"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=280, blank=True)
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.GUIDE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, related_name="posts")

    summary = models.CharField(max_length=300, help_text="Used in listings and as meta_description fallback")
    content = models.TextField(help_text="Post body — HTML/Markdown, 100% original content")
    cover_image = models.URLField(max_length=500, blank=True)

    # Products mentioned in the post — allows building "products mentioned" blocks with live pricing
    products = models.ManyToManyField(
        "products.Product", blank=True, related_name="posts", through="ProductMention"
    )

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status", "published_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:280]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title


class ProductMention(models.Model):
    """
    Post <-> Product through table.
    Lets you rank/rate a product within a comparison (e.g. "1st place", score 9.5) and
    point to WHICH AffiliateLink (platform) the post is specifically recommending.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    recommended_link = models.ForeignKey(
        "affiliates.AffiliateLink", on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Which platform this post recommends for this product"
    )
    position = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="E.g. 1st, 2nd place in a list/comparison"
    )
    score = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True, help_text="Editor's score, e.g. 9.5"
    )
    editor_notes = models.TextField(blank=True, help_text="Pros/cons specific to this product in this post")

    class Meta:
        ordering = ["position"]
        unique_together = ("post", "product")

    def __str__(self):
        return f"{self.product.name} in {self.post.title}"
