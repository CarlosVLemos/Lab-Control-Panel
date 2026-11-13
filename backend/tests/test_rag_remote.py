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



def test_sdk_request_is_same_envelope_reserved_before_send(monkeypatch):
    """Verify actual SDK kwargs and preflight use the same request source."""
    captured = []

    class ResponsesFake:
        def create(self, **kwargs):
            captured.append(kwargs)
            return types.SimpleNamespace(
                status="completed", service_tier="default",
                output_text=json.dumps({
                    "answer": "Não há prova suficiente.",
                    "abstained": True, "citations": [],
                }),
                model=remote.GEN_MODEL,
                usage=types.SimpleNamespace(
                    input_tokens=100, output_tokens=30, input_tokens_details=None,
                ),
            )

    class SDKFake:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.responses = ResponsesFake()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SDKFake))
    adapter = remote.OpenAIAdapter("sk-test-sentinel")
    question = "Qual o prazo?"
    docs = [{"id": "shipping", "version": "v1", "text": "Cinco dias úteis."}]
    envelope = remote.generation_request(question, docs)
    g = guard()
    g.authorize("generation", [json.dumps(envelope, ensure_ascii=False, sort_keys=True)])
    answer = adapter.generate(question, docs)
    assert captured == [envelope]
    assert "shipping" in captured[0]["input"]
    assert "expected_facts" not in str(captured)
    assert answer["input_tokens"] == 100
    assert g.generation_calls == 1


def test_sdk_timeout_never_retries_and_never_raises_secret_text(monkeypatch):
    sends = []

    class ResponsesFake:
        def create(self, **kwargs):
            sends.append(kwargs)
            raise TimeoutError("Bearer sk-test-sentinel")

    class SDKFake:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.responses = ResponsesFake()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SDKFake))
    adapter = remote.OpenAIAdapter("sk-test-sentinel")
    with pytest.raises(TimeoutError):
        adapter.generate("Pergunta de teste", [])
    assert len(sends) == 1
    assert remote.error_code(TimeoutError("Bearer sk-test-sentinel")) == "TIMEOUT"


def test_response_with_incompatible_tier_is_rejected(monkeypatch):
    class ResponsesFake:
        def create(self, **kwargs):
            return types.SimpleNamespace(
                status="completed", service_tier="priority",
                output_text='{"answer":"a","abstained":false,"citations":[]}',
                model=remote.GEN_MODEL,
                usage=types.SimpleNamespace(input_tokens=1, output_tokens=1),
            )

    class SDKFake:
        def __init__(self, **kwargs):
            self.responses = ResponsesFake()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SDKFake))
    with pytest.raises(remote.Inconclusive, match="TIER_MISMATCH"):
        remote.OpenAIAdapter("sk-test-sentinel").generate("Pergunta", [])


def test_generation_bound_covers_outgoing_document_and_schema_envelope():
    request = remote.generation_request(
        "Qual o prazo?", [{"id": "shipping", "version": "v1", "text": "Cinco dias úteis."}]
    )
    wire_json = json.dumps(request, ensure_ascii=False, sort_keys=True)
    g = guard()
    g.authorize("generation", [wire_json])
    assert g.generation_calls == 1
    # The serialized schema and all labels are included in the reservation.
    assert "rag_answer" in wire_json
    assert "DOCUMENTO_NAO_CONFIAVEL" in wire_json
    assert remote.token_upper_bound([wire_json], overhead=2048) <= remote.MAX_INPUT



def test_retrieval_recall_is_distinct_and_not_scored_for_missing_cases():
    fake = FakeProvider()
    rows = remote.run_pilot(fake, fake, guard())
    assert len(rows) == 12
    for row in rows:
        if row["arm"] == "NO_CONTEXT" or row["case_id"] in ("rag-27", "rag-32"):
            assert row["retrieval_recall_at_3"] is None
        else:
            assert 0.0 <= row["retrieval_recall_at_3"] <= 1.0
        assert row["semantic_correctness"] == "NOT_EVALUATED"



