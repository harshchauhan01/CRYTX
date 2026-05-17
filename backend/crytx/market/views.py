"""
CRYTX — Market Views
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal
from django.db.models import Sum, F, DecimalField, OuterRef, Subquery, Value, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.conf import settings

from .models import AssetCategory, Asset, Portfolio, Transaction, PriceHistory
from .serializers import (
    AssetCategorySerializer, AssetSerializer, PortfolioSerializer,
    TransactionSerializer, PriceHistorySerializer, TradeSerializer,
)
from .trading_engine import execute_buy, execute_sell, TradeError
from users.models import User, Wallet


class AssetCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Asset.objects.filter(is_active=True).select_related('category')
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def history(self, request, pk=None):
        """Get price history for an asset (for charts)."""
        asset = self.get_object()
        limit = int(request.query_params.get('limit', 100))
        history = PriceHistory.objects.filter(asset=asset).order_by('-timestamp')[:limit]
        # Return in chronological order
        data = PriceHistorySerializer(reversed(list(history)), many=True).data
        return Response(data)


class PortfolioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(
            user=self.request.user, quantity__gt=0
        ).select_related('asset', 'asset__category')

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def value(self, request):
        """Calculate total portfolio value using DB aggregation."""
        total = Portfolio.objects.filter(
            user=request.user, quantity__gt=0
        ).aggregate(
            total_value=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F('quantity') * F('asset__current_price'),
                        output_field=DecimalField(max_digits=20, decimal_places=2)
                    )
                ),
                Value(Decimal('0')),
                output_field=DecimalField(max_digits=20, decimal_places=2)
            )
        )['total_value']

        wallet_balance = request.user.wallet.balance

        return Response({
            'portfolio_value': float(total),
            'wallet_balance': float(wallet_balance),
            'net_worth': float(total + wallet_balance),
        })


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user
        ).select_related('asset')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def execute_trade(request):
    """Execute a BUY or SELL trade."""
    serializer = TradeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        if data['trade_type'] == 'BUY':
            result = execute_buy(request.user, data['asset_id'], data['quantity'])
        else:
            result = execute_sell(request.user, data['asset_id'], data['quantity'])
        return Response(result, status=status.HTTP_200_OK)
    except TradeError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Trade failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def leaderboard(request):
    """
    Top 50 players by net worth.
    Uses DB-level aggregation to avoid O(N) memory issues.
    """
    portfolio_value_subquery = Portfolio.objects.filter(
        user=OuterRef('pk')
    ).values('user').annotate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('asset__current_price'),
                output_field=DecimalField(max_digits=20, decimal_places=2)
            )
        )
    ).values('total')

    users = User.objects.annotate(
        portfolio_val=Coalesce(Subquery(portfolio_value_subquery), 0, output_field=DecimalField()),
        wallet_bal=Coalesce(Subquery(Wallet.objects.filter(user=OuterRef('pk')).values('balance')[:1]), 0, output_field=DecimalField()),
    ).annotate(
        net_worth=F('portfolio_val') + F('wallet_bal')
    ).order_by('-net_worth')[:50]

    data = [
        {
            'rank': idx + 1,
            'username': u.username,
            'player_rank': u.rank,
            'net_worth': float(u.net_worth),
            'total_trades': u.total_trades,
        }
        for idx, u in enumerate(users)
    ]
    return Response(data)
