from decimal import Decimal

from bibitai.config import load_default_config
from bibitai.engine import BotEngine
from bibitai.markets import flat_candles
from bibitai.models import Candle, Side
from bibitai.paper import PaperBroker


def test_engine_fills_a_buy_after_warmup_when_price_dips() -> None:
    config = load_default_config()
    broker = PaperBroker(quote=Decimal("10000"), base=Decimal("0"), fee=Decimal("0.001"))
    engine = BotEngine(broker=broker, config=config)
    warmup = flat_candles(price=Decimal("100000"), bars=60)
    engine.on_candles(warmup)

    dip = Candle(
        open_time=61,
        open=Decimal("100000"),
        high=Decimal("100000"),
        low=Decimal("99000"),
        close=Decimal("99200"),
        volume=Decimal("1"),
    )
    engine.on_candles(warmup + [dip], last=Decimal("99200"))

    assert broker.base > 0
    assert any(order.side is Side.BUY and order.status == "filled" for order in broker.orders())


def test_same_candle_does_not_churn_open_orders() -> None:
    config = load_default_config()
    broker = PaperBroker(quote=Decimal("10000"), base=Decimal("0"), fee=Decimal("0.001"))
    engine = BotEngine(broker=broker, config=config)
    warmup = flat_candles(price=Decimal("100000"), bars=60)
    engine.on_candles(warmup, last=Decimal("100000"))
    first = {order.order_id for order in broker.open_orders()}
    assert first
    engine.on_candles(warmup, last=Decimal("100080"))
    assert {order.order_id for order in broker.open_orders()} == first
    assert sum(1 for order in broker.orders() if order.status == "canceled") == 0
