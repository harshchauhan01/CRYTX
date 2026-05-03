"""
market/tasks.py

Async Celery tasks for CRYTX.

These run *after* the DB transaction commits via transaction.on_commit(),
so they never hold the row locks that the core trade execution needs.

In development (CELERY_TASK_ALWAYS_EAGER = True) they run synchronously
in-process — no separate worker required.

In production, point CELERY_BROKER_URL at a real Redis instance and
start workers with: celery -A user_service worker -l info
"""

from celery import shared_task
from django.core.cache import cache
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def update_portfolio_task(self, user_id: int, asset_id: int, quantity: str, price: str, side: str):
    """
    Asynchronously update a user's portfolio position after a trade executes.

    Decoupled from the critical trade path so it does NOT hold wallet/asset
    row locks while doing the portfolio arithmetic.

    Args:
        user_id:  PK of the trading user
        asset_id: PK of the traded asset
        quantity: Trade quantity (passed as str to avoid float serialisation issues)
        price:    Execution price (str)
        side:     'buy' or 'sell'
    """
    try:
        from django.contrib.auth import get_user_model
        from .models import Asset, Portfolio

        User = get_user_model()
        quantity = Decimal(quantity)
        price = Decimal(price)

        user = User.objects.get(pk=user_id)
        asset = Asset.objects.get(pk=asset_id)

        if side == 'buy':
            portfolio, created = Portfolio.objects.get_or_create(user=user, asset=asset)

            if created or portfolio.quantity == 0:
                portfolio.avg_buy_price = price
            else:
                old_qty = portfolio.quantity
                old_avg = portfolio.avg_buy_price
                portfolio.avg_buy_price = (
                    (old_qty * old_avg) + (quantity * price)
                ) / (old_qty + quantity)

            portfolio.quantity += quantity
            portfolio.save()
            logger.info(
                "Portfolio updated (buy): user=%s asset=%s qty=%s avg=%s",
                user_id, asset_id, portfolio.quantity, portfolio.avg_buy_price
            )

        elif side == 'sell':
            try:
                portfolio = Portfolio.objects.get(user=user, asset=asset)
                # WAP stays the same on sell; realized P&L is informational only
                portfolio.quantity -= quantity
                if portfolio.quantity < 0:
                    # Shouldn't happen — trading_engine validates before executing
                    logger.error(
                        "Portfolio quantity went negative: user=%s asset=%s",
                        user_id, asset_id
                    )
                    portfolio.quantity = Decimal('0')
                portfolio.save()
                logger.info(
                    "Portfolio updated (sell): user=%s asset=%s qty=%s",
                    user_id, asset_id, portfolio.quantity
                )
            except Portfolio.DoesNotExist:
                logger.error(
                    "Portfolio not found for sell: user=%s asset=%s",
                    user_id, asset_id
                )

    except Exception as exc:
        logger.error("update_portfolio_task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def recalculate_price_task(self, asset_id: int, buy_delta: str, sell_delta: str):
    """
    Asynchronously recalculate an asset's price and push it to the Django
    cache so that subsequent reads (leaderboards, portfolio values) are fast
    without hitting the DB.

    The cache key format is: market:price:<asset_id>
    TTL = 60 seconds — stale prices are automatically evicted.

    Args:
        asset_id:   PK of the asset to reprice
        buy_delta:  Volume bought in this trade (str)
        sell_delta: Volume sold in this trade (str)
    """
    try:
        from .models import Asset
        from .pricing_engine import calculate_new_price

        buy_delta = Decimal(buy_delta)
        sell_delta = Decimal(sell_delta)

        asset = Asset.objects.get(pk=asset_id)

        # Accumulate volume into the asset's running totals
        asset.buy_volume += buy_delta
        asset.sell_volume += sell_delta

        new_price = calculate_new_price(asset)
        asset.current_price = new_price
        asset.save(update_fields=['current_price', 'buy_volume', 'sell_volume'])

        from .models import PriceHistory
        PriceHistory.objects.create(asset=asset, price=new_price)

        # Push the fresh price into the cache for fast reads
        cache_key = f'market:price:{asset_id}'
        cache.set(cache_key, str(new_price), timeout=60)

        logger.info(
            "Price recalculated: asset=%s new_price=%s",
            asset_id, new_price
        )
        return str(new_price)

    except Exception as exc:
        logger.error("recalculate_price_task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ═══════════════════════════════════════════════════════════════════════════════
# CHAOS ENGINE TASKS
# These are scheduled by Celery Beat (configured in settings.py CELERY_BEAT_SCHEDULE).
# They run on a fixed interval to drive the living, breathing market simulation.
# ═══════════════════════════════════════════════════════════════════════════════

@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def apply_events_task(self):
    """
    Celery Beat task — runs every 30 seconds.

    Lifecycle manager for MarketEvent rows:

    1. ACTIVATE: Find events whose scheduled_at <= now and not yet executed.
       - Apply supply_shock (one-time add/remove from available_supply)
       - Write demand_multiplier and volatility_multiplier into the asset's
         event_multiplier field (read by the pricing engine each tick)
       - For global events (target_asset=None), apply to ALL active assets

    2. EXPIRE: Find events whose expires_at <= now and executed but not expired.
       - Reset the asset's event_multiplier back to 1.0
       - Mark the event as expired

    This means events influence the market through the pricing engine formula,
    not by directly setting prices — preserving mathematical consistency.
    """
    try:
        from django.utils import timezone
        from .models import Asset, MarketEvent

        now = timezone.now()

        # ── Phase 1: Activate due events ──────────────────────────────────────
        due_events = MarketEvent.objects.filter(
            scheduled_at__lte=now,
            executed=False,
            expired=False,
        ).select_related('target_asset')

        for event in due_events:
            targets = (
                Asset.objects.filter(is_active=True, id=event.target_asset_id)
                if event.target_asset_id
                else Asset.objects.filter(is_active=True)
            )

            for asset in targets:
                # Apply one-time supply shock
                if event.supply_shock != 0:
                    asset.available_supply = max(
                        Decimal('0'),
                        asset.available_supply + event.supply_shock
                    )

                # Write event multiplier so pricing engine picks it up next tick.
                # We combine demand and volatility into the single event_multiplier
                # field.  The pricing engine uses it as E in:
                #   delta = price * (net_pressure / L_eff) * V * E
                asset.event_multiplier = float(
                    event.demand_multiplier * event.volatility_multiplier
                )
                asset.volatility = min(
                    asset.volatility * event.volatility_multiplier,
                    2.0  # Hard cap so volatility can't go infinite
                )
                asset.save(update_fields=['available_supply', 'event_multiplier', 'volatility'])

            event.executed = True
            event.activated_at = now
            event.save(update_fields=['executed', 'activated_at'])

            logger.info(
                "MarketEvent ACTIVATED: [%s] '%s' (target=%s, multiplier=%.2f)",
                event.effect_type, event.title,
                event.target_asset or 'ALL', event.demand_multiplier
            )

        # ── Phase 2: Expire elapsed events ────────────────────────────────────
        elapsed_events = MarketEvent.objects.filter(
            expires_at__lte=now,
            executed=True,
            expired=False,
        ).select_related('target_asset')

        for event in elapsed_events:
            targets = (
                Asset.objects.filter(is_active=True, id=event.target_asset_id)
                if event.target_asset_id
                else Asset.objects.filter(is_active=True)
            )

            for asset in targets:
                # Reset event pressure — market returns to organic state
                asset.event_multiplier = 1.0
                # Restore original volatility (stored in base; approximate here)
                asset.volatility = max(asset.volatility / event.volatility_multiplier, 0.01)
                asset.save(update_fields=['event_multiplier', 'volatility'])

            event.expired = True
            event.save(update_fields=['expired'])

            logger.info(
                "MarketEvent EXPIRED: [%s] '%s'",
                event.effect_type, event.title
            )

    except Exception as exc:
        logger.error("apply_events_task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def price_tick_task(self):
    """
    Celery Beat task — runs every 10 seconds.

    Drives organic market noise even when no trades are happening.
    Without this, prices would be perfectly static between trades,
    making the market feel dead and creating obvious arbitrage windows
    by letting players predict exact prices.

    For each active asset that is NOT circuit-breaker-tripped:
    - Calls calculate_new_price() with zero net pressure (noise-only tick)
    - Pushes updated price to DB and Django cache
    - Resets buy_volume / sell_volume accumulators so the next trade
      sees fresh relative pressure rather than accumulated history
    """
    try:
        from .models import Asset
        from .pricing_engine import calculate_new_price
        from django.core.cache import cache

        assets = Asset.objects.filter(
            is_active=True,
            circuit_breaker_tripped=False,
        )

        for asset in assets:
            # Zero out volumes for a noise-only tick (no accumulated pressure)
            asset.buy_volume  = Decimal('0')
            asset.sell_volume = Decimal('0')

            new_price = calculate_new_price(asset)
            asset.current_price = new_price
            asset.save(update_fields=[
                'current_price', 'buy_volume', 'sell_volume', 'circuit_breaker_tripped'
            ])

            from .models import PriceHistory
            PriceHistory.objects.create(asset=asset, price=new_price)

            cache_key = f'market:price:{asset.id}'
            cache.set(cache_key, str(new_price), timeout=30)

        logger.debug("price_tick_task: ticked %d assets", assets.count())

    except Exception as exc:
        logger.error("price_tick_task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)
