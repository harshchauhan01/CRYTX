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
    total_supply = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    available_supply = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    buy_volume = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    sell_volume = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    event_multiplier = models.FloatField(default=1.0)
    volatility = models.FloatField(default=0.05)
    is_active = models.BooleanField(default=True)
    circuit_breaker_tripped = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['current_price']),
        ]

    def __str__(self) -> str:
        return self.name


class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolios')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='portfolios')
    quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    avg_buy_price = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    class Meta:
        unique_together = ('user', 'asset')

    def __str__(self) -> str:
        return f"{self.user.username} - {self.asset.name}"


class Transaction(models.Model):
    TRANSACTION_BUY = 'buy'
    TRANSACTION_SELL = 'sell'
    TRANSACTION_CHOICES = [(TRANSACTION_BUY, 'Buy'), (TRANSACTION_SELL, 'Sell')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='transactions')
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_CHOICES)
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    price = models.DecimalField(max_digits=20, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} {self.transaction_type} {self.quantity} {self.asset.name} @ {self.price}"


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=150, unique=True)
    treasury = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class MarketEvent(models.Model):
    """
    A scheduled macroeconomic event that injects economic pressure into the market.

    Events do NOT directly set prices. They modify:
      - demand_multiplier: scales buy-side pressure (>1 = demand spike, <1 = demand crash)
      - volatility_multiplier: scales asset volatility during the event window
      - supply_shock: one-time injection (+) or removal (-) of available supply on activation

    Lifecycle: SCHEDULED -> ACTIVE -> EXPIRED
    Driven by the Celery Beat task `apply_events_task`.
    """

    class EffectType(models.TextChoices):
        DEMAND_SPIKE   = 'demand_spike',   'Demand Spike'
        DEMAND_CRASH   = 'demand_crash',   'Demand Crash'
        SUPPLY_SHOCK   = 'supply_shock',   'Supply Shock'
        VOLATILITY_SURGE = 'volatility_surge', 'Volatility Surge'
        GENERAL        = 'general',        'General'

    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    effect_type = models.CharField(
        max_length=20,
        choices=EffectType.choices,
        default=EffectType.GENERAL,
    )
    target_asset = models.ForeignKey(
        Asset,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='events',
        help_text='Null = global event affecting all assets',
    )
    # Multipliers applied while the event is ACTIVE
    demand_multiplier    = models.FloatField(default=1.0)
    volatility_multiplier = models.FloatField(default=1.0)
    supply_shock         = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    scheduled_at = models.DateTimeField()
    expires_at   = models.DateTimeField()
    activated_at = models.DateTimeField(null=True, blank=True)
    executed     = models.BooleanField(default=False)  # True once activated
    expired      = models.BooleanField(default=False)  # True once cleaned up

    class Meta:
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['executed', 'expired', 'scheduled_at']),
        ]

    def __str__(self) -> str:
        return f"[{self.effect_type}] {self.title}"


class LedgerEntry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)
    change = models.DecimalField(max_digits=20, decimal_places=4)
    balance_after = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.timestamp.isoformat()} {self.user} {self.change}"


class PriceHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=20, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['asset', 'timestamp']),
        ]

    def __str__(self) -> str:
        return f"{self.asset.name} @ {self.price} on {self.timestamp}"
