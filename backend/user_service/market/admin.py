from django.contrib import admin
from . import models


@admin.register(models.AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'current_price', 'supply', 'demand', 'is_active')
    list_filter = ('category', 'is_active')


@admin.register(models.Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'quantity', 'avg_price')


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'side', 'quantity', 'price', 'status', 'created_at')
    list_filter = ('status', 'side')


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'treasury')


@admin.register(models.MarketEvent)
class MarketEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_at', 'executed')


@admin.register(models.LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'change', 'balance_after')
