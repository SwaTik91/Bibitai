from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Regime(str, Enum):
    RANGING = "RANGING"
    TRANSITION = "TRANSITION"
    TRENDING = "TRENDING"


class RiskDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK_BUYS = "BLOCK_BUYS"
    PAUSE_CRASH = "PAUSE_CRASH"
    KILL_DAILY_LOSS = "KILL_DAILY_LOSS"
    KILL_DRAWDOWN = "KILL_DRAWDOWN"


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @property
    def bar_range(self) -> Decimal:
        return self.high - self.low


@dataclass(frozen=True)
class GridLevel:
    side: Side
    price: Decimal
    quantity: Decimal


@dataclass
class Order:
    order_id: str
    client_id: str
    side: Side
    price: Decimal
    quantity: Decimal
    filled_qty: Decimal = Decimal("0")
    status: str = "open"


@dataclass(frozen=True)
class Fill:
    order_id: str
    side: Side
    price: Decimal
    quantity: Decimal
    fee: Decimal


@dataclass
class BacktestReport:
    ending_equity: Decimal
    ending_price: Decimal
    trade_count: int
    max_drawdown_pct: Decimal
    max_base: Decimal
    killed: bool
    ending_base: Decimal = Decimal("0")
    ending_quote: Decimal = Decimal("0")
    notes: list[str] = field(default_factory=list)
