"""
CRYTX — User & Wallet Models
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Extended user with CRYTX-specific fields."""

    RANK_CHOICES = [
        ('scavenger', 'Scavenger'),
        ('trader', 'Trader'),
        ('merchant', 'Merchant'),
        ('baron', 'Baron'),
        ('syndicate_lord', 'Syndicate Lord'),
        ('crystal_sovereign', 'Crystal Sovereign'),
    ]

    rank = models.CharField(max_length=30, choices=RANK_CHOICES, default='scavenger')
    avatar_url = models.URLField(blank=True, default='')
    total_earned = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_trades = models.IntegerField(default=0)

    def __str__(self):
        return f"[{self.rank.upper()}] {self.username}"


class Wallet(models.Model):
    """Player's Crytal (Ç) balance."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=settings.CRYTX_STARTING_BALANCE)

    def __str__(self):
        return f"{self.user.username}: {self.balance} Ç"
