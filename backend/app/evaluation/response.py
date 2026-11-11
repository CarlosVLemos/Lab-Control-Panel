"""Fail-closed evaluator and JSON report composer for Response fixtures."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypedDict

from app.workloads.response import Candidate, IntentCase, LabelOutput


class CandidateResult(TypedDict):
    output: dict[str, str]
    passed: bool


class CaseReport(TypedDict):
    id: str
    input: dict[str, str]
    expected: dict[str, str]
    baseline: CandidateResult
    candidate: CandidateResult


class ResponseReport(TypedDict):
    experimentId: str
    synthetic: bool
    dataset: dict[str, str]
    baseline: dict[str, str]
    candidate: dict[str, str]
    summary: dict[str, dict[str, int]]
    cases: list[CaseReport]


@dataclass(frozen=True)
class CandidateExecution:
    """A single adapter execution; failures deliberately have no output."""

    output: LabelOutput | None
    error: str | None = None


def run_candidate(candidate: Candidate, case: IntentCase) -> CandidateExecution:
    """Run one adapter, converting adapter failures into a serializable-safe result."""
    try:
        output = candidate.classify(case.text)
    except Exception as error:  # Adapter boundary: an error must not promote a pass.
        return CandidateExecution(output=None, error=type(error).__name__)
    if not isinstance(output, LabelOutput):
        return CandidateExecution(output=None, error="InvalidOutput")
    return CandidateExecution(output=output)


def evaluate_exact_label(expected: str, execution: CandidateExecution) -> bool:
    """Return true only for an observed output whose label exactly matches."""
    return execution.output is not None and execution.output.label == expected


def _result(case: IntentCase, execution: CandidateExecution) -> CandidateResult:
    # The integration contract has only output/passed. Empty output represents an
    # unavailable/invalid adapter result and fail-closes the evaluator.
    output = execution.output.as_json() if execution.output is not None else {}
    return {"output": output, "passed": evaluate_exact_label(case.expected_label, execution)}


def build_response_report(
    *,
    experiment_id: str,
    dataset_id: str,
    dataset_version: str,
    baseline: Candidate,
    candidate: Candidate,
    cases: Sequence[IntentCase],
) -> ResponseReport:
    """Execute both candidates over the same ordered cases and compose the contract JSON."""
    case_reports: list[CaseReport] = []
    baseline_passed = 0
    candidate_passed = 0

    for case in cases:
        baseline_result = _result(case, run_candidate(baseline, case))
        candidate_result = _result(case, run_candidate(candidate, case))
        baseline_passed += int(baseline_result["passed"])
        candidate_passed += int(candidate_result["passed"])
        case_reports.append({
            "id": case.id,
            "input": case.input_json(),
            "expected": case.expected_json(),
            "baseline": baseline_result,
            "candidate": candidate_result,
        })

    total = len(case_reports)
    return {
        "experimentId": experiment_id,
        "synthetic": True,
        "dataset": {"id": dataset_id, "version": dataset_version},
        "baseline": {"id": baseline.id, "label": baseline.label},
        "candidate": {"id": candidate.id, "label": candidate.label},
        "summary": {
            "baseline": {"passed": baseline_passed, "total": total},
            "candidate": {"passed": candidate_passed, "total": total},
        },
        "cases": case_reports,
    }


def response_report_json(report: ResponseReport) -> dict[str, Any]:
    """Expose the TypedDict report as a JSON-compatible object for future adapters."""
    return report
