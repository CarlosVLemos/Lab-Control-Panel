from app.evaluation.rag import Answer, CASES, POLICIES, Document, RagCase, VectorIndex, cosine, evaluate, fingerprint

class FakeEmbedder:
    def embed(self, text):
        return [1.0, 0.0] if "shipping" in text or "Prazo" in text else [0.0, 1.0]

def test_versioned_fixture_has_36_cases_and_fingerprint():
    assert len(CASES) == 36
    assert len(POLICIES) == 12
    assert len(fingerprint(POLICIES, CASES)) == 64
    assert sum(case.expected_answer is None for case in CASES) == 12
    assert {case.category for case in CASES} == {"factual", "synthesis", "missing", "adversarial"}

def test_cosine_index_and_top_k_are_deterministic():
    index = VectorIndex((Document("a", "shipping"), Document("b", "returns")), FakeEmbedder())
    assert [item.id for item in index.search("shipping", 1)] == ["a"]
    assert cosine([1, 0], [1, 0]) == 1.0

def test_deterministic_answer_source_and_abstention_evaluation():
    grounded = RagCase("x", "q", "free", ("shipping",), expected_facts=("shipping.standard.5d",))
    assert evaluate(grounded, Answer("paraphrase", ("shipping",), ("shipping.standard.5d",))).answer_correct
    assert evaluate(RagCase("y", "q", None), Answer(None)).abstention_correct
    assert not evaluate(RagCase("y", "q", None), Answer("invented")).abstention_correct

def test_fingerprint_changes_for_categories_and_facts():
    changed = RagCase(**{**CASES[0].__dict__, "category": "adversarial"})
    assert fingerprint(POLICIES, CASES) != fingerprint(POLICIES, (changed, *CASES[1:]))
