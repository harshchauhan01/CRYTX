from django.conf import settings
from django.db import models


class AssetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Asset(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    base_price = models.DecimalField(max_digits=20, decimal_places=2)
    current_price = models.DecimalField(max_digits=20, decimal_places=2)
    supply = models.PositiveBigIntegerField(default=0)
    demand = models.PositiveBigIntegerField(default=0)
    volatility = models.FloatField(default=0.05)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['current_price']),
        ]

    def __str__(self) -> str:
        return self.name


class Holding(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='holdings')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    avg_price = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    class Meta:
        unique_together = ('user', 'asset')

    def __str__(self) -> str:
        return f"{self.user.username} - {self.asset.name}"


class Order(models.Model):
    SIDE_BUY = 'buy'
    SIDE_SELL = 'sell'
    SIDE_CHOICES = [(SIDE_BUY, 'Buy'), (SIDE_SELL, 'Sell')]

    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_PENDING, 'Pending'), (STATUS_COMPLETED, 'Completed'), (STATUS_FAILED, 'Failed')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='orders')
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    price = models.DecimalField(max_digits=20, decimal_places=4)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} {self.side} {self.quantity} {self.asset.name} @ {self.price}"


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=150, unique=True)
    treasury = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class MarketEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    effect_json = models.JSONField(blank=True, null=True)
    impact = models.FloatField(default=0)
    scheduled_at = models.DateTimeField()
    executed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class LedgerEntry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)
    change = models.DecimalField(max_digits=20, decimal_places=4)
    balance_after = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.timestamp.isoformat()} {self.user} {self.change}"
