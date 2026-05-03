from rest_framework import serializers
from . import models
from users.models import User


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AssetCategory
        fields = ('id', 'name', 'description')


class AssetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = models.Asset
        fields = (
            'id', 'name', 'category', 'category_name', 'base_price', 'current_price',
            'total_supply', 'available_supply', 'buy_volume', 'sell_volume', 'event_multiplier', 'volatility', 'is_active', 'created_by', 'created_by_username', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class PortfolioSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_price = serializers.DecimalField(source='asset.current_price', read_only=True, max_digits=20, decimal_places=2)
    value = serializers.SerializerMethodField()

    class Meta:
        model = models.Portfolio
        fields = ('id', 'user', 'asset', 'asset_name', 'asset_price', 'quantity', 'avg_buy_price', 'value')
        read_only_fields = ('user',)

    def get_value(self, obj):
        """Compute total value: quantity * current_price"""
        return obj.quantity * obj.asset.current_price


class TransactionSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = models.Transaction
        fields = ('id', 'user', 'user_username', 'asset', 'asset_name', 'transaction_type', 'quantity', 'price', 'timestamp')
        read_only_fields = ('user',)


class CompanySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = models.Company
        fields = ('id', 'owner', 'owner_username', 'name', 'treasury', 'created_at')
        read_only_fields = ('owner', 'created_at')


class MarketEventSerializer(serializers.ModelSerializer):
    target_asset_name = serializers.CharField(source='target_asset.name', read_only=True, allow_null=True)
    is_active_now = serializers.SerializerMethodField()

    class Meta:
        model = models.MarketEvent
        fields = (
            'id', 'title', 'description', 'effect_type',
            'target_asset', 'target_asset_name',
            'demand_multiplier', 'volatility_multiplier', 'supply_shock',
            'scheduled_at', 'expires_at', 'activated_at',
            'executed', 'expired', 'is_active_now',
        )

    def get_is_active_now(self, obj):
        """True if the event is currently live (executed but not yet expired)."""
        return obj.executed and not obj.expired


class LedgerEntrySerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True, allow_null=True)

    class Meta:
        model = models.LedgerEntry
        fields = ('id', 'timestamp', 'user', 'user_username', 'asset', 'asset_name', 'change', 'balance_after', 'note')
