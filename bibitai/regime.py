from bibitai.models import Regime


def classify_regime(
    ema_fast: float,
    ema_slow: float,
    atr: float | None,
    range_threshold: float = 1.0,
    trend_threshold: float = 2.0,
) -> Regime:
    if atr is None or atr <= 0:
        return Regime.TRANSITION
    strength = abs(ema_fast - ema_slow) / atr
    if strength >= trend_threshold:
        return Regime.TRENDING
    if strength < range_threshold:
        return Regime.RANGING
    return Regime.TRANSITION
