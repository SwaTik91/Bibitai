from decimal import Decimal

from bibitai.models import Side
from bibitai.paper import PaperBroker


def test_buy_limit_fills_when_last_trades_through() -> None:
    broker = PaperBroker(quote=Decimal("10000"), base=Decimal("0"), fee=Decimal("0.001"))
    order = broker.place_limit(Side.BUY, price=Decimal("99000"), quantity=Decimal("0.01"))
    fills = broker.mark(last=Decimal("98950"))
    assert fills[0].order_id == order.order_id
    assert broker.base == Decimal("0.01")
    # 99000 * 0.01 * 1.001 = 990.99 quote spent
    assert broker.quote == Decimal("10000") - Decimal("990.99")


def test_sell_limit_does_not_fill_before_price() -> None:
    broker = PaperBroker(quote=Decimal("0"), base=Decimal("0.01"), fee=Decimal("0.001"))
    broker.place_limit(Side.SELL, price=Decimal("101000"), quantity=Decimal("0.01"))
    assert broker.mark(last=Decimal("100500")) == []
    assert broker.base == Decimal("0.01")


def test_restart_does_not_double_fill_the_same_order() -> None:
    broker = PaperBroker(quote=Decimal("10000"), base=Decimal("0"), fee=Decimal("0.001"))
    order = broker.place_limit(Side.BUY, price=Decimal("99000"), quantity=Decimal("0.01"))
    broker.mark(last=Decimal("98900"))
    again = broker.mark(last=Decimal("98800"))
    assert again == []
    assert broker.get_order(order.order_id).status == "filled"
