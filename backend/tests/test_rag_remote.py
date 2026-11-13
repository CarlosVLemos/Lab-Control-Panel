"""Contract tests for RAG-001 remote MVP. Entire suite is offline."""
from __future__ import annotations

import json
import sys
import types
from decimal import Decimal

import pytest

from app.evaluation import rag_remote as remote


class FakeProvider:
    def __init__(self, *, fail_at: int | None = None):
        self.embeddings: list[list[str]] = []
        self.generations: list[tuple[str, list[dict[str, str]]]] = []
        self.fail_at = fail_at

    def embed(self, texts):
        self.embeddings.append(list(texts))
        return [[float((sum(x.encode()) % 13) + 1), float(len(x) % 11 + 1)] for x in texts], 10

    def generate(self, question, context):
        self.generations.append((question, list(context)))
        if self.fail_at == len(self.generations):
            raise TimeoutError("sk-test-sentinel private HTTP header")
        return {
            "answer": "Resposta de teste, não é avaliação semântica.",
            "citations": [],
            "input_tokens": 65,
            "output_tokens": 20,
            "cached_input_tokens": None,
            "model": remote.GEN_MODEL,
        }


def guard(embeddings=7, generations=12):
    return remote.Guard(Decimal("2"), generations, embeddings)


def test_manifest_is_frozen_and_case_order():
    m, cases = remote.validate_manifest()
    assert remote.canonical_sha(m) == remote.MANIFEST_SHA
    assert [c.id for c in cases] == [
        "rag-03", "rag-19", "rag-21", "rag-26", "rag-27", "rag-32"
    ]
    assert remote.fingerprint(remote.POLICIES, remote.CASES) == remote.DATASET_SHA


def test_manifest_tamper_fails_before_client(tmp_path):
    manifest, _ = remote.validate_manifest()
    for mutation in (
        lambda m: m["pilot_cases"].reverse(),
        lambda m: m["pilot_cases"][0].update({"category": "missing"}),
        lambda m: m.update({"attempts_per_arm": 2}),
    ):
        clone = json.loads(json.dumps(manifest))
        mutation(clone)
        path = tmp_path / "pilot.json"
        path.write_text(json.dumps(clone), encoding="utf-8")
        with pytest.raises(remote.Blocked):
            remote.validate_manifest(path)


def test_dry_run_never_constructs_network_client(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("network constructor must never be invoked")

    monkeypatch.setattr(remote, "OpenAIAdapter", forbidden)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert remote.main([]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["network_calls"] == 0 and payload["generation_calls_planned"] == 12
    assert not payload.get("execute")


def test_pairing_is_12_calls_only_and_no_context_leak():
    fake = FakeProvider()
    records = remote.run_pilot(fake, fake, guard())
    assert len(records) == 12
    assert len(fake.generations) == 12
    assert len(fake.embeddings) == 7  # one corpus batch + six query embeddings
    assert all(row["status"] == "COMPLETED" for row in records)
    assert {row["semantic_correctness"] for row in records} == {"NOT_EVALUATED"}
    for n in range(0, 12, 2):
        question0, context0 = fake.generations[n]
        question1, context1 = fake.generations[n + 1]
        assert question0 == question1
        assert context0 == []
        assert len(context1) == 3
        assert records[n]["arm"] == "NO_CONTEXT"
        assert records[n + 1]["arm"] == "SEMANTIC_RAG"
        assert all("expected_facts" not in json.dumps(item) for item in context1)


def test_counter_saturation_generation_12_plus_one_and_embeddings_n_plus_one():
    g = guard(embeddings=7)
    for _ in range(12):
        g.authorize("generation", ["pergunta"])
    with pytest.raises(remote.Blocked, match="CALL_LIMIT"):
        g.authorize("generation", ["pergunta"])
    assert g.generation_calls == 12
    for _ in range(7):
        g.authorize("embedding", ["pergunta"])
    with pytest.raises(remote.Blocked, match="CALL_LIMIT"):
        g.authorize("embedding", ["pergunta"])
    assert g.embedding_requests == 7


def test_budget_and_token_limits_fail_closed():
    g = guard()
    before = (g.reserved, g.generation_calls)
    with pytest.raises(remote.Blocked, match="TOKEN_BOUND"):
        g.authorize("generation", ["x" * 8193])
    assert (g.reserved, g.generation_calls) == before
    with pytest.raises(remote.Blocked, match="BUDGET_BLOCKED"):
        remote.Guard(Decimal("0"), 12, 7).authorize("generation", ["q"])
    assert remote.token_upper_bound(["ação"]) >= len("ação".encode())


def test_timeout_stops_after_one_transport_and_does_not_echo_secret(tmp_path, capsys):
    fake = FakeProvider(fail_at=1)
    records = remote.run_pilot(fake, fake, guard())
    assert len(records) == 1
    assert len(fake.generations) == 1
    assert records[0]["status"] == "INCONCLUSIVE"
    assert records[0]["error_code"] == "TIMEOUT"
    remote.save_report(records, tmp_path)
    combined = "".join(p.read_text() for p in tmp_path.iterdir())
    combined += capsys.readouterr().out
    assert "sk-test-sentinel" not in combined
    assert "private HTTP" not in combined


def test_sdk_constructor_disables_retries_and_includes_no_network_until_called(monkeypatch):
    created = []

    class SDKFake:
        def __init__(self, **options):
            created.append(options)

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SDKFake))
    remote.OpenAIAdapter("sk-test-sentinel")
    assert len(created) == 1
    assert created[0]["max_retries"] == 0


