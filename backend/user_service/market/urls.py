from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.AssetCategoryViewSet, basename='assetcategory')
router.register(r'assets', views.AssetViewSet, basename='asset')
router.register(r'holdings', views.HoldingViewSet, basename='holding')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'events', views.MarketEventViewSet, basename='marketevent')
router.register(r'ledger', views.LedgerEntryViewSet, basename='ledgerentry')

urlpatterns = [
    path('', include(router.urls)),
]
