"""Ensure AI coding guidance stays discoverable, concise and evidence-based."""

from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[2]
ROLES = ("jarvis", "maquiavel", "van-gogh", "mefisto")


def test_root_instructions_are_short_and_actionable():
    text = (ROOT / "AGENTS.md").read_text()
    assert len(text.split()) < 270
    assert "SDD/rules.md" in text
    assert "python -m pytest" in text
    assert "README" in text
    assert "untrusted" in text


def test_risk_tracks_and_human_gates_are_defined():
    rules = (ROOT / "SDD/rules.md").read_text()
    for token in ("QUICK", "STANDARD", "CRITICAL", "FROZEN", "Change Request",
                  "Mefisto", "Allowed paths", "NOT_RUN", "passed_with_restrictions"):
        assert token in rules


def test_skills_have_discoverable_metadata_and_separation():
    for name in ("lcp-implement-issue", "lcp-review-change"):
        path = ROOT / ".agents" / "skills" / name / "SKILL.md"
        text = path.read_text()
        assert text.startswith("---\n")
        frontmatter = text.split("---", 2)[1]
        assert f"name: {name}" in frontmatter
        assert "description:" in frontmatter
        assert "SDD/rules.md" in text
        assert "NOT_RUN" in text
    assert "independent" in (ROOT / ".agents/skills/lcp-review-change/SKILL.md").read_text()


def test_role_profiles_still_load():
    for role in ROLES:
        cfg = tomllib.loads((ROOT / ".codex/agents" / f"{role}.toml").read_text())
        assert cfg["description"]
        assert "SDD/rules.md" in cfg["developer_instructions"]
        agent = (ROOT / ".github/agents" / f"{role}.agent.md").read_text()
        assert agent.startswith("---\n")
        assert "description:" in agent


def test_pr_template_makes_missing_evidence_explicit():
    text = (ROOT / ".github/pull_request_template.md").read_text()
    assert "CRITICAL" in text
    assert "NOT_RUN" in text
    assert "Human approval" in text
