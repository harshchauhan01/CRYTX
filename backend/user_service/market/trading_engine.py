"""
market/trading_engine.py

Core trade execution engine for CRYTX.

Architecture:
  - The @transaction.atomic block does ONLY the minimum required work:
      1. Validate and lock the Asset row (supply check)
      2. Validate and lock the Wallet row (balance check)
      3. Update the Wallet balance (debit/credit)
      4. Update Asset available_supply
      5. Write the Transaction ledger entry
  - Everything else (portfolio WAP, price recalculation) is dispatched
    as a Celery task via transaction.on_commit() so it fires ONLY after
    the DB commit succeeds and never holds the row locks.

  In dev (CELERY_TASK_ALWAYS_EAGER=True) on_commit callbacks run
  synchronously after the outer transaction ends, so behaviour is identical
  to the old implementation — just structurally decoupled.
"""

from decimal import Decimal
from django.db import transaction
from .models import Asset, Transaction


@transaction.atomic
def execute_buy(user, asset_id, quantity, idempotency_key=None):
    """
    Execute a BUY order atomically.

    Critical path (inside transaction):
      - Idempotency gate
      - Asset supply validation + lock
      - Slippage calculation
      - Wallet balance deduction + lock
      - Asset supply update
      - Transaction record creation

    Post-commit (async tasks):
      - Portfolio WAP update
      - Price recalculation + cache push
    """
    # ── Idempotency gate ──────────────────────────────────────────────────────
    if idempotency_key:
        existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

    quantity = Decimal(str(quantity))
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    # ── Lock asset row ────────────────────────────────────────────────────────
    asset = Asset.objects.select_for_update().get(id=asset_id, is_active=True)

    if asset.available_supply < quantity:
        raise ValueError("Insufficient available supply")

    # ── Slippage (linear, proportional to order size vs total supply) ─────────
    if asset.total_supply > 0:
        slippage_factor = Decimal('1') + (quantity / asset.total_supply)
    else:
        slippage_factor = Decimal('1')

    effective_price = asset.current_price * slippage_factor
    total_cost = effective_price * quantity

    # ── Lock wallet + deduct balance ──────────────────────────────────────────
    from users.models import Wallet
    locked_wallet = Wallet.objects.select_for_update().get(user=user, currency='USD')

    if locked_wallet.balance < total_cost:
        raise ValueError("Insufficient balance")

    locked_wallet.balance -= total_cost
    locked_wallet.save()

    # ── Update asset supply (price recalc happens async) ──────────────────────
    asset.available_supply -= quantity
    asset.save(update_fields=['available_supply'])

    # ── Write ledger entry ────────────────────────────────────────────────────
    txn = Transaction.objects.create(
        user=user,
        asset=asset,
        transaction_type=Transaction.TRANSACTION_BUY,
        quantity=quantity,
        price=effective_price,
        idempotency_key=idempotency_key,
    )

    # ── Dispatch async tasks (fire only after commit) ─────────────────────────
    # If the transaction rolls back, these callbacks never run.
    _user_id = user.id
    _asset_id = asset.id
    _qty = str(quantity)
    _price = str(effective_price)

    def _dispatch():
        from .tasks import update_portfolio_task, recalculate_price_task
        update_portfolio_task.delay(_user_id, _asset_id, _qty, _price, 'buy')
        recalculate_price_task.delay(_asset_id, _qty, '0')

    transaction.on_commit(_dispatch)

    return txn


@transaction.atomic
def execute_sell(user, asset_id, quantity, idempotency_key=None):
    """
    Execute a SELL order atomically.

    Same architecture as execute_buy — minimal critical path,
    portfolio + price work dispatched post-commit.
    """
    # ── Idempotency gate ──────────────────────────────────────────────────────
    if idempotency_key:
        existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

    quantity = Decimal(str(quantity))
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    # ── Validate holdings BEFORE locking anything else ────────────────────────
    # This catches "no holdings" errors early without acquiring locks.
    from .models import Portfolio
    try:
        holding = Portfolio.objects.get(user=user, asset_id=asset_id)
    except Portfolio.DoesNotExist:
        raise ValueError("No holdings for this asset")

    if holding.quantity < quantity:
        raise ValueError("Insufficient holdings to sell")

    # ── Lock asset row ────────────────────────────────────────────────────────
    asset = Asset.objects.select_for_update().get(id=asset_id, is_active=True)

    # ── Lock wallet ────────────────────────────────────────────────────────────
    from users.models import Wallet
    locked_wallet = Wallet.objects.select_for_update().get(user=user, currency='USD')

    # ── Slippage ───────────────────────────────────────────────────────────────
    if asset.total_supply > 0:
        slippage_factor = Decimal('1') - (quantity / asset.total_supply)
    else:
        slippage_factor = Decimal('1')

    if slippage_factor < Decimal('0.01'):
        slippage_factor = Decimal('0.01')

    effective_price = asset.current_price * slippage_factor
    total_revenue = effective_price * quantity

    # ── Credit wallet ──────────────────────────────────────────────────────────
    locked_wallet.balance += total_revenue
    locked_wallet.save()

    # ── Update asset supply ────────────────────────────────────────────────────
    asset.available_supply += quantity
    asset.save(update_fields=['available_supply'])

    # ── Write ledger entry ─────────────────────────────────────────────────────
    txn = Transaction.objects.create(
        user=user,
        asset=asset,
        transaction_type=Transaction.TRANSACTION_SELL,
        quantity=quantity,
        price=effective_price,
        idempotency_key=idempotency_key,
    )

    # ── Dispatch async tasks (fire only after commit) ──────────────────────────
    _user_id = user.id
    _asset_id = asset.id
    _qty = str(quantity)
    _price = str(effective_price)

    def _dispatch():
        from .tasks import update_portfolio_task, recalculate_price_task
        update_portfolio_task.delay(_user_id, _asset_id, _qty, _price, 'sell')
        recalculate_price_task.delay(_asset_id, '0', _qty)

    transaction.on_commit(_dispatch)

    return txn
