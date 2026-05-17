from django.contrib import admin
from .models import AssetCategory, Asset, Portfolio, Transaction, PriceHistory

admin.site.register(AssetCategory)
admin.site.register(Asset)
admin.site.register(Portfolio)
admin.site.register(Transaction)
admin.site.register(PriceHistory)
