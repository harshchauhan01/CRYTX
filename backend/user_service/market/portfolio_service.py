from decimal import Decimal
from django.db import transaction
from .models import Portfolio

@transaction.atomic
def update_portfolio_on_buy(user, asset, quantity, price):
    # Lock the row to prevent concurrent task runs racing on WAP calculation
    portfolio, created = Portfolio.objects.select_for_update().get_or_create(
        user=user, asset=asset
    )

    if created or portfolio.quantity == 0:
        portfolio.avg_buy_price = price
    else:
        old_qty = portfolio.quantity
        old_avg = portfolio.avg_buy_price
        portfolio.avg_buy_price = ((old_qty * old_avg) + (quantity * price)) / (old_qty + quantity)

    portfolio.quantity += quantity
    portfolio.save()
    return portfolio

def update_portfolio_on_sell(user, asset, quantity, price):
    portfolio = Portfolio.objects.select_for_update().get(user=user, asset=asset)
    
    if portfolio.quantity < quantity:
        raise ValueError("Insufficient holdings to sell")
        
    # Do not change avg_buy_price on sell
    realized_profit = (price - portfolio.avg_buy_price) * quantity
    
    portfolio.quantity -= quantity
    portfolio.save()
    
    return portfolio, realized_profit
