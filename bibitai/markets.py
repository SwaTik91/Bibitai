from __future__ import annotations

from decimal import Decimal
from math import pi, sin

from bibitai.models import Candle


def _candle(index: int, price: Decimal, low: Decimal, high: Decimal) -> Candle:
    open_price = price if index == 0 else price
    return Candle(
        open_time=index,
        open=open_price,
        high=max(high, price),
        low=min(low, price),
        close=price,
        volume=Decimal("1"),
    )


def flat_candles(price: Decimal, bars: int) -> list[Candle]:
    return [_candle(index, price, price, price) for index in range(bars)]


def ranging_sine_candles(
    start: Decimal,
    bars: int,
    amplitude: Decimal,
    period: int = 48,
) -> list[Candle]:
    candles: list[Candle] = []
    previous = start
    for index in range(bars):
        price = start + amplitude * Decimal(str(sin(2 * pi * index / period)))
        low = min(previous, price)
        high = max(previous, price)
        # Give each bar a little body so grid levels inside the swing can fill.
        swing = abs(price - previous)
        pad = max(swing / Decimal("2"), Decimal("40"))
        candles.append(_candle(index, price, low - pad, high + pad))
        previous = price
    return candles


def trending_down_candles(start: Decimal, bars: int, drop: Decimal) -> list[Candle]:
    step = drop / Decimal(bars)
    candles: list[Candle] = []
    price = start
    for index in range(bars):
        nxt = start - step * Decimal(index + 1)
        candles.append(_candle(index, nxt, nxt, price))
        price = nxt
    return candles
