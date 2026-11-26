#!/usr/bin/env python3
"""历史 PNG→无损 WebP 重建工具；当前 WebP 源不适用。

仅当输入 `#tut-data` 仍含 48 张 PNG 时使用；禁止对当前源文件执行 `--in-place`。

为什么是无损：用户要求「清晰度不变」。无损 WebP 解码后与 PNG **逐像素相同**
（PSNR = ∞），不做任何有损量化；体积仍能降约 31%。

除图片载荷外，HTML/CSS/JS/JSON 一律不动：按 `#tut-data` 切开后只对 JSON 正文
做 `data:image/png;base64,…` → `data:image/webp;base64,…` 的等位置换，
head / tail 逐字节比较。

用法：
    python perf/tools/build_lossless.py            # 写 perf/dist/…lossless.html
    python perf/tools/build_lossless.py --in-place # 校验通过后覆盖源文件
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
HTML = REPO / "Meow Star Map 官网.html"
ASSETS = ROOT / "assets"
SHOTS = ASSETS / "shots"
WEBP_LOSSLESS = ASSETS / "webp" / "lossless"
MANIFEST = ASSETS / "manifest.json"
DIST = ROOT / "dist"
REPORTS = ROOT / "reports"

TUT_OPEN = '<script id="tut-data" type="application/json">'
TUT_CLOSE = "</script>"
PNG_RE = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")
WEBP_RE = re.compile(r"data:image/webp;base64,([A-Za-z0-9+/=]+)")

INVARIANTS = {
    "外链 link": r"<link\b(?![^>]*href=[\"']data:)",
    "script src": r"<script[^>]*\bsrc=",
    "iframe": r"<iframe\b",
    "外链 img": r"<img[^>]*\bsrc=[\"']https?:",
    "url(http)": r"url\(\s*[\"']?https?:",
    "@font-face{": r"@font-face\s*\{",
    "img": r"<img\b",
    "style": r"<style\b",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_tut(text: str):
    start = text.index(TUT_OPEN) + len(TUT_OPEN)
    pos = start
    while True:
        end = text.index(TUT_CLOSE, pos)
        body = text[start:end]
        try:
            json.loads(body)
        except json.JSONDecodeError:
            pos = end + len(TUT_CLOSE)
            continue
        return text[:start], body, text[end:]


def placeholder_json(body: str):
    """把所有 data: 图片载荷替换为占位符，用于结构等价比对。"""
    clean = re.sub(r"data:image/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]+", "@IMG@", body)
    return json.loads(clean)


def node_check_scripts(text: str) -> tuple[int, list[str]]:
    blocks = re.findall(r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S)
    js = [b for b in blocks if b.strip() and not b.lstrip().startswith("{")]
    errors = []
    with tempfile.TemporaryDirectory() as td:
        for i, body in enumerate(js):
            p = Path(td) / f"b{i}.js"
            p.write_text(body, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
            if r.returncode != 0:
                errors.append(f"block {i}: {r.stderr.strip()[:300]}")
    return len(js), errors


def pixel_identical(png_path: Path, webp_bytes: bytes) -> bool:
    from PIL import Image, ImageChops

    with Image.open(png_path) as a, Image.open(io.BytesIO(webp_bytes)) as b:
        a.load()
        b.load()
        if a.mode != b.mode or a.size != b.size:
            return False
        return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-place", action="store_true", help="校验通过后覆盖源文件")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_sha: dict[str, bytes] = {}
    for rec in manifest["shots"]:
        p = WEBP_LOSSLESS / (rec["file"][:-4] + ".webp")
        by_sha[rec["sha256"]] = p.read_bytes()

    raw = HTML.read_bytes()
    text = raw.decode("utf-8")
    old_bytes = len(raw)
    head, body, tail = split_tut(text)
    # 尾巴从 </script> 开始，但 `dev-data` 紧挨着，这里只切 tut 块，tail 未动。

    occurrences = PNG_RE.findall(body)
    if len(occurrences) != 48:
        print(f"FAIL: 期望 48 处 PNG，实际 {len(occurrences)}")
        return 1

    replaced = 0
    mismatch = []

    def repl(m):
        nonlocal replaced
        png = base64.b64decode(m.group(1))
        webp = by_sha.get(sha(png))
        if webp is None:
            mismatch.append(sha(png))
            return m.group(0)
        replaced += 1
        return "data:image/webp;base64," + base64.b64encode(webp).decode("ascii")

    new_body = PNG_RE.sub(repl, body)
    if mismatch:
        print(f"FAIL: {len(mismatch)} 张 PNG 没有对应 WebP")
        return 1

    new_text = head + new_body + tail
    new_bytes = new_text.encode("utf-8")

    # ── 结构等价 ──
    checks = []
    checks.append(("head 逐字节相同", head == split_tut(new_text)[0]))
    checks.append(("tail 逐字节相同", tail == split_tut(new_text)[2]))
    checks.append(("JSON 结构等价（载荷占位后）", placeholder_json(body) == placeholder_json(new_body)))
    checks.append(("PNG 载荷归零", len(PNG_RE.findall(new_body)) == 0))
    checks.append(("WebP 载荷 48 处", len(WEBP_RE.findall(new_body)) == 48))
    checks.append(("替换处数 48", replaced == 48))

    for name, pattern in INVARIANTS.items():
        before = len(re.findall(pattern, text))
        after = len(re.findall(pattern, new_text))
        checks.append((f"不变量 {name}: {before} == {after}", before == after))

    crlf_before = text.count("\r\n")
    crlf_after = new_text.count("\r\n")
    checks.append((f"CRLF 计数 {crlf_before} == {crlf_after}", crlf_before == crlf_after))

    # ── 逐像素复核（从最终文本解出 48 张 WebP，与 PNG 原图比） ──
    final_images = WEBP_RE.findall(new_body)
    png_by_sha = {}
    for rec in manifest["shots"]:
        png_by_sha[rec["sha256"]] = SHOTS / rec["file"]
    # 按出现顺序：tut JSON 里的 48 处与 manifest 的 48 个 sha（unique）一一对应
    sha_of_webp = {sha(v): k for k, v in by_sha.items()}
    bad = []
    seen = set()
    for i, b64 in enumerate(final_images):
        data = base64.b64decode(b64)
        key = sha_of_webp.get(sha(data))
        if key is None:
            bad.append(i)
            continue
        seen.add(key)
        if not pixel_identical(png_by_sha[key], data):
            bad.append(i)
    checks.append((f"48 张逐像素一致（失败 {len(bad)}）", not bad))
    checks.append(("48 张唯一图全覆盖", len(seen) == 48))

    # ── JS 块编译 ──
    js_count, js_errors = node_check_scripts(new_text)
    checks.append((f"{js_count} 个 JS 块 node --check 通过", not js_errors))

    ok = all(flag for _, flag in checks)
    for name, flag in checks:
        print(("PASS " if flag else "FAIL ") + name)
    for e in js_errors:
        print("  JS ERROR", e)

    print(f"\n源文件      : {old_bytes:,} B ({old_bytes / 1048576:.2f} MiB)")
    print(f"优化后      : {len(new_bytes):,} B ({len(new_bytes) / 1048576:.2f} MiB)  "
          f"降幅 {100 * (1 - len(new_bytes) / old_bytes):.1f}%")
    print(f"图片载荷    : {sum(len(v) for v in by_sha.values()):,} B 无损 WebP（PNG 22.09 MiB）")
    if not ok:
        print("未通过全部断言，不写出。")
        return 1

    DIST.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = DIST / (HTML.stem + ".lossless.html")
    out.write_bytes(new_bytes)
    meta = {
        "built_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "mode": "lossless",
        "source": {"bytes": old_bytes, "sha256": sha(raw)},
        "output": {"file": out.name, "bytes": len(new_bytes), "sha256": sha(new_bytes)},
        "images": {"count": 48, "png_bytes": sum(r["bytes"] for r in manifest["shots"]),
                   "webp_bytes": sum(len(v) for v in by_sha.values())},
        "checks": [{"name": n, "pass": f} for n, f in checks],
    }
    (REPORTS / "build-lossless.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
    print(f"产物        : {out}")

    if args.in_place:
        HTML.write_bytes(new_bytes)
        print(f"已覆盖源文件: {HTML}")
    else:
        print("（未覆盖源文件；追加 --in-place 生效）")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
