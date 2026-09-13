from decimal import Decimal

from bibitai.grid import GridPlanner
from bibitai.models import Regime, Side


def planner() -> GridPlanner:
    return GridPlanner(
        levels=3,
        spacing_atr_mult=0.5,
        min_spacing_pct=Decimal("0.002"),
        inventory_shift_levels=2.0,
        quote_reserve_pct=0.20,
        maker_fee=Decimal("0.001"),
        min_notional=Decimal("10"),
        tick_size=Decimal("0.01"),
        step_size=Decimal("0.00001"),
    )


def test_ranging_grid_is_symmetric_around_mid() -> None:
    plan = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("800"),
        equity=Decimal("10000"),
        base=Decimal("0"),
        regime=Regime.RANGING,
    )
    buys = [level.price for level in plan if level.side is Side.BUY]
    sells = [level.price for level in plan if level.side is Side.SELL]
    assert buys == [Decimal("99600.00"), Decimal("99200.00"), Decimal("98800.00")]
    assert sells == [Decimal("100400.00"), Decimal("100800.00"), Decimal("101200.00")]
    assert all(level.quantity > 0 for level in plan)


def test_long_inventory_shifts_grid_down_and_drops_buys() -> None:
    # 0.03 BTC at 100k = 3000 USDT, 30% of 10k equity → skew = 0.30/0.35
    plan = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("800"),
        equity=Decimal("10000"),
        base=Decimal("0.03"),
        regime=Regime.RANGING,
        max_inventory_pct=0.35,
    )
    buys = [level.price for level in plan if level.side is Side.BUY]
    sells = [level.price for level in plan if level.side is Side.SELL]
    assert min(buys) < Decimal("98800.00")
    assert min(sells) < Decimal("100400.00")
    assert len(buys) <= len(sells)


def test_trending_only_reduces_inventory_never_adds() -> None:
    plan = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("800"),
        equity=Decimal("10000"),
        base=Decimal("0.02"),
        regime=Regime.TRENDING,
    )
    assert all(level.side is Side.SELL for level in plan)
    assert plan


def test_trending_with_no_base_stays_flat() -> None:
    plan = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("800"),
        equity=Decimal("10000"),
        base=Decimal("0"),
        regime=Regime.TRENDING,
    )
    assert plan == []


def test_fee_floor_widens_an_otherwise_tight_grid() -> None:
    plan = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("10"),
        equity=Decimal("10000"),
        base=Decimal("0"),
        regime=Regime.RANGING,
    )
    buys = [level.price for level in plan if level.side is Side.BUY]
    # ATR spacing is 5; fee-safe spacing is 3 * fee * mid = 300.
    assert buys[0] == Decimal("99700.00")


def test_transition_uses_half_size() -> None:
    ranging = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("800"),
        equity=Decimal("10000"),
        base=Decimal("0"),
        regime=Regime.RANGING,
    )
    transition = planner().plan(
        mid=Decimal("100000"),
        atr=Decimal("800"),
        equity=Decimal("10000"),
        base=Decimal("0"),
        regime=Regime.TRANSITION,
    )
    assert ranging and transition
    assert transition[0].quantity == ranging[0].quantity / 2
