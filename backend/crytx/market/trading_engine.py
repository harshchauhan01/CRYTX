"""
CRYTX — Atomic Trading Engine
Handles buy/sell execution with slippage, fees, and balance checks.
All operations use select_for_update() for transactional safety.
"""

from decimal import Decimal
from django.db import transaction
from django.conf import settings
from .models import Asset, Portfolio, Transaction
from users.models import Wallet


TRADE_FEE_PCT = Decimal(str(getattr(settings, 'CRYTX_TRADE_FEE_PCT', 0.5)))


class TradeError(Exception):
    """Raised when a trade cannot be executed."""
    pass


def calculate_slippage(asset, quantity, trade_type):
    """
    Calculate slippage based on trade size relative to supply.
    Larger trades move the price more.
    """
    supply = max(asset.total_supply, 1)
    impact = float(quantity) / supply
    slippage = Decimal(str(min(impact * 10, 0.05)))  # Max 5% slippage

    if trade_type == 'BUY':
        return asset.current_price * (1 + slippage)
    else:
        return asset.current_price * (1 - slippage)


@transaction.atomic
def execute_buy(user, asset_id, quantity):
    """
    Execute a BUY order atomically.
    - Locks wallet and asset rows
    - Calculates slippage-adjusted price
    - Deducts balance including fees
    - Updates portfolio and volumes
    """
    quantity = Decimal(str(quantity))
    if quantity <= 0:
        raise TradeError("Quantity must be greater than zero.")

    # Lock rows for atomic operation
    wallet = Wallet.objects.select_for_update().get(user=user)
    asset = Asset.objects.select_for_update().get(id=asset_id, is_active=True)

    # Calculate execution price with slippage
    exec_price = calculate_slippage(asset, quantity, 'BUY')
    subtotal = exec_price * quantity
    fee = subtotal * TRADE_FEE_PCT / 100
    total_cost = subtotal + fee

    # Balance check
    if wallet.balance < total_cost:
        raise TradeError(
            f"Insufficient balance. Need {total_cost:.2f} Ç, have {wallet.balance:.2f} Ç."
        )

    # Deduct balance
    wallet.balance -= total_cost
    wallet.save(update_fields=['balance'])

    # Update or create portfolio entry
    portfolio, created = Portfolio.objects.get_or_create(
        user=user, asset=asset,
        defaults={'quantity': 0, 'avg_buy_price': 0}
    )
    # Update weighted average buy price
    old_value = portfolio.quantity * portfolio.avg_buy_price
    new_value = quantity * exec_price
    portfolio.quantity += quantity
    if portfolio.quantity > 0:
        portfolio.avg_buy_price = (old_value + new_value) / portfolio.quantity
    portfolio.save(update_fields=['quantity', 'avg_buy_price'])

    # Update asset volumes
    asset.buy_volume += int(quantity)
    asset.circulating_supply += int(quantity)
    asset.save(update_fields=['buy_volume', 'circulating_supply'])

    # Update user stats
    user.total_trades += 1
    user.save(update_fields=['total_trades'])

    # Record transaction
    txn = Transaction.objects.create(
        user=user,
        asset=asset,
        trade_type='BUY',
        quantity=quantity,
        price_at_trade=exec_price,
        total_cost=total_cost,
        fee=fee,
    )

    return {
        'transaction_id': txn.id,
        'type': 'BUY',
        'asset': asset.ticker,
        'quantity': float(quantity),
        'price': float(exec_price),
        'fee': float(fee),
        'total_cost': float(total_cost),
        'new_balance': float(wallet.balance),
    }


@transaction.atomic
def execute_sell(user, asset_id, quantity):
    """
    Execute a SELL order atomically.
    - Locks wallet, portfolio, and asset rows
    - Checks sufficient holdings
    - Calculates slippage-adjusted price
    - Credits balance minus fees
    """
    quantity = Decimal(str(quantity))
    if quantity <= 0:
        raise TradeError("Quantity must be greater than zero.")

    wallet = Wallet.objects.select_for_update().get(user=user)
    asset = Asset.objects.select_for_update().get(id=asset_id, is_active=True)

    try:
        portfolio = Portfolio.objects.select_for_update().get(user=user, asset=asset)
    except Portfolio.DoesNotExist:
        raise TradeError("You don't own any of this asset.")

    if portfolio.quantity < quantity:
        raise TradeError(
            f"Insufficient holdings. Have {portfolio.quantity}, trying to sell {quantity}."
        )

    # Calculate execution price with slippage
    exec_price = calculate_slippage(asset, quantity, 'SELL')
    subtotal = exec_price * quantity
    fee = subtotal * TRADE_FEE_PCT / 100
    total_revenue = subtotal - fee

    # Credit balance
    wallet.balance += total_revenue
    wallet.save(update_fields=['balance'])

    # Update portfolio
    portfolio.quantity -= quantity
    if portfolio.quantity == 0:
        portfolio.delete()
    else:
        portfolio.save(update_fields=['quantity'])

    # Update asset volumes
    asset.sell_volume += int(quantity)
    asset.circulating_supply = max(0, asset.circulating_supply - int(quantity))
    asset.save(update_fields=['sell_volume', 'circulating_supply'])

    # Track profit
    profit = (exec_price - portfolio.avg_buy_price) * quantity
    if profit > 0:
        user.total_earned += profit
    user.total_trades += 1
    user.save(update_fields=['total_earned', 'total_trades'])

    # Record transaction
    txn = Transaction.objects.create(
        user=user,
        asset=asset,
        trade_type='SELL',
        quantity=quantity,
        price_at_trade=exec_price,
        total_cost=total_revenue,
        fee=fee,
    )

    return {
        'transaction_id': txn.id,
        'type': 'SELL',
        'asset': asset.ticker,
        'quantity': float(quantity),
        'price': float(exec_price),
        'fee': float(fee),
        'total_revenue': float(total_revenue),
        'new_balance': float(wallet.balance),
    }
