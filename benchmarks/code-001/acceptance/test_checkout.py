"""Frozen acceptance suite: run against each agent clone via PYTHONPATH.

Keep OUTSIDE both agent workspaces. It intentionally fails on the starter.
"""
import pytest
from checkout import OrderLedger


def event(event_id, order_id="order-1", type="PAYMENT", amount_cents=1000):
    return {"event_id": event_id, "order_id": order_id, "type": type, "amount_cents": amount_cents}


def expected(status, paid=1000, refunded=0, order_id="order-1"):
    return {"order_id": order_id, "status": status, "paid_cents": paid, "refunded_cents": refunded}


def test_payment_creates_order():
    assert OrderLedger().apply(event("p1")) == expected("PAID")


def test_partial_refund():
    ledger = OrderLedger()
    ledger.apply(event("p1"))
    assert ledger.apply(event("r1", type="REFUND", amount_cents=300)) == expected("PARTIALLY_REFUNDED", refunded=300)


def test_full_refund_after_two_parts():
    ledger = OrderLedger()
    ledger.apply(event("p1"))
    ledger.apply(event("r1", type="REFUND", amount_cents=300))
    assert ledger.apply(event("r2", type="REFUND", amount_cents=700)) == expected("REFUNDED", refunded=1000)


def test_duplicate_event_returns_original_snapshot_after_other_events():
    ledger = OrderLedger()
    first = ledger.apply(event("p1"))
    ledger.apply(event("r1", type="REFUND", amount_cents=300))
    assert ledger.apply(event("p1")) == expected("PAID")
    assert first == expected("PAID")


def test_distinct_payment_event_cannot_recharge():
    ledger = OrderLedger()
    ledger.apply(event("p1"))
    with pytest.raises(ValueError):
        ledger.apply(event("p2"))
    assert ledger.apply(event("p1")) == expected("PAID")


def test_event_id_conflict_rejected_even_for_another_order():
    ledger = OrderLedger()
    ledger.apply(event("p1"))
    with pytest.raises(ValueError):
        ledger.apply(event("p1", order_id="other"))
    assert ledger.apply(event("p1")) == expected("PAID")


def test_over_refund_raises_and_does_not_mutate():
    ledger = OrderLedger()
    ledger.apply(event("p1"))
    with pytest.raises(ValueError):
        ledger.apply(event("r1", type="REFUND", amount_cents=1001))
    assert ledger.apply(event("p1")) == expected("PAID")
    assert ledger.apply(event("r1", type="REFUND", amount_cents=500)) == expected("PARTIALLY_REFUNDED", refunded=500)


def test_refund_unknown_order_is_value_error():
    with pytest.raises(ValueError):
        OrderLedger().apply(event("r1", type="REFUND", amount_cents=100))


@pytest.mark.parametrize("amount", [0, -1, True, 2.5, "100"])
def test_invalid_amounts_do_not_consume_event_id(amount):
    ledger = OrderLedger()
    with pytest.raises(ValueError):
        ledger.apply(event("p1", amount_cents=amount))
    assert ledger.apply(event("p1")) == expected("PAID")


@pytest.mark.parametrize("updates", [
    {"event_id": "   "},
    {"order_id": " "},
    {"event_id": 17},
    {"type": "CAPTURE"},
])
def test_invalid_event_does_not_modify_state(updates):
    ledger = OrderLedger()
    with pytest.raises(ValueError):
        ledger.apply(event("p1") | updates)
    assert ledger.apply(event("p1")) == expected("PAID")


def test_missing_field_rejected_without_mutation():
    ledger = OrderLedger()
    with pytest.raises(ValueError):
        ledger.apply({"event_id": "p1", "order_id": "order-1", "type": "PAYMENT"})
    assert ledger.apply(event("p1")) == expected("PAID")


def test_normalized_duplicate_event_id_and_order_id():
    ledger = OrderLedger()
    assert ledger.apply(event(" p1 ", order_id=" order-1 ")) == expected("PAID")
    assert ledger.apply(event("p1", order_id="order-1")) == expected("PAID")


def test_outcome_snapshots_are_defensive_copies():
    ledger = OrderLedger()
    response = ledger.apply(event("p1"))
    response["paid_cents"] = -999
    assert ledger.apply(event("p1")) == expected("PAID")


def test_refund_after_completion_rejected_without_mutation():
    ledger = OrderLedger()
    ledger.apply(event("p1"))
    ledger.apply(event("r1", type="REFUND", amount_cents=1000))
    with pytest.raises(ValueError):
        ledger.apply(event("r2", type="REFUND", amount_cents=10))
    assert ledger.apply(event("r1", type="REFUND", amount_cents=1000)) == expected("REFUNDED", refunded=1000)
