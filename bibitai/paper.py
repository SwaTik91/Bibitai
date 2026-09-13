from __future__ import annotations

from decimal import Decimal

from bibitai.models import Fill, Order, Side


class PaperBroker:
    def __init__(self, quote: Decimal, base: Decimal, fee: Decimal) -> None:
        self.quote = quote
        self.base = base
        self.fee = fee
        self._orders: dict[str, Order] = {}
        self._seq = 0

    def place_limit(self, side: Side, price: Decimal, quantity: Decimal) -> Order:
        self._seq += 1
        order_id = str(self._seq)
        order = Order(
            order_id=order_id,
            client_id=f"bibitai-{order_id}",
            side=side,
            price=price,
            quantity=quantity,
        )
        self._orders[order_id] = order
        return order

    def cancel(self, order_id: str) -> None:
        order = self._orders.get(order_id)
        if order and order.status == "open":
            order.status = "canceled"

    def cancel_open(self) -> None:
        for order in self._orders.values():
            if order.status == "open":
                order.status = "canceled"

    def get_order(self, order_id: str) -> Order:
        return self._orders[order_id]

    def orders(self) -> list[Order]:
        return list(self._orders.values())

    def open_orders(self) -> list[Order]:
        return [order for order in self._orders.values() if order.status == "open"]

    def mark(self, last: Decimal) -> list[Fill]:
        fills: list[Fill] = []
        for order in self._orders.values():
            if order.status != "open":
                continue
            fill = self._try_fill(order, last)
            if fill:
                fills.append(fill)
        return fills

    def mark_candle(self, low: Decimal, high: Decimal) -> list[Fill]:
        fills: list[Fill] = []
        for order in self._orders.values():
            if order.status != "open":
                continue
            if order.side is Side.BUY and low <= order.price:
                fill = self._try_fill(order, order.price)
            elif order.side is Side.SELL and high >= order.price:
                fill = self._try_fill(order, order.price)
            else:
                fill = None
            if fill:
                fills.append(fill)
        return fills

    def _try_fill(self, order: Order, last: Decimal) -> Fill | None:
        if order.side is Side.BUY:
            if last > order.price:
                return None
            cost = order.price * order.quantity
            fee = cost * self.fee
            if self.quote < cost + fee:
                return None
            self.quote -= cost + fee
            self.base += order.quantity
        else:
            if last < order.price:
                return None
            if self.base < order.quantity:
                return None
            proceeds = order.price * order.quantity
            fee = proceeds * self.fee
            self.base -= order.quantity
            self.quote += proceeds - fee
        order.filled_qty = order.quantity
        order.status = "filled"
        fee = order.price * order.quantity * self.fee
        return Fill(order.order_id, order.side, order.price, order.quantity, fee)

    def equity(self, mid: Decimal) -> Decimal:
        return self.quote + self.base * mid
