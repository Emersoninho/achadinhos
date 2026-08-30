# products/urls.py
from django.urls import path
from .views import ProductListView, ProductDetailView, CategoryDetailView, PriceDropListView, ImportProductView  # Adicione ImportProductView


app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('categoria/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('produto/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('ofertas/', PriceDropListView.as_view(), name='price_drops'),
    # products/urls.py
path('importar/', ImportProductView.as_view(), name='import_product'),
]