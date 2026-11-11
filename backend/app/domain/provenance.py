"""Canonical content hashes for versioned experiment inputs.

A SHA-256 fingerprint identifies a snapshot; it does not authenticate its origin
or replace signed/audited storage. No model secrets should enter these payloads.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def content_fingerprint(payload: Any) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
