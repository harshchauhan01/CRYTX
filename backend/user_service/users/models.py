from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    currency = models.CharField(max_length=10, default='USD')
    balance = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    locked_balance = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    class Meta:
        unique_together = ('user', 'currency')
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name='balance_gte_0'),
            models.CheckConstraint(check=models.Q(locked_balance__gte=0), name='locked_balance_gte_0'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.currency} - {self.balance}"