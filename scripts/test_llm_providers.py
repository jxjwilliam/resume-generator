#!/usr/bin/env python3
"""
Smoke-test all configured LLM providers against jds/*.txt.

Usage:
  python scripts/test_llm_providers.py
  python scripts/test_llm_providers.py --provider deepseek
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)

from src.llm_config import list_providers, resolve_llm_config
from resume import load_base, llm_extract_tags, llm_generate_headline, llm_generate_summary


def _ok(text: str, *, min_len: int = 5) -> bool:
    if not text or len(text.strip()) < min_len:
        return False
    lower = text.lower()
    if "redacted_thinking" in lower or "<think>" in lower or "<thinking>" in lower:
        return False
    # Reject leaked chain-of-thought from reasoning models
    leaked = (
        "the user wants",
        "we need to",
        "let me analyze",
        "i need to",
    )
    if any(lower.startswith(p) for p in leaked):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Test LLM providers with jds/*.txt")
    parser.add_argument("--provider", choices=[p["id"] for p in list_providers()])
    args = parser.parse_args()

    jds = sorted((ROOT / "jds").glob("*.txt"))
    if not jds:
        print("No JD files found in jds/", file=sys.stderr)
        return 1

    providers = [args.provider] if args.provider else [p["id"] for p in list_providers()]
    base = load_base()

    passed = 0
    failed = 0

    print(f"Testing {len(providers)} provider(s) × {len(jds)} JD file(s)\n")

    for provider in providers:
        try:
            cfg = resolve_llm_config(provider)
        except ValueError as e:
            print(f"[{provider}] SKIP — {e}")
            failed += len(jds) * 3
            continue

        if not cfg["api_key"]:
            print(f"[{provider}] SKIP — no API key ({cfg['label']})")
            failed += len(jds) * 3
            continue

        print(f"=== {cfg['label']} ({cfg['model']}) ===")

        for jd_path in jds:
            jd_text = jd_path.read_text(encoding="utf-8")
            role = jd_path.stem.replace("-", " ").title()
            label = jd_path.name

            tags = llm_extract_tags(jd_text, base, llm_provider=provider)
            headline = llm_generate_headline(jd_text, role, llm_provider=provider)
            summary = llm_generate_summary(jd_text, base, role, llm_provider=provider)

            checks = [
                ("tags", tags, 10),
                ("headline", headline, 10),
                ("summary", summary, 40),
            ]

            for name, text, min_len in checks:
                ok = _ok(text, min_len=min_len)
                status = "PASS" if ok else "FAIL"
                preview = (text[:70] + "…") if text and len(text) > 70 else (text or "(empty)")
                print(f"  {label:20} {name:10} {status:4}  {preview}")
                if ok:
                    passed += 1
                else:
                    failed += 1

        print()

    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
