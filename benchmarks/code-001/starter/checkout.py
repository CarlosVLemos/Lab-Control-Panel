"""Intentionally flawed checkout-event ledger for benchmark CODE-001.

This implementation is the INPUT to a coding-agent task, not production code.
Keep this file unchanged in the benchmark fixture: agents edit a separate clone.
"""


class OrderLedger:
    def __init__(self):
        self._orders = {}
        self._processed = {}

    def apply(self, event):
        event_id = event["event_id"]
        order_id = event["order_id"]
        event_type = event["type"]
        amount = int(event["amount_cents"])

        if event_id in self._processed:
            return self._processed[event_id]

        if event_type == "PAYMENT":
            order = self._orders.setdefault(order_id, {
                "order_id": order_id,
                "status": "PAID",
                "paid_cents": 0,
                "refunded_cents": 0,
            })
            order["paid_cents"] += amount
            order["status"] = "PAID"
        elif event_type == "REFUND":
            order = self._orders[order_id]
            order["refunded_cents"] += amount
            order["status"] = (
                "REFUNDED"
                if order["refunded_cents"] >= order["paid_cents"]
                else "PARTIALLY_REFUNDED"
            )
        else:
            raise ValueError("unsupported event type")

        self._processed[event_id] = order
        return order
