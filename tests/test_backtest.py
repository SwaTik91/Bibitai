from decimal import Decimal

from bibitai.backtest import run_backtest
from bibitai.config import load_default_config
from bibitai.markets import trending_down_candles, ranging_sine_candles


def test_ranging_market_does_not_blow_up() -> None:
    report = run_backtest(
        candles=ranging_sine_candles(
            start=Decimal("100000"),
            bars=240,
            amplitude=Decimal("1200"),
        ),
        config=load_default_config(),
        quote=Decimal("10000"),
    )
    assert report.ending_equity > Decimal("9000")
    assert report.trade_count > 0
    assert report.max_drawdown_pct < Decimal("0.08")


def test_downtrend_does_not_accumulate_a_large_long() -> None:
    report = run_backtest(
        candles=trending_down_candles(
            start=Decimal("100000"),
            bars=180,
            drop=Decimal("15000"),
        ),
        config=load_default_config(),
        quote=Decimal("10000"),
    )
    assert report.max_base * report.ending_price / report.ending_equity < Decimal("0.35")
    assert report.killed is False or report.ending_equity >= Decimal("9000")
