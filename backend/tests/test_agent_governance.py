"""Validate agent configuration without requiring Codex or Copilot at CI runtime."""

from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ("jarvis", "maquiavel", "van-gogh", "mefisto")
CANONICAL = ("Jarvis", "Maquiavel", "Van Gogh", "Mefisto")


def test_single_governance_source_and_templates():
    rules = (ROOT / "SDD/rules.md").read_text()
    assert (ROOT / "AGENTS.md").exists()
    assert "single normative source" in rules
    for name in CANONICAL:
        assert name in rules
    for template in ("spec", "tasks", "contract", "tests", "validation-result", "review"):
        assert (ROOT / "SDD/templates" / f"{template}.md").is_file()
    assert "FROZEN" in rules and "Change Request" in rules
    assert "PARALLEL_SAFE" in rules and "SINGLE_WRITER" in rules


def test_codex_and_copilot_profiles():
    for filename in AGENTS:
        copilot = (ROOT / ".github/agents" / f"{filename}.agent.md").read_text()
        assert copilot.startswith("---\n")
        assert "description:" in copilot.split("---", 2)[1]
        assert "SDD/rules.md" in copilot

        codex = tomllib.loads((ROOT / ".codex/agents" / f"{filename}.toml").read_text())
        assert codex["name"] and codex["description"]
        assert "SDD/rules.md" in codex["developer_instructions"]
        assert "AGENTS.md" in codex["developer_instructions"]


def test_agent_rules_keep_development_separate_from_product_evaluation():
    rules = (ROOT / "SDD/rules.md").read_text()
    assert "development agents" in rules.lower()
    assert "Response, Task and Code" in rules
    assert "do not supersede product PolicyDecision" in rules
