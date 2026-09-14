from decimal import Decimal
from pathlib import Path

from bibitai.config import load_default_config
from bibitai.engine import BotEngine
from bibitai.models import Side
from bibitai.paper import PaperBroker
from bibitai.statefile import load_paper, save_paper


def test_save_paper_drops_canceled_orders(tmp_path: Path) -> None:
    config = load_default_config()
    broker = PaperBroker(quote=Decimal("10000"), base=Decimal("0"), fee=Decimal("0.001"))
    engine = BotEngine(broker=broker, config=config)
    kept = broker.place_limit(Side.BUY, Decimal("99000"), Decimal("0.01"))
    dead = broker.place_limit(Side.BUY, Decimal("98000"), Decimal("0.01"))
    broker.cancel(dead.order_id)
    path = tmp_path / "paper-state.json"
    save_paper(path, engine)

    fresh = BotEngine(
        broker=PaperBroker(quote=Decimal("1"), base=Decimal("0"), fee=Decimal("0.001")),
        config=config,
    )
    load_paper(path, fresh)
    assert [order.order_id for order in fresh.broker.orders()] == [kept.order_id]
    assert fresh.broker.open_orders()[0].price == Decimal("99000")
