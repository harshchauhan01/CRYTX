from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
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
        portfolios = self.get_queryset()
        total_value = sum(p.quantity * p.asset.current_price for p in portfolios)
        
        from users.models import Wallet
        user_wallet = Wallet.objects.filter(user=request.user, currency='USD').first()
        user_balance = user_wallet.balance if user_wallet else Decimal('0.00')
        
        net_worth = Decimal(total_value) + user_balance
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
