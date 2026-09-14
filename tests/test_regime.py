from bibitai.models import Regime
from bibitai.regime import classify_regime


def test_ranging_when_emas_are_close_relative_to_atr() -> None:
    assert classify_regime(ema_fast=100.4, ema_slow=100.0, atr=1.0) is Regime.RANGING


def test_trending_when_emas_are_far_relative_to_atr() -> None:
    assert classify_regime(ema_fast=103.0, ema_slow=100.0, atr=1.0) is Regime.TRENDING
    assert classify_regime(ema_fast=97.0, ema_slow=100.0, atr=1.0) is Regime.TRENDING


def test_transition_is_the_band_between_range_and_trend() -> None:
    assert classify_regime(ema_fast=101.5, ema_slow=100.0, atr=1.0) is Regime.TRANSITION


def test_missing_atr_is_transition_not_a_guess() -> None:
    assert classify_regime(ema_fast=100.0, ema_slow=100.0, atr=0.0) is Regime.TRANSITION
    assert classify_regime(ema_fast=100.0, ema_slow=100.0, atr=None) is Regime.TRANSITION
