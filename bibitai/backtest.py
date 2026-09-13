from __future__ import annotations

from decimal import Decimal

from bibitai.config import AppConfig, load_default_config
from bibitai.engine import BotEngine
from bibitai.models import BacktestReport, Candle
from bibitai.paper import PaperBroker


def run_backtest(
    candles: list[Candle],
    config: AppConfig | None = None,
    quote: Decimal | None = None,
    base: Decimal | None = None,
) -> BacktestReport:
    config = config or load_default_config()
    broker = PaperBroker(
        quote=quote if quote is not None else config.paper.quote,
        base=base if base is not None else config.paper.base,
        fee=config.strategy.maker_fee,
    )
    engine = BotEngine(broker=broker, config=config)

    for index in range(len(candles)):
        engine.on_candles(candles[: index + 1], last=candles[index].close)

    last_price = candles[-1].close if candles else Decimal("0")
    return BacktestReport(
        ending_equity=broker.equity(last_price),
        ending_price=last_price,
        trade_count=len(engine.state.fills),
        max_drawdown_pct=engine.state.max_drawdown_pct,
        max_base=engine.state.max_base,
        killed=engine.state.stopped,
        ending_base=broker.base,
        ending_quote=broker.quote,
        notes=[
            f"regime={engine.state.regime}",
            f"decision={engine.state.decision}",
        ],
    )
