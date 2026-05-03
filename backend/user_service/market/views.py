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


class HoldingViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.HoldingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return models.Holding.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        return Response({'error': 'Cannot create holdings directly. Use /orders/ endpoint.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def portfolio_value(self, request):
        """Calculate total portfolio value"""
        holdings = self.get_queryset()
        total_value = sum(h.quantity * h.asset.current_price for h in holdings)
        user_balance = request.user.balance
        net_worth = Decimal(total_value) + user_balance
        return Response({
            'total_holdings_value': float(total_value),
            'cash_balance': float(user_balance),
            'net_worth': float(net_worth)
        })


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return models.Order.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Place a buy or sell order with atomic transaction"""
        asset_id = request.data.get('asset_id')
        quantity = Decimal(str(request.data.get('quantity', 0)))
        side = request.data.get('side', '').lower()

        if not asset_id or not quantity or side not in ['buy', 'sell']:
            return Response({'error': 'Invalid asset_id, quantity, or side'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Lock asset row to prevent race conditions
                asset = models.Asset.objects.select_for_update().get(id=asset_id, is_active=True)

                # execution price is the price at which this trade occurs
                execution_price = asset.current_price

                if side == 'buy':
                    total_cost = quantity * execution_price
                    if request.user.balance < total_cost:
                        return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

                    # Deduct crystals from user
                    request.user.balance -= total_cost
                    request.user.save()

                    # Update holding
                    holding, _ = models.Holding.objects.get_or_create(user=request.user, asset=asset)
                    if holding.quantity == 0:
                        holding.avg_price = asset.current_price
                    else:
                        holding.avg_price = (holding.quantity * holding.avg_price + quantity * asset.current_price) / (holding.quantity + quantity)
                    holding.quantity += quantity
                    holding.save()

                    # Update asset supply/demand
                    asset.supply -= quantity
                    asset.demand += quantity

                elif side == 'sell':
                    holding = models.Holding.objects.get(user=request.user, asset=asset)
                    if holding.quantity < quantity:
                        return Response({'error': 'Insufficient holdings'}, status=status.HTTP_400_BAD_REQUEST)

                    total_revenue = quantity * asset.current_price
                    request.user.balance += total_revenue
                    request.user.save()

                    holding.quantity -= quantity
                    if holding.quantity == 0:
                        holding.delete()
                    else:
                        holding.save()

                    asset.supply += quantity
                    asset.demand -= quantity

                # after adjusting supply/demand, compute new price based on imbalance and volatility
                try:
                    # use Decimal for precision
                    supply = Decimal(asset.supply)
                    demand = Decimal(asset.demand)
                    total = supply + demand
                    imbalance = demand - supply
                    vol = Decimal(str(asset.volatility)) if asset.volatility is not None else Decimal('0')

                    if total <= 0:
                        delta = Decimal('0')
                    else:
                        # proportion in [-1,1]
                        prop = imbalance / (total + Decimal(1))
                        # delta is proportional to volatility and imbalance
                        delta = vol * prop

                    # clamp delta to reasonable bounds [-0.2, 0.2]
                    max_move = Decimal('0.2')
                    if delta > max_move:
                        delta = max_move
                    if delta < -max_move:
                        delta = -max_move

                    new_price = (execution_price * (Decimal(1) + delta)).quantize(Decimal('0.01'))
                    if new_price <= 0:
                        new_price = Decimal('0.01')

                    asset.current_price = new_price
                except Exception:
                    # fallback: keep current price unchanged
                    pass

                asset.save()

                # Create order record
                order = models.Order.objects.create(
                    user=request.user,
                    asset=asset,
                    quantity=quantity,
                    price=execution_price,
                    side=side,
                    status=models.Order.STATUS_COMPLETED,
                    completed_at=timezone.now()
                )

                # Log to ledger
                models.LedgerEntry.objects.create(
                    user=request.user,
                    asset=asset,
                    change=total_cost if side == 'buy' else total_revenue,
                    balance_after=request.user.balance,
                    note=f"{side.upper()} {quantity} {asset.name} @ {execution_price}"
                )

                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except models.Asset.DoesNotExist:
            return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)
        except models.Holding.DoesNotExist:
            return Response({'error': 'No holdings for this asset'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        return Response({'error': 'Cannot delete orders'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        return Response({'error': 'Cannot update orders'}, status=status.HTTP_403_FORBIDDEN)


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
