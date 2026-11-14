# CODE-001 — Idempotent checkout webhook ledger

Implement a correct **in-memory** `OrderLedger` in `checkout.py` (Python 3.12+, standard library only), preserving the public API `OrderLedger().apply(event: dict) -> dict`. This is a controlled benchmark, not a production payment service. Change only `checkout.py`.

The webhook event contains `event_id`, `order_id`, `type` (`PAYMENT` or `REFUND`), and `amount_cents` (positive integer; reject booleans). Missing fields, blank/non-string IDs, invalid types and nonpositive amounts must raise `ValueError` without modifying state. IDs are stripped of surrounding whitespace before use. Each successful call returns a **fresh snapshot** dictionary: `order_id`, `status`, `paid_cents`, `refunded_cents`; the caller must never be able to mutate stored state through this result.

Required behavior:
- The first `PAYMENT` for an order creates `PAID`, with `paid_cents` equal to the amount and `refunded_cents=0`.
- A **distinct** payment event for an order that already exists must raise `ValueError`: never charge twice or reopen a refunded order.
- `REFUND` requires an existing paid order. Multiple partial refunds are allowed only while the cumulative amount remains at most the original payment. Use `PARTIALLY_REFUNDED` until fully refunded and `REFUNDED` when complete; further refunds must fail.
- Re-delivery of **the same `event_id` with identical normalized payload** must return the **original result snapshot from that event**, even if later events changed the order.
- Reuse of an `event_id` with a different normalized payload must raise `ValueError`, regardless of order.
- Invalid events must not consume the event ID. After a rejected event, a corrected event with that ID must be eligible for processing.
- Failed events never mutate balances, statuses or deduplication records. Monetary values are integer cents only.

No database, API, threading, network access, extra dependencies or logging of sensitive data is needed. Work only in this isolated fixture. If you create temporary local tests, remove them when finished. **Do not edit or inspect the evaluator's separate acceptance tests**. Do not create commits.