def test_report_jsonl_and_summary_have_no_winner(tmp_path):
    fake = FakeProvider()
    rows = remote.run_pilot(fake, fake, guard())
    remote.save_report(rows, tmp_path)
    lines = (tmp_path / "rag-001-results.jsonl").read_text().splitlines()
    assert len(lines) == 12
    assert json.loads(lines[0])["review_score"] is None
    assert json.loads(lines[0])["cached_input_tokens"] is None
    summary = json.loads((tmp_path / "rag-001-summary.json").read_text())
    assert summary["winner"] is None
    assert summary["completed"] == 12


@pytest.mark.parametrize("value", [
    "sk-test-sentinel", "Bearer sk-test-sentinel", None, 14
])
def test_secret_shaped_or_non_string_visible_answer_is_rejected(value):
    with pytest.raises(remote.Inconclusive):
        remote.safe_answer(value)


def test_cli_execute_requires_explicit_limits_even_with_env(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-sentinel")
    monkeypatch.setattr(remote, "OpenAIAdapter",
                        lambda *_: pytest.fail("client must not be built"))
    assert remote.main(["--execute", "--max-usd", "2"]) == 2
    assert "sk-test-sentinel" not in capsys.readouterr().err

def test_export_drops_unknown_provider_data_and_headers(tmp_path):
    row = {
        "schema": remote.SCHEMA_VERSION,
        "status": "INCONCLUSIVE",
        "error_code": "UNKNOWN",
        "answer": None,
        "private_headers": {"authorization": "Bearer sk-test-sentinel"},
        "sdk_exception": "sk-test-sentinel",
        "request": {"api_key": "sk-test-sentinel"},
    }
    remote.save_report([row], tmp_path)
    content = "".join(x.read_text() for x in tmp_path.iterdir())
    assert "sk-test-sentinel" not in content
    assert "private_headers" not in content
    assert "sdk_exception" not in content


def test_export_rejects_secret_in_allowlisted_field_without_creating_files(tmp_path):
    row = {
        "schema": remote.SCHEMA_VERSION,
        "answer": "sk-test-sentinel",
        "status": "COMPLETED",
    }
    with pytest.raises(remote.Blocked, match="EXPORT_SECRET"):
        remote.save_report([row], tmp_path)
    assert not tmp_path.exists() or not list(tmp_path.iterdir())


def test_export_rejects_nested_secret_and_invalid_error_code(tmp_path):
    with pytest.raises(remote.Blocked, match="EXPORT_SECRET"):
        remote.save_report([{"retrieved_docs": [{"id": "sk-test-sentinel"}]}], tmp_path)
    with pytest.raises(remote.Blocked, match="EXPORT_ERROR_CODE"):
        remote.save_report([{"error_code": "secret provider exception"}], tmp_path)

def test_partial_run_does_not_report_unknown_cost_as_zero(tmp_path):
    fake = FakeProvider(fail_at=1)
    rows = remote.run_pilot(fake, fake, guard())
    remote.save_report(rows, tmp_path)
    result = json.loads((tmp_path / "rag-001-summary.json").read_text())
    assert result["inconclusive"] is True
    assert result["total_estimated_usd"] is None
    assert result["generation_estimated_usd"] is None
