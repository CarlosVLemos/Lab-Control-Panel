"""Opt-in integration check for the operator-provided real SWE-bench files."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from app.experiments.swebench_verified import import_pair

DATASET_DIR = os.getenv("LCP_DATASETS_DIR")


@pytest.mark.skipif(not DATASET_DIR, reason="LCP_DATASETS_DIR is not set")
def test_exp002_real_pair_matches_manifest_and_importer():
    root = Path(DATASET_DIR)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    entries = {entry["path"]: entry for entry in manifest["files"]}
    left_relative = "swebench/swebench_verified_raw/gpt-5.2-codex/astropy__astropy-12907/astropy__astropy-12907.traj.json"
    right_relative = "swebench/swebench_verified_raw/gpt-5-mini/astropy__astropy-12907/astropy__astropy-12907.traj.json"
    left, right = root / left_relative, root / right_relative

    for relative, path in ((left_relative, left), (right_relative, right)):
        payload = path.read_bytes()
        assert len(payload) == entries[relative]["bytes"]
        assert hashlib.sha256(payload).hexdigest() == entries[relative]["sha256"]

    result = import_pair(
        left, right,
        left_sha256=entries[left_relative]["sha256"],
        right_sha256=entries[right_relative]["sha256"],
    )
    assert result["instance_id"] == "astropy__astropy-12907"
    assert [run["model"] for run in result["runs"]] == ["gpt-5.2-codex", "gpt-5-mini"]
    assert [run["published_resolved"] for run in result["runs"]] == [True, True]
    assert [run["patch_status"] for run in result["runs"]] == ["not_recorded", "not_recorded"]
