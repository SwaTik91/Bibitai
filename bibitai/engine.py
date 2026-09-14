from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from bibitai.config import AppConfig
from bibitai.grid import GridPlanner
from bibitai.indicators import atr, ema
from bibitai.models import Candle, Fill, GridLevel, Regime, RiskDecision, Side
from bibitai.money import quantize
from bibitai.paper import PaperBroker
from bibitai.regime import classify_regime
from bibitai.risk import RiskGuard


@dataclass
class EngineSnapshot:
    regime: Regime | None = None
    decision: RiskDecision | None = None
    stopped: bool = False
    pause_remaining: int = 0
    peak_equity: Decimal = Decimal("0")
    day_start_equity: Decimal = Decimal("0")
    day_key: int | None = None
    fills: list[Fill] = field(default_factory=list)
    max_base: Decimal = Decimal("0")
    max_drawdown_pct: Decimal = Decimal("0")
    last_candle_open_time: int | None = None
    last_plan_mid: Decimal | None = None
    last_regime: Regime | None = None
    seeded: bool = False


class BotEngine:
    def __init__(self, broker: PaperBroker, config: AppConfig) -> None:
        self.broker = broker
        self.config = config
        self.state = EngineSnapshot()
        self.planner = GridPlanner(
            levels=config.strategy.grid_levels,
            spacing_atr_mult=config.strategy.spacing_atr_mult,
            min_spacing_pct=config.strategy.min_spacing_pct,
            inventory_shift_levels=config.strategy.inventory_shift_levels,
            quote_reserve_pct=config.strategy.quote_reserve_pct,
            maker_fee=config.strategy.maker_fee,
            min_notional=config.risk.min_notional,
            tick_size=config.tick_size,
            step_size=config.step_size,
        )
        self.risk = RiskGuard(
            max_inventory_pct=config.risk.max_inventory_pct,
            max_daily_loss_pct=config.risk.max_daily_loss_pct,
            max_drawdown_pct=config.risk.max_drawdown_pct,
            crash_atr_mult=config.risk.crash_atr_mult,
            pause_candles_after_crash=config.risk.pause_candles_after_crash,
        )

    def on_candles(self, candles: list[Candle], last: Decimal | None = None) -> EngineSnapshot:
        if not candles:
            return self.state
        latest = candles[-1]
        price = last if last is not None else latest.close
        new_bar = self.state.last_candle_open_time != latest.open_time

        new_fills: list[Fill] = []
        if new_bar:
            new_fills.extend(self.broker.mark_candle(latest.low, latest.high))
            self.state.last_candle_open_time = latest.open_time
        new_fills.extend(self.broker.mark(price))
        self.state.fills.extend(new_fills)
        self.state.max_base = max(self.state.max_base, self.broker.base)

        if self.state.stopped:
            return self.state

        if len(candles) < self.config.strategy.ema_slow + 1:
            return self.state

        closes = [float(candle.close) for candle in candles]
        fast = ema(closes, self.config.strategy.ema_fast)[-1]
        slow = ema(closes, self.config.strategy.ema_slow)[-1]
        atr_values = atr(candles, self.config.strategy.atr_period)
        atr_last = atr_values[-1]
        if fast is None or slow is None:
            return self.state

        regime = classify_regime(
            ema_fast=fast,
            ema_slow=slow,
            atr=atr_last,
            range_threshold=self.config.strategy.range_threshold,
            trend_threshold=self.config.strategy.trend_threshold,
        )
        self.state.regime = regime

        equity = self.broker.equity(price)
        self._roll_day(latest, equity)
        if equity > self.state.peak_equity:
            self.state.peak_equity = equity
        if self.state.peak_equity > 0:
            drawdown = (self.state.peak_equity - equity) / self.state.peak_equity
            if drawdown > self.state.max_drawdown_pct:
                self.state.max_drawdown_pct = drawdown

        atr_decimal = Decimal(str(atr_last or 0))
        decision = self.risk.evaluate(
            equity=equity,
            day_start_equity=self.state.day_start_equity,
            peak_equity=self.state.peak_equity,
            base=self.broker.base,
            mid=price,
            candle_range=latest.bar_range,
            atr=atr_decimal,
        )
        self.state.decision = decision

        if decision in {RiskDecision.KILL_DAILY_LOSS, RiskDecision.KILL_DRAWDOWN}:
            self.broker.cancel_open()
            self.state.stopped = True
            return self.state

        if self.state.pause_remaining > 0:
            if new_bar:
                self.state.pause_remaining -= 1
            self.broker.cancel_open()
            return self.state

        if decision is RiskDecision.PAUSE_CRASH:
            self.state.pause_remaining = self.config.risk.pause_candles_after_crash
            self.broker.cancel_open()
            return self.state

        seeded_now = self._maybe_seed(price, equity, regime)
        if seeded_now:
            new_fills.append(seeded_now)
            self.state.fills.append(seeded_now)
            self.state.max_base = max(self.state.max_base, self.broker.base)

        spacing = self.planner.spacing(price, atr_decimal)
        moved = (
            self.state.last_plan_mid is None
            or abs(price - self.state.last_plan_mid) >= spacing * Decimal("0.5")
        )
        should_replan = (
            new_bar
            or bool(new_fills)
            or not self.broker.open_orders()
            or regime != self.state.last_regime
            or moved
        )
        if not should_replan:
            return self.state

        plan = self.planner.plan(
            mid=price,
            atr=atr_decimal,
            equity=equity,
            base=self.broker.base,
            regime=regime,
            max_inventory_pct=self.config.risk.max_inventory_pct,
        )
        if decision is RiskDecision.BLOCK_BUYS:
            plan = [level for level in plan if level.side is Side.SELL]
        self._reconcile(plan)
        self.state.last_plan_mid = price
        self.state.last_regime = regime
        return self.state

    def _maybe_seed(self, price: Decimal, equity: Decimal, regime: Regime) -> Fill | None:
        if self.state.seeded:
            return None
        if self.broker.base > 0:
            self.state.seeded = True
            return None
        if regime is not Regime.RANGING:
            return None
        pct = Decimal(str(self.config.strategy.seed_inventory_pct))
        if pct <= 0 or price <= 0:
            self.state.seeded = True
            return None
        quantity = quantize((equity * pct) / price, self.config.step_size)
        if quantity * price < self.config.risk.min_notional:
            return None
        fill = self.broker.market_buy(price, quantity)
        if fill:
            self.state.seeded = True
        return fill

    def _roll_day(self, candle: Candle, equity: Decimal) -> None:
        key = candle.open_time // 86_400_000 if candle.open_time > 10_000_000 else 0
        if self.state.day_key is None or key != self.state.day_key:
            self.state.day_key = key
            self.state.day_start_equity = equity

    def _reconcile(self, plan: list[GridLevel]) -> None:
        desired = {(level.side, level.price): level for level in plan}
        for order in self.broker.open_orders():
            key = (order.side, order.price)
            if key in desired:
                del desired[key]
            else:
                self.broker.cancel(order.order_id)

        for level in desired.values():
            quantity = level.quantity
            if level.side is Side.SELL:
                quantity = min(quantity, quantize(self.broker.base, self.config.step_size))
            if quantity <= 0 or quantity * level.price < self.config.risk.min_notional:
                continue
            if level.side is Side.BUY:
                cost = quantity * level.price * (Decimal("1") + self.config.strategy.maker_fee)
                if self.broker.quote < cost:
                    continue
            self.broker.place_limit(level.side, level.price, quantity)
