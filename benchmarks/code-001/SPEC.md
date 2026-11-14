# CODE-001 — Implementation Spec (WITH_SPEC arm only)

The user story and acceptance requirements are **exactly those in TASK.md**. This document reorganizes them into invariants and state transitions; it does not add different acceptance criteria.

## Data model and invariants

Per order: `order_id` (canonical trimmed nonempty string), `status`, `paid_cents` (positive integer established once), `refunded_cents` (integer in `[0, paid_cents]`). Per successful event ID, store its canonical payload identity and **a copy of its outcome snapshot**. Return a fresh copy on every call, including retries. Never expose internal dictionaries.

Validation comes before lookup/mutation. A payload identity is `(order_id, type, amount_cents)` after trimming ID strings; boolean amounts are invalid even though `isinstance(True, int)` is true. Any validation/transition failure leaves both order and event registries unchanged.

## Transition table

| Existing order | Event with new ID | Outcome |
| --- | --- | --- |
| None | PAYMENT | PAID; `paid_cents = amount`, `refunded_cents = 0` |
| None | REFUND | Reject, no mutation |
| PAID / PARTIALLY_REFUNDED | REFUND | Add amount iff total ≤ paid; PARTIALLY_REFUNDED or REFUNDED |
| REFUNDED | REFUND | Reject, no mutation |
| Any existing status | PAYMENT | Reject (different event ID cannot recharge) |

Before these transitions, for a **previously successful** event ID: if the canonical payload matches, return the cached snapshot copy; if it differs, reject. A rejected event ID is not reserved and can be retried with a corrected payload.

## Acceptance checklist

Inputs validated; no double payment; partial/full/over-refund; unknown order; conflict on reused event ID; original snapshot for retries after later events; result isolation; atomic failure. Preserve the class and method signature. No migrations or external systems.
