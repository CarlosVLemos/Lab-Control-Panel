from app.evaluation.rag import Answer, CASES, POLICIES, Document, RagCase, VectorIndex, cosine, evaluate, fingerprint

class FakeEmbedder:
    def embed(self, text):
        return [1.0, 0.0] if "shipping" in text or "Prazo" in text else [0.0, 1.0]

def test_versioned_fixture_has_36_cases_and_fingerprint():
    assert len(CASES) == 36
    assert len(POLICIES) == 12
    assert len(fingerprint(POLICIES, CASES)) == 64
    assert sum(case.expected_answer is None for case in CASES) == 10
    assert len({case.id for case in CASES}) == 36
    assert {case.category for case in CASES} == {"factual", "synthesis", "missing", "adversarial"}

def test_cosine_index_and_top_k_are_deterministic():
    index = VectorIndex((Document("a", "shipping"), Document("b", "returns")), FakeEmbedder())
    assert [item.id for item in index.search("shipping", 1)] == ["a"]
    assert cosine([1, 0], [1, 0]) == 1.0

def test_deterministic_answer_source_and_abstention_evaluation():
    grounded = RagCase("x", "q", "free", ("shipping",), expected_facts=("shipping.standard.5d",))
    result = evaluate(grounded, Answer("entrega em 300 dias", ("shipping",), ("shipping.standard.5d",)))
    assert result.facts_match
    assert result.semantic_correctness == "NOT_EVALUATED"
    assert result.expected_sources_present
    assert result.citations_match_expected
    assert evaluate(RagCase("y", "q", None), Answer(None)).abstention_correct
    assert not evaluate(RagCase("y", "q", None), Answer("invented")).abstention_correct


def test_source_coverage_does_not_validate_extra_citations():
    grounded = RagCase("x", "q", "free", ("shipping",), expected_facts=("shipping.standard.5d",))
    result = evaluate(grounded, Answer("cinco dias", ("shipping", "fabricated"), ("shipping.standard.5d",)))
    assert result.expected_sources_present
    assert not result.citations_match_expected


def test_synthesis_cases_require_multiple_sources_and_facts():
    synthesis = [case for case in CASES if case.category == "synthesis"]
    assert len(synthesis) == 6
    assert all(len(case.expected_sources) >= 2 and len(case.expected_facts) >= 2 for case in synthesis)


def test_version_conflict_uses_v2_and_adversarial_cases_are_marked():
    versions = {document.id: document.version for document in POLICIES}
    current_shipping = [case for case in CASES if "shipping.standard.4d" in case.expected_facts]
    assert current_shipping and all("shipping-v2" in case.expected_sources for case in current_shipping)
    assert versions["shipping-v2"] == "v2"
    conflicting_source = evaluate(current_shipping[0], Answer("quatro dias", ("shipping",), ("shipping.standard.4d",)))
    assert not conflicting_source.expected_sources_present
    assert all(case.adversarial for case in CASES if case.category == "adversarial")
    assert all(not case.adversarial for case in CASES if case.category != "adversarial")


def test_delivery_synthesis_compares_versions_and_uses_current_six_day_credit():
    delivery = next(case for case in CASES if case.question.startswith("Como os prazos"))
    current_policy = next(document for document in POLICIES if document.id == "shipping-v2")
    assert delivery.expected_sources == ("shipping", "shipping-v2")
    assert set(delivery.expected_facts) == {
        "shipping.standard.5d", "shipping.credit.7d",
        "shipping.standard.4d", "shipping.credit.6d",
    }
    assert "6 dias" in current_policy.text


def test_known_negative_policies_are_not_missing_abstentions():
    lifetime_return = next(case for case in CASES if "devolução vitalícia" in case.question)
    unlimited_coupons = next(case for case in CASES if "cupons ilimitados" in case.question)
    assert lifetime_return.category == "factual" and lifetime_return.expected_sources == ("returns",)
    assert unlimited_coupons.category == "factual" and unlimited_coupons.expected_sources == ("coupons",)
    assert all("devolução vitalícia" not in case.question and "cupons ilimitados" not in case.question for case in CASES if case.category == "missing")

def test_fingerprint_changes_for_categories_facts_and_sources():
    changed_category = RagCase(**{**CASES[0].__dict__, "category": "adversarial"})
    changed_fact = RagCase(**{**CASES[0].__dict__, "expected_facts": ("shipping.credit.7d",)})
    changed_source = RagCase(**{**CASES[0].__dict__, "expected_sources": ("shipping-v2",)})
    assert fingerprint(POLICIES, CASES) != fingerprint(POLICIES, (changed_category, *CASES[1:]))
    assert fingerprint(POLICIES, CASES) != fingerprint(POLICIES, (changed_fact, *CASES[1:]))
    assert fingerprint(POLICIES, CASES) != fingerprint(POLICIES, (changed_source, *CASES[1:]))
