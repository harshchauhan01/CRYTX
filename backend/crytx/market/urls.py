"""
CRYTX — Market URL routes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.AssetCategoryViewSet, basename='categories')
router.register(r'assets', views.AssetViewSet, basename='assets')
router.register(r'portfolio', views.PortfolioViewSet, basename='portfolio')
router.register(r'transactions', views.TransactionViewSet, basename='transactions')

urlpatterns = [
    path('trade/', views.execute_trade, name='trade'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('', include(router.urls)),
]
