from __future__ import annotations

from decimal import Decimal

from bibitai.models import RiskDecision


class RiskGuard:
    def __init__(
        self,
        max_inventory_pct: float,
        max_daily_loss_pct: float,
        max_drawdown_pct: float,
        crash_atr_mult: float,
        pause_candles_after_crash: int,
    ) -> None:
        self.max_inventory_pct = max_inventory_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.crash_atr_mult = crash_atr_mult
        self.pause_candles_after_crash = pause_candles_after_crash

    def evaluate(
        self,
        equity: Decimal,
        day_start_equity: Decimal,
        peak_equity: Decimal,
        base: Decimal,
        mid: Decimal,
        candle_range: Decimal,
        atr: Decimal,
    ) -> RiskDecision:
        if day_start_equity > 0:
            daily_loss = (day_start_equity - equity) / day_start_equity
            if daily_loss >= Decimal(str(self.max_daily_loss_pct)):
                return RiskDecision.KILL_DAILY_LOSS
        if peak_equity > 0:
            drawdown = (peak_equity - equity) / peak_equity
            if drawdown >= Decimal(str(self.max_drawdown_pct)):
                return RiskDecision.KILL_DRAWDOWN
        atr_is_reliable = atr > 0 and mid > 0 and atr >= mid * Decimal("0.001")
        if atr_is_reliable and candle_range >= Decimal(str(self.crash_atr_mult)) * atr:
            return RiskDecision.PAUSE_CRASH
        if equity > 0 and (base * mid) / equity >= Decimal(str(self.max_inventory_pct)):
            return RiskDecision.BLOCK_BUYS
        return RiskDecision.ALLOW
