import json

import pytest

from app.demo.response_fixture import (
    BASELINE,
    CANDIDATE,
    DATASET_ID,
    DATASET_VERSION,
    EXPERIMENT_ID,
    RESPONSE_CASES,
)
from app.evaluation.response import build_response_report, evaluate_exact_label, run_candidate
from app.workloads.response import Candidate, IntentCase, LabelOutput, classify_baseline, classify_candidate


def report():
    return build_response_report(
        experiment_id=EXPERIMENT_ID,
        dataset_id=DATASET_ID,
        dataset_version=DATASET_VERSION,
        baseline=BASELINE,
        candidate=CANDIDATE,
        cases=RESPONSE_CASES,
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Olá, preciso de ajuda", "greeting"),
        ("Onde está meu pedido?", "order_status"),
        ("Meu pedido veio errado", "complaint"),
        ("Quero cancelar meu pedido", "cancellation"),
        ("Quero meu dinheiro de volta", "refund"),
        ("Como altero meu endereço?", "question"),
    ],
)
def test_candidate_classifies_synthetic_intents(text, expected):
    assert classify_candidate(text).label == expected


def test_baseline_is_distinct_and_reproducible():
    case = RESPONSE_CASES[2]
    assert classify_baseline(case.text).label == "question"
    assert classify_candidate(case.text).label == "complaint"
    assert report() == report()


def test_report_preserves_fixture_ids_and_order_and_derives_scores():
    actual = report()
    assert [case["id"] for case in actual["cases"]] == [case.id for case in RESPONSE_CASES]
    assert actual["summary"] == {
        "baseline": {"passed": 2, "total": 6},
        "candidate": {"passed": 6, "total": 6},
    }
    assert actual["synthetic"] is True


def test_adapter_errors_and_missing_outputs_fail_closed():
    def broken_classifier(_: str) -> LabelOutput:
        raise RuntimeError("adapter unavailable")

    broken = Candidate("broken", "Broken", broken_classifier)
    execution = run_candidate(broken, RESPONSE_CASES[0])
    assert execution.output is None
    assert execution.error == "RuntimeError"
    assert not evaluate_exact_label(RESPONSE_CASES[0].expected_label, execution)

    invalid = Candidate("invalid", "Invalid", lambda _: "greeting")  # type: ignore[arg-type]
    assert run_candidate(invalid, RESPONSE_CASES[0]).error == "InvalidOutput"


def test_report_matches_minimum_json_schema_without_extra_required_fields():
    actual = report()
    assert set(actual) == {"experimentId", "synthetic", "dataset", "baseline", "candidate", "summary", "cases"}
    assert set(actual["dataset"]) == {"id", "version"}
    assert set(actual["baseline"]) == {"id", "label"}
    assert set(actual["summary"]["candidate"]) == {"passed", "total"}
    assert set(actual["cases"][0]) == {"id", "input", "expected", "baseline", "candidate"}
    assert set(actual["cases"][0]["candidate"]) == {"output", "passed"}
    assert json.loads(json.dumps(actual)) == actual


def test_empty_fixture_is_a_valid_zero_total_report():
    actual = build_response_report(
        experiment_id="empty-demo",
        dataset_id="empty",
        dataset_version="v1",
        baseline=BASELINE,
        candidate=CANDIDATE,
        cases=(),
    )
    assert actual["summary"] == {
        "baseline": {"passed": 0, "total": 0},
        "candidate": {"passed": 0, "total": 0},
    }