def valid_pricing_dict():
    return {
        "schema": remote.PRICING_SCHEMA,
        "generation_model": remote.GEN_MODEL,
        "embedding_model": remote.EMBED_MODEL,
        "service_tier": "standard",
        "region": "global",
        "account_region_confirmed": True,
        "regional_surcharge_applies": False,
        "model_access_confirmed": True,
        "currency": "USD",
        "unit": "per_million_tokens",
        "generation_price_url": remote.PRICE_REFERENCE,
        "embedding_price_url": remote.EMBED_PRICE_REFERENCE,
        "multiplier": "1",
        "additional_fees_confirmed": "none",
        "verified_at_utc": "2026-11-13T13:00:00Z",
        "prices_usd_per_million": {
            "generation_input": "0.10",
            "generation_cache_read": "0.01",
            "generation_cache_write": "0.125",
            "generation_output": "0.50",
            "embedding_input": "0.02",
        },
    }


def pricing_file(tmp_path, obj):
    from pathlib import Path
    path = (tmp_path / "pricing.json").resolve()
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def pricing_clock():
    from datetime import datetime, timezone
    return datetime(2026, 11, 13, 13, 30, tzinfo=timezone.utc)


def test_valid_operator_snapshot_loaded_and_worst_case_reservation(tmp_path):
    snapshot = remote.load_pricing_snapshot(
        pricing_file(tmp_path, valid_pricing_dict()), now=pricing_clock())
    g = remote.Guard(Decimal("2"), 12, 7, pricing=snapshot)
    g.authorize("generation", ["pergunta"])
    assert g.reserved == remote.estimated_usd(
        remote.token_upper_bound(["pergunta"], overhead=2048), 1024,
        prices=snapshot.prices,
    )
    assert snapshot.region == "global"
    assert snapshot.service_tier == "standard"


@pytest.mark.parametrize("mutator", [
    lambda p: p.pop("region"),
    lambda p: p.update({"region": "us-east-1"}),
    lambda p: p.update({"region": "regional"}),
    lambda p: p.update({"regional_surcharge_applies": True}),
    lambda p: p.update({"account_region_confirmed": False}),
    lambda p: p.update({"service_tier": "priority"}),
    lambda p: p.update({"model_access_confirmed": False}),
    lambda p: p.update({"verified_at_utc": "2026-11-10T13:00:00Z"}),
    lambda p: p.update({"verified_at_utc": "2030-01-01T00:00:00Z"}),
    lambda p: p.update({"generation_price_url": "https://example.com"}),
    lambda p: p.update({"multiplier": "2"}),
    lambda p: p.update({"additional_fees_confirmed": "unknown"}),
    lambda p: p["prices_usd_per_million"].pop("embedding_input"),
    lambda p: p["prices_usd_per_million"].update({"generation_output": "NaN"}),
    lambda p: p["prices_usd_per_million"].update({"generation_input": "0.001"}),
])
def test_pricing_bad_or_stale_snapshot_blocks_pre_client(tmp_path, mutator):
    p = valid_pricing_dict()
    mutator(p)
    with pytest.raises(remote.Blocked, match="PRICING_UNVERIFIED"):
        remote.load_pricing_snapshot(pricing_file(tmp_path, p), now=pricing_clock())


