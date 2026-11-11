"""Deterministic synthetic Response workload primitives.

These adapters are intentionally small rules for a demo fixture.  They do not
represent a production intent model or a claim about general AI quality.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

Label = str
Classifier = Callable[[str], "LabelOutput"]


@dataclass(frozen=True)
class LabelOutput:
    """The serializable output of an intent classifier."""

    label: Label

    def as_json(self) -> dict[str, str]:
        return {"label": self.label}


@dataclass(frozen=True)
class IntentCase:
    """One ordered synthetic input and its expected label."""

    id: str
    text: str
    expected_label: Label

    def input_json(self) -> dict[str, str]:
        return {"text": self.text}

    def expected_json(self) -> dict[str, str]:
        return {"label": self.expected_label}


@dataclass(frozen=True)
class Candidate:
    """A named deterministic classifier used by the comparison runner."""

    id: str
    label: str
    classify: Classifier


QUESTION: Final[Label] = "question"


def classify_baseline(text: str) -> LabelOutput:
    """A deliberately limited baseline: greeting or generic question."""
    normalized = text.casefold()
    if "olá" in normalized or "oi" in normalized:
        return LabelOutput("greeting")
    return LabelOutput(QUESTION)


def classify_candidate(text: str) -> LabelOutput:
    """A reproducible keyword classifier with broader support intent coverage."""
    normalized = text.casefold()
    if "cancelar" in normalized:
        return LabelOutput("cancellation")
    if "errado" in normalized or "reclamação" in normalized:
        return LabelOutput("complaint")
    if "dinheiro de volta" in normalized or "reembolso" in normalized:
        return LabelOutput("refund")
    if "onde está" in normalized or "rastrear" in normalized:
        return LabelOutput("order_status")
    if "olá" in normalized or "oi" in normalized:
        return LabelOutput("greeting")
    return LabelOutput(QUESTION)
