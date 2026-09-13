from __future__ import annotations

from decimal import Decimal

from bibitai.models import GridLevel, Regime, Side
from bibitai.money import quantize


class GridPlanner:
    def __init__(
        self,
        levels: int,
        spacing_atr_mult: float,
        min_spacing_pct: Decimal,
        inventory_shift_levels: float,
        quote_reserve_pct: float,
        maker_fee: Decimal,
        min_notional: Decimal,
        tick_size: Decimal,
        step_size: Decimal,
    ) -> None:
        self.levels = levels
        self.spacing_atr_mult = spacing_atr_mult
        self.min_spacing_pct = min_spacing_pct
        self.inventory_shift_levels = inventory_shift_levels
        self.quote_reserve_pct = quote_reserve_pct
        self.maker_fee = maker_fee
        self.min_notional = min_notional
        self.tick_size = tick_size
        self.step_size = step_size

    def spacing(self, mid: Decimal, atr_value: Decimal) -> Decimal:
        atr_spacing = atr_value * Decimal(str(self.spacing_atr_mult))
        floor = mid * self.min_spacing_pct
        fee_floor = mid * self.maker_fee * Decimal("3")
        raw = max(atr_spacing, floor, fee_floor)
        return quantize(raw, self.tick_size) or self.tick_size

    def plan(
        self,
        mid: Decimal,
        atr: Decimal,
        equity: Decimal,
        base: Decimal,
        regime: Regime,
        max_inventory_pct: float = 0.35,
    ) -> list[GridLevel]:
        if mid <= 0 or equity <= 0:
            return []
        spacing = self.spacing(mid, atr)
        if regime is Regime.TRENDING:
            return self._flatten(mid, base, spacing)

        inventory_pct = (base * mid) / equity
        cap = Decimal(str(max_inventory_pct))
        skew = Decimal("0") if cap <= 0 else inventory_pct / cap
        skew = min(Decimal("1"), max(Decimal("-1"), skew))
        center = quantize(mid - skew * Decimal(str(self.inventory_shift_levels)) * spacing, self.tick_size)

        size_mult = Decimal("0.5") if regime is Regime.TRANSITION else Decimal("1")
        usable = equity * (Decimal("1") - Decimal(str(self.quote_reserve_pct)))
        level_notional = (usable / Decimal(self.levels * 2)) * size_mult
        remaining_buy = max(Decimal("0"), cap * equity - base * mid)

        buys: list[GridLevel] = []
        sells: list[GridLevel] = []
        for index in range(1, self.levels + 1):
            buy_price = quantize(center - spacing * index, self.tick_size)
            sell_price = quantize(center + spacing * index, self.tick_size)
            if buy_price <= 0:
                continue
            buy_notional = min(level_notional, remaining_buy)
            buy_qty = quantize(buy_notional / buy_price, self.step_size)
            if buy_qty > 0 and buy_qty * buy_price >= self.min_notional:
                buys.append(GridLevel(Side.BUY, buy_price, buy_qty))
                remaining_buy -= buy_qty * buy_price

            sell_qty = quantize(level_notional / sell_price, self.step_size)
            if sell_qty > 0 and sell_qty * sell_price >= self.min_notional:
                sells.append(GridLevel(Side.SELL, sell_price, sell_qty))

        return buys + sells

    def _flatten(self, mid: Decimal, base: Decimal, spacing: Decimal) -> list[GridLevel]:
        quantity = quantize(base, self.step_size)
        if quantity <= 0:
            return []
        price = quantize(mid - spacing / Decimal("2"), self.tick_size) or mid
        if quantity * price < self.min_notional:
            return []
        return [GridLevel(Side.SELL, price, quantity)]
