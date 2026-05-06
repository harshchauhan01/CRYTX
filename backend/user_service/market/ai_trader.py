import random
import logging
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from market.models import Asset, Portfolio
from users.models import Wallet
from market.trading_engine import execute_buy, execute_sell

logger = logging.getLogger(__name__)
User = get_user_model()

NUM_BOTS = 5

def initialize_bots():
    """Ensure bot accounts exist and have starting capital."""
    bots = []
    for i in range(1, NUM_BOTS + 1):
        username = f"AITrader_{i}"
        email = f"ai_trader_{i}@crytx.local"
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        if created:
            user.set_unusable_password()
            user.save()
            Wallet.objects.get_or_create(user=user, currency='USD', defaults={'balance': Decimal('100000.00')})
            logger.info(f"Created new AI bot: {username}")
        bots.append(user)
    return bots

def ai_trader_tick():
    """
    Executes a random trade for one of the bots.
    Called periodically by run_market_loop.py.
    """
    bots = initialize_bots()
    if not bots:
        return
        
    bot = random.choice(bots)
    assets = list(Asset.objects.filter(is_active=True, circuit_breaker_tripped=False))
    if not assets:
        return
        
    asset = random.choice(assets)
    
    # Decide buy or sell
    holdings = Portfolio.objects.filter(user=bot, asset=asset).first()
    can_sell = holdings is not None and holdings.quantity >= Decimal('1')
    
    side = 'sell' if (can_sell and random.random() > 0.5) else 'buy'
    
    if side == 'buy':
        max_qty = float(asset.available_supply) * 0.05
        if max_qty < 1:
            max_qty = 1
        qty_to_trade = Decimal(str(round(random.uniform(1, min(100, max_qty)), 4)))
    else:
        max_qty = float(holdings.quantity)
        qty_to_trade = Decimal(str(round(random.uniform(1, max_qty), 4)))
        
    idemp_key = str(uuid.uuid4())
    
    try:
        if side == 'buy':
            execute_buy(bot, asset.id, qty_to_trade, idemp_key)
            logger.info(f"AI {bot.username} BOUGHT {qty_to_trade} {asset.name}")
        else:
            execute_sell(bot, asset.id, qty_to_trade, idemp_key)
            logger.info(f"AI {bot.username} SOLD {qty_to_trade} {asset.name}")
    except Exception as e:
        logger.debug(f"AI {bot.username} failed to {side} {asset.name}: {e}")
