from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from bibitai.engine import BotEngine
from bibitai.models import Order, Side
from bibitai.paper import PaperBroker


def save_paper(path: Path, engine: BotEngine) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    broker = engine.broker
    payload = {
        "quote": str(broker.quote),
        "base": str(broker.base),
        "seq": broker._seq,
        "peak_equity": str(engine.state.peak_equity),
        "day_start_equity": str(engine.state.day_start_equity),
        "day_key": engine.state.day_key,
        "stopped": engine.state.stopped,
        "orders": [
            {
                "order_id": order.order_id,
                "client_id": order.client_id,
                "side": order.side.value,
                "price": str(order.price),
                "quantity": str(order.quantity),
                "filled_qty": str(order.filled_qty),
                "status": order.status,
            }
            for order in broker.orders()
        ],
    }
    path.write_text(json.dumps(payload, indent=2))


def load_paper(path: Path, engine: BotEngine) -> None:
    if not path.exists():
        return
    payload = json.loads(path.read_text())
    broker = engine.broker
    broker.quote = Decimal(payload["quote"])
    broker.base = Decimal(payload["base"])
    broker._seq = int(payload.get("seq", 0))
    broker._orders = {}
    for raw in payload.get("orders", []):
        order = Order(
            order_id=raw["order_id"],
            client_id=raw["client_id"],
            side=Side(raw["side"]),
            price=Decimal(raw["price"]),
            quantity=Decimal(raw["quantity"]),
            filled_qty=Decimal(raw["filled_qty"]),
            status=raw["status"],
        )
        broker._orders[order.order_id] = order
    engine.state.peak_equity = Decimal(payload.get("peak_equity", "0"))
    engine.state.day_start_equity = Decimal(payload.get("day_start_equity", "0"))
    engine.state.day_key = payload.get("day_key")
    engine.state.stopped = bool(payload.get("stopped", False))
    engine.state.max_base = broker.base
