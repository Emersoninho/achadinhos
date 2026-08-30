# blog/urls.py
from django.urls import path
from .views import PostListView, PostDetailView, CategoryPostListView

app_name = 'blog'

urlpatterns = [
    path('', PostListView.as_view(), name='list'),
    path('categoria/<slug:slug>/', CategoryPostListView.as_view(), name='category'),
    path('post/<slug:slug>/', PostDetailView.as_view(), name='detail'),
]