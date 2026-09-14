from decimal import Decimal

from bibitai.indicators import atr, ema
from bibitai.models import Candle


def _candle(o: str, h: str, l: str, c: str) -> Candle:
    return Candle(
        open_time=0,
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(l),
        close=Decimal(c),
        volume=Decimal("1"),
    )


def test_ema_equals_seed_then_reacts_to_new_prices() -> None:
    values = [10.0, 10.0, 10.0, 16.0]
    result = ema(values, period=3)
    assert result[2] == 10.0
    # k = 2/(3+1) = 0.5 → 16*0.5 + 10*0.5 = 13
    assert result[3] == 13.0


def test_atr_uses_true_range_including_gaps() -> None:
    candles = [
        _candle("10", "11", "9", "10"),
        _candle("12", "13", "11.5", "12"),  # gap up; TR = max(1.5, 3, 1.5) = 3
        _candle("12", "12.5", "11", "11.5"),  # TR = max(1.5, 0.5, 1) = 1.5
    ]
    values = atr(candles, period=2)
    assert values[1] is None
    assert values[2] == 2.25
