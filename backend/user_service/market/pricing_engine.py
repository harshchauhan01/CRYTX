"""
market/pricing_engine.py

Production-grade AMM Pricing Engine for CRYTX.

Formula (from System Design):
    P(t+1) = P(t) * (1 + (net_pressure / L_eff) * V * E) + noise

Where:
  net_pressure = (ΔD - ΔS) / total_supply
                 Normalized net demand this tick.

  L_eff = base_liquidity_resistance * (1 + exp(k * price_deviation))
           Exponential resistance that grows as price deviates from base.
           Prevents whales from pumping a coin to infinity — each unit of
           price deviation makes the next unit exponentially more expensive.
           k=0.05 means a 100% price increase from base doubles resistance.

  V  = asset.volatility  (0.0 – 2.0)
       Per-asset sensitivity scalar set at seeding time.

  E  = event_multiplier   (applied to the whole delta, not just pressure)
       Sourced from asset.event_multiplier (written by apply_events_task).

  noise = Gaussian-distributed N(0, σ) where σ = V * P * noise_scale
          Simulates organic market jitter and prevents deterministic arbitrage.
          Uses Decimal-safe random to avoid float precision corruption.

Hard Guards:
  - Circuit Breaker: if |ΔP/P| > 15% in one tick → return clamped price
    AND set asset.circuit_breaker_tripped = True (halts further trading).
  - Absolute Floor: price never goes below minimum_price (default 0.01).
  - Slippage in buy/sell is separate from this engine (handled in trading_engine.py).
"""

import math
import random
from decimal import Decimal, ROUND_HALF_UP

# ── Tuneable constants ─────────────────────────────────────────────────────────
BASE_LIQUIDITY_RESISTANCE = Decimal('50')   # denominator at zero deviation
DEVIATION_SENSITIVITY     = Decimal('0.05') # k — exponential growth rate
NOISE_SCALE               = Decimal('0.005') # σ multiplier (0.5% of price per tick)
CIRCUIT_BREAKER_THRESHOLD = Decimal('0.15') # 15% single-tick move → halt
MINIMUM_PRICE             = Decimal('0.01')


def _clamp(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    return max(lo, min(value, hi))


def _gaussian_noise(volatility: Decimal, price: Decimal) -> Decimal:
    """
    Generate Gaussian noise N(0, σ) where σ = volatility * price * NOISE_SCALE.
    Uses Box-Muller so we don't need scipy, keeps everything in Decimal.
    """
    u1 = random.random()
    u2 = random.random()
    # Box-Muller transform → standard normal
    z = math.sqrt(-2.0 * math.log(max(u1, 1e-10))) * math.cos(2.0 * math.pi * u2)
    sigma = volatility * price * NOISE_SCALE
    return sigma * Decimal(str(round(z, 8)))


def calculate_new_price(asset, minimum_price: Decimal = MINIMUM_PRICE) -> Decimal:
    """
    Compute the next price tick for `asset` using the exponential AMM formula.

    This function is called by `recalculate_price_task` (async, post-commit).
    It reads the asset's running buy_volume and sell_volume accumulators which
    are incremented per-trade by the Celery task, NOT the atomic transaction.

    Edge-case handling:
      - Zero supply: no price movement, return current price.
      - Circuit breaker already tripped: return current price (trading halted).
      - Negative effective price after noise: floor at minimum_price.
    """
    price = asset.current_price

    # Guard: zero supply — price is undefined, don't move it.
    if asset.total_supply <= 0:
        return price

    # Guard: circuit breaker already tripped — don't recalculate until cleared.
    if asset.circuit_breaker_tripped:
        return price

    # ── Net pressure ───────────────────────────────────────────────────────────
    # Normalize by total_supply so a 10-unit order means the same thing
    # whether total supply is 100 or 1,000,000.
    net_pressure = (asset.buy_volume - asset.sell_volume) / asset.total_supply

    # ── Exponential Liquidity Resistance (L_eff) ───────────────────────────────
    # L_eff grows exponentially as price deviates from base_price.
    # This makes large pumps self-defeating: the higher the price, the more
    # capital is required to move it by the same percentage.
    #
    #   L_eff = BASE_RESISTANCE * (1 + exp(k * |price - base| / base))
    #
    # Example: base=100, current=200 → 100% deviation
    #   exp(0.05 * 1.0) ≈ 1.051 → L_eff ≈ 50 * 2.051 ≈ 102.5
    # vs base=100, current=100 → L_eff = 50 * 2.0 = 100
    if asset.base_price > 0:
        price_deviation = abs(price - asset.base_price) / asset.base_price
    else:
        price_deviation = Decimal('0')

    exp_factor = Decimal(str(math.exp(float(DEVIATION_SENSITIVITY * price_deviation))))
    l_eff = BASE_LIQUIDITY_RESISTANCE * (Decimal('1') + exp_factor)

    # ── Volatility scalar ──────────────────────────────────────────────────────
    V = Decimal(str(asset.volatility))

    # ── Event multiplier (injected by apply_events_task) ──────────────────────
    E = Decimal(str(asset.event_multiplier))

    # ── Core delta ─────────────────────────────────────────────────────────────
    delta = price * (net_pressure / l_eff) * V * E

    # ── Gaussian noise ─────────────────────────────────────────────────────────
    noise = _gaussian_noise(V, price)

    new_price = price + delta + noise

    # ── Circuit Breaker ────────────────────────────────────────────────────────
    # If the price would move more than 15% in a single tick, clamp it
    # and flag the asset for a trading halt.  The flag is cleared manually
    # by an admin (or an automated cooldown task after N seconds).
    if price > 0:
        pct_change = abs(new_price - price) / price
        if pct_change > CIRCUIT_BREAKER_THRESHOLD:
            # Clamp to exactly ±15% and trip the breaker
            direction = Decimal('1') if new_price > price else Decimal('-1')
            new_price = price * (Decimal('1') + direction * CIRCUIT_BREAKER_THRESHOLD)
            asset.circuit_breaker_tripped = True

    # ── Absolute floor ─────────────────────────────────────────────────────────
    new_price = max(new_price, minimum_price)

    return new_price.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
