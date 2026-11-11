"""Pure, deterministic workload adapters."""

from .response import Candidate, IntentCase, LabelOutput, classify_baseline, classify_candidate

__all__ = [
    "Candidate",
    "IntentCase",
    "LabelOutput",
    "classify_baseline",
    "classify_candidate",
]
