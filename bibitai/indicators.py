from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from bibitai.models import Candle


def ema(values: Sequence[float], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return [None] * len(values)

    k = 2.0 / (period + 1)
    out: list[float | None] = [None] * (period - 1)
    seed = sum(values[:period]) / period
    out.append(seed)
    previous = seed
    for value in values[period:]:
        previous = value * k + previous * (1.0 - k)
        out.append(previous)
    return out


def _true_range(previous_close: Decimal, candle: Candle) -> float:
    high_low = float(candle.high - candle.low)
    high_close = abs(float(candle.high - previous_close))
    low_close = abs(float(candle.low - previous_close))
    return max(high_low, high_close, low_close)


def atr(candles: Sequence[Candle], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    true_ranges: list[float | None] = [None]
    for index in range(1, len(candles)):
        true_ranges.append(_true_range(candles[index - 1].close, candles[index]))

    out: list[float | None] = [None] * len(candles)
    for index in range(len(candles)):
        start = index - period + 1
        if start < 1:
            continue
        window = true_ranges[start : index + 1]
        if len(window) == period and all(item is not None for item in window):
            out[index] = sum(window) / period  # type: ignore[arg-type]
    return out
