"""Versioned, synthetic support-intent fixture used by the MVP comparison."""

from __future__ import annotations

from app.workloads.response import Candidate, IntentCase, classify_baseline, classify_candidate

EXPERIMENT_ID = "demo-support-intents-v1"
DATASET_ID = "support-intents"
DATASET_VERSION = "v1"

# This is synthetic fixture data only; it is not evidence of general model quality.
RESPONSE_CASES: tuple[IntentCase, ...] = (
    IntentCase("case-01", "Olá, preciso de ajuda", "greeting"),
    IntentCase("case-02", "Onde está meu pedido?", "order_status"),
    IntentCase("case-03", "Meu pedido veio errado", "complaint"),
    IntentCase("case-04", "Quero cancelar meu pedido", "cancellation"),
    IntentCase("case-05", "Quero meu dinheiro de volta", "refund"),
    IntentCase("case-06", "Como altero meu endereço?", "question"),
)

BASELINE = Candidate("baseline-v1", "Baseline", classify_baseline)
CANDIDATE = Candidate("candidate-v2", "Candidato", classify_candidate)
