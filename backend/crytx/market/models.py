"""
CRYTX — Market Models
Core trading data: AssetCategory, Asset, Portfolio, Transaction, PriceHistory
"""

from django.db import models
from django.conf import settings


class AssetCategory(models.Model):
    """Sector grouping: AgriFlux, MedCore, Volt, Arsenal, NexaTech, Ironworks"""

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=10, default='💎')
    color = models.CharField(max_length=7, default='#00f5e4')  # Hex color
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'Asset Categories'

    def __str__(self):
        return f"{self.icon} {self.name}"


class Asset(models.Model):
    """A tradeable Crytal card."""

    name = models.CharField(max_length=150)
    ticker = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    base_price = models.DecimalField(max_digits=20, decimal_places=2)
    current_price = models.DecimalField(max_digits=20, decimal_places=2)
    total_supply = models.IntegerField(default=100000)
    circulating_supply = models.IntegerField(default=0)
    volatility = models.DecimalField(max_digits=5, decimal_places=3, default=0.05)
    buy_volume = models.IntegerField(default=0)
    sell_volume = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticker} ({self.name}) @ {self.current_price} Ç"

    @property
    def change_pct(self):
        """Price change percentage from base price."""
        if self.base_price == 0:
            return 0
        return float((self.current_price - self.base_price) / self.base_price * 100)


class Portfolio(models.Model):
    """Player's holding of a specific asset."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolios')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='holders')
    quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    avg_buy_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'asset')

    def __str__(self):
        return f"{self.user.username} holds {self.quantity}x {self.asset.ticker}"

    @property
    def current_value(self):
        return float(self.quantity * self.asset.current_price)

    @property
    def profit_loss(self):
        return float(self.quantity * (self.asset.current_price - self.avg_buy_price))

    @property
    def profit_loss_pct(self):
        if self.avg_buy_price == 0:
            return 0
        return float((self.asset.current_price - self.avg_buy_price) / self.avg_buy_price * 100)


class Transaction(models.Model):
    """Record of every trade executed."""

    TRADE_TYPES = [('BUY', 'Buy'), ('SELL', 'Sell')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transactions')
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    price_at_trade = models.DecimalField(max_digits=20, decimal_places=2)
    total_cost = models.DecimalField(max_digits=20, decimal_places=2)
    fee = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.isoformat()} {self.user.username} {self.trade_type} {self.quantity}x {self.asset.ticker}"


class PriceHistory(models.Model):
    """Time-series price data for charts."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    volume = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.asset.ticker} @ {self.price} Ç ({self.timestamp.isoformat()})"