def test_execute_blocks_missing_pricing_before_credential_read(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-sentinel")
    monkeypatch.setattr(remote, "OpenAIAdapter", lambda *_: pytest.fail("client created"))
    assert remote.main([
        "--execute", "--max-usd", "2", "--max-generation-calls", "12",
        "--max-embedding-requests", "7",
    ]) == 2
    assert "sk-test-sentinel" not in capsys.readouterr().err


@pytest.mark.parametrize("input_bytes", [8191, 8192, 8193, 271999, 272000, 272001])
def test_token_boundary_before_transport(input_bytes):
    g = guard()
    text = "x" * input_bytes
    physical = []
    try:
        g.authorize("generation", [text])
        physical.append(1)
    except remote.Blocked as exc:
        assert str(exc) == "TOKEN_BOUND"
    assert not physical
    assert g.generation_calls == 0


@pytest.mark.parametrize("kind", ["generation", "embedding"])
def test_tier_region_or_multiplier_unverified_never_sends(tmp_path, kind):
    cases = [
        {"region": "regional"},
        {"regional_surcharge_applies": True},
        {"service_tier": "priority"},
        {"multiplier": "2"},
    ]
    for delta in cases:
        snapshot = valid_pricing_dict()
        snapshot.update(delta)
        try:
            attestation = remote.load_pricing_snapshot(
                pricing_file(tmp_path, snapshot), now=pricing_clock())
        except remote.Blocked:
            continue
        pytest.fail("unapproved pricing configuration accepted")


def test_full_export_contains_config_timestamp_and_unreviewed_rubric(tmp_path):
    fake = FakeProvider()
    records = remote.run_pilot(fake, fake, guard())
    remote.save_report(records, tmp_path)
    first = json.loads((tmp_path / "rag-001-results.jsonl").read_text().splitlines()[0])
    assert first["timestamp_utc"]
    assert first["service_tier"] == "default"
    assert first["reasoning_effort"] == "none"
    assert first["max_output_tokens"] == 1024
    for key in (
        "review_abstention_appropriate", "review_justified_negative",
        "review_safe_refusal", "review_error", "reviewed_at_utc"
    ):
        assert key in first and first[key] is None


@pytest.mark.parametrize("status,error", [
    ("incomplete", remote.Inconclusive),
    ("failed", remote.Inconclusive),
    ("completed", remote.Inconclusive),
])
def test_generation_sdk_incomplete_or_usage_absent(monkeypatch, status, error):
    class ResponsesFake:
        def create(self, **kwargs):
            usage = None if status == "completed" else types.SimpleNamespace(
                input_tokens=1, output_tokens=1)
            return types.SimpleNamespace(
                status=status, usage=usage, service_tier="default",
                output_text='{"answer":"x","abstained":false,"citations":[]}',
                model=remote.GEN_MODEL
            )
    class SDKFake:
        def __init__(self, **kwargs):
            self.responses = ResponsesFake()
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SDKFake))
    with pytest.raises(error):
        remote.OpenAIAdapter("sk-test-sentinel").generate("Pergunta", [])


@pytest.mark.parametrize("http_status", [408, 409, 429, 500, 502, 503])
def test_provider_http_failure_is_single_attempt_without_retry(monkeypatch, http_status):
    physical = []
    class ResponsesFake:
        def create(self, **kwargs):
            physical.append(http_status)
            raise RuntimeError(f"HTTP {http_status} sk-test-sentinel")
    class SDKFake:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.responses = ResponsesFake()
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SDKFake))
    try:
        remote.OpenAIAdapter("sk-test-sentinel").generate("Pergunta", [])
    except RuntimeError as exc:
        assert remote.error_code(exc) == "PROVIDER_UNAVAILABLE"
    else:
        pytest.fail("expected provider exception")
    assert physical == [http_status]


def test_embedding_failure_consumes_one_reserved_attempt_and_stops(tmp_path):
    class BrokenEmbedding(FakeProvider):
        def embed(self, texts):
            self.embeddings.append(list(texts))
            raise TimeoutError("Bearer sk-test-sentinel")
    fake = BrokenEmbedding()
    limit = guard()
    rows = remote.run_pilot(fake, fake, limit)
    assert len(fake.embeddings) == 1
    assert limit.embedding_requests == 1
    assert rows[0]["status"] == "INCONCLUSIVE"
    remote.save_report(rows, tmp_path)
    assert "sk-test-sentinel" not in "".join(p.read_text() for p in tmp_path.iterdir())
