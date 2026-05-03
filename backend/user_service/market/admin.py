from django.contrib import admin
from . import models


@admin.register(models.AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'current_price', 'total_supply', 'available_supply', 'is_active')
    list_filter = ('category', 'is_active')


@admin.register(models.Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'quantity', 'avg_buy_price')


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'transaction_type', 'quantity', 'price', 'timestamp')
    list_filter = ('transaction_type',)


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'treasury')


@admin.register(models.MarketEvent)
class MarketEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_at', 'executed')


@admin.register(models.LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'change', 'balance_after')
