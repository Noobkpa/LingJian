"""POST /api/v1/analyze/text once; long timeout for Qwen load + generate。

需设置环境变量 LINGJIAN_ACCESS_TOKEN（通过 POST /api/v1/auth/login 获取）。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
TIMEOUT_SEC = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
OUT = Path(__file__).resolve().parents[1] / "uploads" / "_last_analyze_qwen.json"


def wait_health(max_wait: float = 120.0) -> None:
    deadline = time.time() + max_wait
    url = f"{BASE}/health"
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=5)
            return
        except OSError:
            time.sleep(0.5)
    raise SystemExit("server /health not ready")


def main() -> None:
    wait_health()
    payload = {
        "text": "这款保健品能彻底根治癌症，三天见效。权威专家推荐。",
        "content_id": "qwen-retry-1",
    }
    tok = os.getenv("LINGJIAN_ACCESS_TOKEN", "").strip()
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(
        f"{BASE}/api/v1/analyze/text",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {body}") from e
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {OUT}")
    llm = data.get("llm") or {}
    raw = (llm.get("raw_output") or "")[:200]
    print("llm.risk_level:", llm.get("risk_level"))
    print("llm.raw_output prefix:", repr(raw))


if __name__ == "__main__":
    main()
