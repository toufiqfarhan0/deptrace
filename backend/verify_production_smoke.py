"""
Veridex Production Deployment Smoke Test Runner (Step 17E).

Safely tests an active Veridex server (in-process, local uvicorn, or deployed on Render)
without ingesting any data. Verifies health checks, RAG asking, dependency tracing,
static frontend serving, provenance preservation, and strict secret redaction.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z\-_]{25,}"),
    re.compile(r"Bearer\s+ey[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"key=ey[A-Za-z0-9_\-\.]+", re.IGNORECASE),
]


def check_for_leaked_secrets(text: str) -> list[str]:
    """Return any leaked secret patterns found in response text."""
    leaks = []
    for pat in SECRET_PATTERNS:
        matches = pat.findall(text)
        if matches:
            leaks.extend(matches)
    return leaks


class TestHttpClient:
    """Unified client supporting both live HTTP endpoints and in-process FastAPI TestClient."""

    def __init__(self, base_url: str | None = None, in_process: bool = False) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.in_process = in_process
        self.test_client = None

        if in_process or not base_url:
            from starlette.testclient import TestClient
            from backend.api.app import app
            self.test_client = TestClient(app)

    def get(self, path: str, timeout: float = 15.0):
        if self.test_client:
            return self.test_client.get(path)
        return requests.get(f"{self.base_url}{path}", timeout=timeout)

    def post(self, path: str, json_data: dict[str, Any], timeout: float = 30.0):
        if self.test_client:
            return self.test_client.post(path, json=json_data)
        return requests.post(f"{self.base_url}{path}", json=json_data, timeout=timeout)


def run_smoke_tests(base_url: str | None = None, in_process: bool = False) -> bool:
    client = TestHttpClient(base_url=base_url, in_process=in_process)
    target_desc = f"In-Process FastAPI Application (HYDRA_MODE={os.getenv('HYDRA_MODE', 'local')})" if client.test_client else base_url

    print("=" * 80)
    print(f"VERIDEX PRODUCTION SMOKE TEST RUNNER")
    print(f"Target: {target_desc}")
    print("=" * 80)

    all_passed = True

    # 1. GET /api/health
    print("\n1. Testing GET /api/health...")
    try:
        t0 = time.perf_counter()
        res = client.get("/api/health", timeout=15)
        lat = (time.perf_counter() - t0) * 1000
        print(f"   HTTP Status: {res.status_code} ({lat:.1f}ms)")
        print(f"   Response:    {res.json()}")
        if res.status_code != 200 or res.json().get("status") != "ok":
            print(f"   FAILED: Health check degraded or unreachable.", file=sys.stderr)
            all_passed = False
        else:
            print("   PASSED: Health check ok.")
    except Exception as exc:
        print(f"   FAILED: Health check network exception: {exc}", file=sys.stderr)
        all_passed = False

    # 2. GET / (Frontend root)
    print("\n2. Testing GET / (Frontend root HTML)...")
    try:
        res = client.get("/", timeout=15)
        print(f"   HTTP Status: {res.status_code}")
        print(f"   Content-Type: {res.headers.get('content-type')}")
        if res.status_code == 200 and "<html" in res.text.lower():
            print("   PASSED: Frontend static bundle served successfully.")
        else:
            print(f"   FAILED: Root path did not return HTML.", file=sys.stderr)
            all_passed = False
    except Exception as exc:
        print(f"   FAILED: Root path exception: {exc}", file=sys.stderr)
        all_passed = False

    # 3. POST /api/ask with representative questions
    ask_queries = [
        "What is PR-99501 about?",
        "What is connected to api-search?",
        "What is connected to kernel-selector?",
    ]

    print("\n3. Testing POST /api/ask questions...")
    for q in ask_queries:
        print(f"\n   Query: \"{q}\"")
        try:
            t0 = time.perf_counter()
            res = client.post(
                "/api/ask",
                json_data={"question": q, "retrieval_limit": 5},
                timeout=30,
            )
            lat = (time.perf_counter() - t0) * 1000
            print(f"   HTTP Status: {res.status_code} ({lat:.1f}ms)")

            if res.status_code != 200:
                print(f"   FAILED: /api/ask returned {res.status_code}: {res.text}", file=sys.stderr)
                all_passed = False
                continue

            data = res.json()
            evidence = data.get("evidence", [])
            print(f"   Grounded:       {data.get('grounded')}")
            print(f"   Evidence Count: {len(evidence)}")
            print(f"   Answer Snippet: {data.get('answer', '')[:120]}...")

            # Provenance and Secret checks
            raw_text = res.text
            leaks = check_for_leaked_secrets(raw_text)
            if leaks:
                print(f"   FAILED: Leaked secret patterns detected in response: {leaks}", file=sys.stderr)
                all_passed = False
            else:
                print("   PASSED: Zero secrets detected in payload.")

            for ev in evidence:
                if not ev.get("document_id") or not ev.get("statement"):
                    print(f"   FAILED: Evidence item missing document_id or statement: {ev}", file=sys.stderr)
                    all_passed = False
                    break
            else:
                print("   PASSED: All evidence items maintain valid document_id provenance.")

        except Exception as exc:
            print(f"   FAILED: /api/ask exception: {exc}", file=sys.stderr)
            all_passed = False

    # 4. POST /api/trace with target entity
    print("\n4. Testing POST /api/trace for 'PR-99501'...")
    try:
        t0 = time.perf_counter()
        res = client.post(
            "/api/trace",
            json_data={"entity": "PR-99501", "max_depth": 2, "limit": 10},
            timeout=20,
        )
        lat = (time.perf_counter() - t0) * 1000
        print(f"   HTTP Status: {res.status_code} ({lat:.1f}ms)")

        if res.status_code != 200:
            print(f"   FAILED: /api/trace returned {res.status_code}: {res.text}", file=sys.stderr)
            all_passed = False
        else:
            data = res.json()
            print(f"   Found:          {data.get('found')}")
            print(f"   Hops Count:     {len(data.get('dependency_hops', []))}")
            print(f"   Timeline Items: {len(data.get('timeline', []))}")

            leaks = check_for_leaked_secrets(res.text)
            if leaks:
                print(f"   FAILED: Leaked secrets in /api/trace: {leaks}", file=sys.stderr)
                all_passed = False
            else:
                print("   PASSED: Zero secrets in trace response.")

    except Exception as exc:
        print(f"   FAILED: /api/trace exception: {exc}", file=sys.stderr)
        all_passed = False

    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print(">>> ALL PRODUCTION SMOKE TESTS PASSED SUCCESSFULLY! <<<")
    else:
        print(">>> SMOKE TESTS ENCOUNTERED FAILURES! <<<", file=sys.stderr)
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Veridex production smoke test runner")
    parser.add_argument("--url", default=None, help="Target remote/local server URL (optional, defaults to in-process)")
    parser.add_argument("--in-process", action="store_true", help="Force in-process Starlette test client")
    args = parser.parse_args()

    success = run_smoke_tests(base_url=args.url, in_process=args.in_process)
    sys.exit(0 if success else 1)
