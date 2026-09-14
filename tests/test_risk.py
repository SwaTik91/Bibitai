from decimal import Decimal

from bibitai.models import RiskDecision
from bibitai.risk import RiskGuard


def guard() -> RiskGuard:
    return RiskGuard(
        max_inventory_pct=0.35,
        max_daily_loss_pct=0.02,
        max_drawdown_pct=0.06,
        crash_atr_mult=4.0,
        pause_candles_after_crash=6,
    )


def test_healthy_book_is_allowed() -> None:
    decision = guard().evaluate(
        equity=Decimal("10000"),
        day_start_equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        base=Decimal("0.01"),
        mid=Decimal("100000"),
        candle_range=Decimal("200"),
        atr=Decimal("400"),
    )
    assert decision is RiskDecision.ALLOW


def test_daily_loss_kills_the_bot() -> None:
    decision = guard().evaluate(
        equity=Decimal("9790"),
        day_start_equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        base=Decimal("0"),
        mid=Decimal("100000"),
        candle_range=Decimal("100"),
        atr=Decimal("400"),
    )
    assert decision is RiskDecision.KILL_DAILY_LOSS


def test_drawdown_from_peak_kills_the_bot() -> None:
    decision = guard().evaluate(
        equity=Decimal("9300"),
        day_start_equity=Decimal("9400"),
        peak_equity=Decimal("10000"),
        base=Decimal("0"),
        mid=Decimal("100000"),
        candle_range=Decimal("100"),
        atr=Decimal("400"),
    )
    assert decision is RiskDecision.KILL_DRAWDOWN


def test_inventory_cap_blocks_new_buys_only() -> None:
    decision = guard().evaluate(
        equity=Decimal("10000"),
        day_start_equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        base=Decimal("0.04"),
        mid=Decimal("100000"),
        candle_range=Decimal("100"),
        atr=Decimal("400"),
    )
    assert decision is RiskDecision.BLOCK_BUYS


def test_crash_candle_pauses_trading() -> None:
    decision = guard().evaluate(
        equity=Decimal("10000"),
        day_start_equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        base=Decimal("0"),
        mid=Decimal("100000"),
        candle_range=Decimal("2000"),
        atr=Decimal("400"),
    )
    assert decision is RiskDecision.PAUSE_CRASH
