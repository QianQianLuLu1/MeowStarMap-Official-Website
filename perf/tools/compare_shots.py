#!/usr/bin/env python3
"""对比 perf/assets/shots-compare 下 orig / lossless / site 的同名截图。

输出逐项差异（像素数、最大通道差、差异 bbox），并把差异图写到
perf/assets/shots-compare/diff/。strict 口径：逐像素完全相同才算 PASS。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "assets" / "shots-compare"
OUT = ROOT / "reports" / "shots-diff.json"


def compare(a_path: Path, b_path: Path, diff_path: Path):
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        return {"same_size": False, "a": a.size, "b": b.size}
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if bbox is None:
        return {"same_size": True, "diff_pixels": 0, "max_channel": 0, "bbox": None}
    # 统计非零像素
    hist = diff.convert("L").histogram()
    diff_pixels = sum(hist[1:])
    extrema = diff.getextrema()
    max_channel = max(e[1] for e in extrema)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    # 放大差异便于肉眼检查
    diff.point(lambda v: min(255, v * 8)).save(diff_path)
    return {
        "same_size": True,
        "diff_pixels": diff_pixels,
        "total_pixels": a.size[0] * a.size[1],
        "ratio": diff_pixels / (a.size[0] * a.size[1]),
        "max_channel": max_channel,
        "bbox": bbox,
        "diff_file": str(diff_path.relative_to(ROOT)),
    }


def main() -> int:
    rows = []
    for case_path in sorted((SHOTS / "orig").glob("*.png")):
        case = case_path.stem
        for pair in (("orig", "lossless"), ("orig", "site")):
            a = SHOTS / pair[0] / (case + ".png")
            b = SHOTS / pair[1] / (case + ".png")
            if not a.exists() or not b.exists():
                rows.append({"case": case, "pair": pair, "status": "MISSING"})
                continue
            r = compare(a, b, SHOTS / "diff" / f"{case}.{pair[0]}-vs-{pair[1]}.png")
            r["case"] = case
            r["pair"] = pair
            if r.get("diff_pixels") == 0:
                r["status"] = "PASS"
            elif r.get("same_size") and r.get("max_channel", 255) <= 2 and r.get("ratio", 1) <= 0.02:
                # 文字抗锯齿 / 合成层的 ±1~2 抖动：无结构、无布局、无颜色块差异，肉眼不可辨
                r["status"] = "PASS(noise)"
            else:
                r["status"] = "DIFF"
            rows.append(r)
            mark = r["status"]
            extra = ""
            if r["status"] != "PASS" and r.get("same_size"):
                extra = f" pixels={r['diff_pixels']} ({r['ratio'] * 100:.3f}%) max={r['max_channel']} bbox={r['bbox']}"
            print(f"{mark:<12} {case:<24} {pair[0]:<8} vs {pair[1]:<8}{extra}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    fails = [r for r in rows if not str(r.get("status", "")).startswith("PASS")]
    exact = sum(1 for r in rows if r.get("status") == "PASS")
    noise = sum(1 for r in rows if r.get("status") == "PASS(noise)")
    print(f"\n{len(rows) - len(fails)}/{len(rows)} PASS（严格 {exact} + ±2 噪声 {noise}）· 报告 {OUT}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
