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
            'supply', 'demand', 'volatility', 'is_active', 'created_by', 'created_by_username', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class HoldingSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_price = serializers.DecimalField(source='asset.current_price', read_only=True, max_digits=20, decimal_places=2)
    value = serializers.SerializerMethodField()

    class Meta:
        model = models.Holding
        fields = ('id', 'user', 'asset', 'asset_name', 'asset_price', 'quantity', 'avg_price', 'value')
        read_only_fields = ('user',)

    def get_value(self, obj):
        """Compute total value: quantity * current_price"""
        return obj.quantity * obj.asset.current_price


class OrderSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = models.Order
        fields = ('id', 'user', 'user_username', 'asset', 'asset_name', 'quantity', 'price', 'side', 'status', 'created_at', 'completed_at')
        read_only_fields = ('user', 'completed_at')


class CompanySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = models.Company
        fields = ('id', 'owner', 'owner_username', 'name', 'treasury', 'created_at')
        read_only_fields = ('owner', 'created_at')


class MarketEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MarketEvent
        fields = ('id', 'title', 'description', 'effect_json', 'impact', 'scheduled_at', 'executed')


class LedgerEntrySerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True, allow_null=True)

    class Meta:
        model = models.LedgerEntry
        fields = ('id', 'timestamp', 'user', 'user_username', 'asset', 'asset_name', 'change', 'balance_after', 'note')
