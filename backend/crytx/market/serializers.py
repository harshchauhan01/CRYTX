"""
CRYTX — Market Serializers
"""

from rest_framework import serializers
from .models import AssetCategory, Asset, Portfolio, Transaction, PriceHistory


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ['id', 'name', 'icon', 'color', 'description']


class AssetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    change_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'ticker', 'category', 'category_name',
            'category_icon', 'category_color', 'base_price',
            'current_price', 'total_supply', 'circulating_supply',
            'volatility', 'buy_volume', 'sell_volume', 'change_pct',
            'is_active', 'created_at',
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_ticker = serializers.CharField(source='asset.ticker', read_only=True)
    asset_price = serializers.DecimalField(source='asset.current_price', max_digits=20, decimal_places=2, read_only=True)
    category_icon = serializers.CharField(source='asset.category.icon', read_only=True)
    category_color = serializers.CharField(source='asset.category.color', read_only=True)
    current_value = serializers.FloatField(read_only=True)
    profit_loss = serializers.FloatField(read_only=True)
    profit_loss_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            'id', 'asset', 'asset_name', 'asset_ticker', 'asset_price',
            'category_icon', 'category_color', 'quantity',
            'avg_buy_price', 'current_value', 'profit_loss', 'profit_loss_pct',
        ]


class TransactionSerializer(serializers.ModelSerializer):
    asset_ticker = serializers.CharField(source='asset.ticker', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'asset', 'asset_ticker', 'asset_name', 'trade_type',
            'quantity', 'price_at_trade', 'total_cost', 'fee', 'timestamp',
        ]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['price', 'volume', 'timestamp']


class TradeSerializer(serializers.Serializer):
    """Input serializer for trade execution."""
    asset_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=20, decimal_places=4)
    trade_type = serializers.ChoiceField(choices=['BUY', 'SELL'])
