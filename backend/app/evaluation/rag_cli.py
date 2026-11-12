"""Offline RAG-001 manifest; --dry-run never invokes an embedding or generation service."""
from __future__ import annotations
import argparse
import json
from .rag import CASES, POLICIES, fingerprint

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args(argv)
    if args.top_k <= 0: parser.error("--top-k must be positive")
    print(json.dumps({"experiment": "RAG-001", "dry_run": args.dry_run, "top_k": args.top_k, "documents": len(POLICIES), "cases": len(CASES), "fingerprint": fingerprint(POLICIES, CASES), "telemetry": None}, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
