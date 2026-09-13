from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PaperConfig(BaseModel):
    quote: Decimal = Decimal("10000")
    base: Decimal = Decimal("0")


class StrategyConfig(BaseModel):
    ema_fast: int = 20
    ema_slow: int = 50
    atr_period: int = 14
    range_threshold: float = 1.0
    trend_threshold: float = 2.0
    grid_levels: int = 4
    spacing_atr_mult: float = 0.6
    min_spacing_pct: Decimal = Decimal("0.002")
    inventory_shift_levels: float = 2.0
    quote_reserve_pct: float = 0.20
    maker_fee: Decimal = Decimal("0.001")


class RiskConfig(BaseModel):
    max_inventory_pct: float = 0.35
    max_daily_loss_pct: float = 0.02
    max_drawdown_pct: float = 0.06
    crash_atr_mult: float = 4.0
    pause_candles_after_crash: int = 6
    min_notional: Decimal = Decimal("10")


class RuntimeConfig(BaseModel):
    poll_seconds: int = 5
    kline_refresh_seconds: int = 30
    state_dir: str = "data"


class AppConfig(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    quote_asset: str = "USDT"
    tick_size: Decimal = Decimal("0.01")
    step_size: Decimal = Decimal("0.00001")
    paper: PaperConfig = Field(default_factory=PaperConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)


def load_default_config() -> AppConfig:
    return AppConfig()


def load_config(path: str | Path | None) -> AppConfig:
    if path is None:
        return load_default_config()
    payload: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
    return AppConfig.model_validate(payload)
