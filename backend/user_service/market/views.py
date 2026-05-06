from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from . import models, serializers
from users.models import User


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AssetCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.AssetCategory.objects.all()
    serializer_class = serializers.AssetCategorySerializer
    permission_classes = [permissions.AllowAny]


class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Asset.objects.filter(is_active=True)
    serializer_class = serializers.AssetSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_assets(self, request):
        """Get assets created by current user"""
        assets = models.Asset.objects.filter(created_by=request.user)
        serializer = self.get_serializer(assets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def history(self, request, pk=None):
        """Get price history for charting"""
        asset = self.get_object()
        # Get the last 60 ticks (10 minutes of data at 10s intervals)
        history = asset.price_history.order_by('-timestamp')[:60]
        # Return in chronological order
        data = [{'time': h.timestamp.isoformat(), 'price': float(h.price)} for h in reversed(history)]
        return Response(data)


class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return models.Portfolio.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        return Response({'error': 'Cannot create portfolios directly. Use /transactions/ endpoint.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def portfolio_value(self, request):
        """Calculate total portfolio value"""
        from django.db.models import Sum, F, DecimalField
        from django.db.models.functions import Coalesce
        
        result = self.get_queryset().aggregate(
            total=Coalesce(Sum(F('quantity') * F('asset__current_price'), output_field=DecimalField()), Decimal('0.00'))
        )
        total_value = result['total']
        
        from users.models import Wallet
        user_wallet = Wallet.objects.filter(user=request.user, currency='USD').first()
        user_balance = user_wallet.balance if user_wallet else Decimal('0.00')
        
        net_worth = total_value + user_balance
        return Response({
            'total_portfolios_value': float(total_value),
            'cash_balance': float(user_balance),
            'net_worth': float(net_worth)
        })


from .trading_engine import execute_buy, execute_sell

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return models.Transaction.objects.filter(user=self.request.user).order_by('-timestamp')

    def create(self, request, *args, **kwargs):
        """Place a buy or sell transaction with atomic transaction engine"""
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({'error': 'Idempotency-Key header is required'}, status=status.HTTP_400_BAD_REQUEST)

        asset_id = request.data.get('asset_id')
        quantity = request.data.get('quantity', 0)
        side = request.data.get('side', '').lower()

        if not asset_id or not quantity or side not in ['buy', 'sell']:
            return Response({'error': 'Invalid asset_id, quantity, or side'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if side == 'buy':
                txn = execute_buy(request.user, asset_id, quantity, idempotency_key)
            elif side == 'sell':
                txn = execute_sell(request.user, asset_id, quantity, idempotency_key)

            serializer = self.get_serializer(txn)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except models.Asset.DoesNotExist:
            return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)
        except models.Portfolio.DoesNotExist:
            return Response({'error': 'No holdings for this asset'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        return Response({'error': 'Cannot delete transactions'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        return Response({'error': 'Cannot update transactions'}, status=status.HTTP_403_FORBIDDEN)


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return models.Company.objects.all()

    def create(self, request, *args, **kwargs):
        """Create a company (TODO: add unlock requirements)"""
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Company name required'}, status=status.HTTP_400_BAD_REQUEST)

        company = models.Company.objects.create(owner=request.user, name=name)
        serializer = self.get_serializer(company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        company = self.get_object()
        if company.owner != request.user:
            return Response({'error': 'Only owner can delete company'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def issue_asset(self, request, pk=None):
        company = self.get_object()
        if company.owner != request.user:
            return Response({'error': 'Only owner can issue assets'}, status=status.HTTP_403_FORBIDDEN)
        
        name = request.data.get('name', '').strip()
        category_id = request.data.get('category_id')
        base_price = request.data.get('base_price', '10.00')
        total_supply = request.data.get('total_supply', '1000')
        
        if not name or not category_id:
            return Response({'error': 'name and category_id are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            category = models.AssetCategory.objects.get(id=category_id)
        except models.AssetCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
            
        asset = models.Asset.objects.create(
            name=name,
            category=category,
            company=company,
            created_by=request.user,
            base_price=Decimal(str(base_price)),
            current_price=Decimal(str(base_price)),
            total_supply=Decimal(str(total_supply)),
            available_supply=Decimal(str(total_supply))
        )
        
        return Response(serializers.AssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class MarketEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.MarketEvent.objects.all()
    serializer_class = serializers.MarketEventSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.LedgerEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return models.LedgerEntry.objects.filter(user=self.request.user).order_by('-timestamp')


from django.db.models import Sum, F, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from users.models import User, Wallet

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def users_by_networth(request):
    """
    Calculate and return the top 100 users by net worth.
    Net worth = USD Wallet Balance + Sum(Portfolio Qty * Asset Current Price)
    """
    # Subquery for USD balance
    usd_balance_sq = Wallet.objects.filter(
        user=OuterRef('pk'), 
        currency='USD'
    ).values('balance')[:1]

    # Subquery for Portfolio value
    portfolio_value_sq = models.Portfolio.objects.filter(
        user=OuterRef('pk')
    ).values('user').annotate(
        total=Sum(F('quantity') * F('asset__current_price'), output_field=DecimalField())
    ).values('total')

    users = User.objects.annotate(
        usd_balance=Coalesce(Subquery(usd_balance_sq), Decimal('0.00'), output_field=DecimalField()),
        portfolio_val=Coalesce(Subquery(portfolio_value_sq), Decimal('0.00'), output_field=DecimalField())
    ).annotate(
        calc_net_worth=F('usd_balance') + F('portfolio_val')
    ).order_by('-calc_net_worth')[:100]
    
    leaderboard = []
    for i, user in enumerate(users):
        leaderboard.append({
            'username': user.username,
            'net_worth': float(user.calc_net_worth),
            'rank': i + 1,
        })
        
    return Response(leaderboard)

