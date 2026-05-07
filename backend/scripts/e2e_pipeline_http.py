"""HTTP 端到端：health + analyze/text +（可选）analyze/mixed（含中文 OCR 图）。

Windows 下同一进程内 Paddle OCR 与 PyTorch(Qwen) 叠加可能导致进程崩溃；
可设 ``LINGJIAN_E2E_SKIP_MIXED=1`` 或传入 ``--skip-mixed`` 仅测文本链路。

需设置 ``LINGJIAN_ACCESS_TOKEN``（登录接口返回的 access_token），调用 ``POST /api/v1/auth/login`` 获取。
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "backend" / "uploads" / "_e2e_pipeline_result.json"
BASE = "http://127.0.0.1:8000"


def get(url: str, timeout: float = 30.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def auth_headers_json() -> dict[str, str]:
    tok = os.getenv("LINGJIAN_ACCESS_TOKEN", "").strip()
    h = {"Content-Type": "application/json; charset=utf-8"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def post_json(url: str, payload: dict, timeout: float = 900.0) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers=auth_headers_json(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_mixed(text: str, png: Path, timeout: float = 900.0) -> dict:
    import http.client
    import mimetypes

    boundary = "lingjianBoundaryE2E"
    parts: list[bytes] = []

    def add_text(name: str, value: str) -> None:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")

    add_text("text", text)
    ctype = mimetypes.guess_type(str(png))[0] or "image/png"
    raw = png.read_bytes()
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{png.name}"\r\n'.encode()
    )
    parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
    parts.append(raw)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=int(timeout))
    try:
        h = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        tok = os.getenv("LINGJIAN_ACCESS_TOKEN", "").strip()
        if tok:
            h["Authorization"] = f"Bearer {tok}"
        conn.request(
            "POST",
            "/api/v1/analyze/mixed",
            body=body,
            headers=h,
        )
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {data[:500]}")
        return json.loads(data)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-mixed",
        action="store_true",
        help="跳过图文 mixed（避免 Win 上 Paddle+Torch 同进程不稳定）",
    )
    args = parser.parse_args()
    skip_mixed = args.skip_mixed or os.getenv("LINGJIAN_E2E_SKIP_MIXED", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    for _ in range(60):
        try:
            h = get(f"{BASE}/health", timeout=5)
            if h.get("status") == "ok":
                break
        except OSError:
            time.sleep(1)
    else:
        raise SystemExit("server /health not ready")

    img_dir = ROOT / "backend" / "uploads"
    img_dir.mkdir(parents=True, exist_ok=True)
    png = img_dir / "_e2e_cn_flow.png"
    if not png.is_file():
        from PIL import Image, ImageDraw, ImageFont

        im = Image.new("RGB", (900, 240), (255, 255, 255))
        d = ImageDraw.Draw(im)
        font = None
        for fp in [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
        ]:
            try:
                font = ImageFont.truetype(fp, 56)
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()
        d.text((20, 80), "这款保健品能根治癌症三天见效", fill=(0, 0, 0), font=font)
        im.save(png)

    text_payload = {
        "text": "这款保健品能彻底根治癌症，三天见效。权威专家推荐。",
        "content_id": "e2e-text-1",
    }
    out: dict = {"health": get(f"{BASE}/health"), "text_analyze": {}, "mixed_analyze": {}}
    out["text_analyze"] = post_json(f"{BASE}/api/v1/analyze/text", text_payload)
    if skip_mixed:
        out["mixed_analyze"] = {
            "skipped": True,
            "reason": "--skip-mixed or LINGJIAN_E2E_SKIP_MIXED",
        }
    else:
        out["mixed_analyze"] = post_mixed("附图说明：网友转发", png)
    out["meta"] = {
        "note": "若 LINGJIAN_LLM_ADAPTER 目录无 adapter_model.safetensors，则仍为基座 Qwen。",
        "skip_mixed": skip_mixed,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    main()
