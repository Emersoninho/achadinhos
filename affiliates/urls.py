from django.urls import path
from .views import AffiliateRedirectView

app_name = "affiliates"

urlpatterns = [
    path("out/<int:pk>/", AffiliateRedirectView.as_view(), name="redirect"),
]