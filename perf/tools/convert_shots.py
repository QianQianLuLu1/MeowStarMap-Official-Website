#!/usr/bin/env python3
"""历史 PNG→WebP 工具：把 perf/assets/shots/*.png 压成 WebP。

当前源文件已是 WebP；本脚本仅用于历史 PNG 输入或对照。

默认只做 **无损**（lossless）编码：像素逐位不变，清晰度零损失。
可选附带 q95 档用于对照（有损，仅供体积/画质报告，不用于正式产物）。

用法：
    python perf/tools/convert_shots.py                 # 仅无损，8 进程
    python perf/tools/convert_shots.py --with-q95      # 额外生成 q95 对照

产物：
    perf/assets/webp/lossless/<name>.webp
    perf/assets/webp/q95/<name>.webp      （仅 --with-q95）
    perf/assets/webp-report.json
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SHOTS = ASSETS / "shots"
WEBP = ASSETS / "webp"
MANIFEST = ASSETS / "manifest.json"


def _encode_one(args):
    png_path, out_dir, level = args
    from PIL import Image

    with Image.open(png_path) as img:
        img.load()
        buf = io.BytesIO()
        if level == "lossless":
            # method=6 是 libwebp 的最高压缩档；exact 保留透明像素下的原始 RGB。
            img.save(buf, "WEBP", lossless=True, method=6, quality=100, exact=True)
        else:
            q = int(level.lstrip("q"))
            img.save(buf, "WEBP", quality=q, method=6)
        raw = buf.getvalue()
    name = Path(png_path).name[:-4] + ".webp"
    out = Path(out_dir) / name
    out.write_bytes(raw)
    return name, len(raw), len(buf.getvalue())


def _verify_roundtrip(args):
    """解码 WebP 与 PNG 逐像素比较，返回 (name, identical, diff_bbox_bytes)。"""
    png_path, webp_path = args
    from PIL import Image, ImageChops

    with Image.open(png_path) as a, Image.open(webp_path) as b:
        a.load()
        b.load()
        if a.mode != b.mode or a.size != b.size:
            return Path(png_path).name, False, f"mode/size {a.mode}{a.size} vs {b.mode}{b.size}"
        diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
        bbox = diff.getbbox()
        return Path(png_path).name, bbox is None, str(bbox)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-q95", action="store_true")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    shots = [SHOTS / rec["file"] for rec in manifest["shots"]]
    if not shots:
        print("没有截图，请先运行 extract_shots.py")
        return 1

    levels = ["lossless"] + (["q95"] if args.with_q95 else [])
    report = {"source": manifest["source"], "levels": {}}

    for level in levels:
        out_dir = WEBP / level
        out_dir.mkdir(parents=True, exist_ok=True)
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            sizes = list(ex.map(_encode_one, [(p, str(out_dir), level) for p in shots]))
        total = sum(s[1] for s in sizes)
        png_total = sum(p.stat().st_size for p in shots)
        report["levels"][level] = {
            "images": len(sizes),
            "webp_bytes": total,
            "png_bytes": png_total,
            "ratio_png_over_webp": round(png_total / total, 4),
            "per_image": [
                {"file": name, "webp_bytes": size}
                for name, size, _ in sorted(sizes)
            ],
        }
        print(f"{level:9s} {total:>12,} B  ({total / 1048576:.2f} MiB)  "
              f"PNG {png_total / total:.2f}x")

    # 无损档必须逐像素相同（有损档不参与此断言）
    lossless_dir = WEBP / "lossless"
    pairs = [(str(p), str(lossless_dir / (p.name[:-4] + ".webp"))) for p in shots]
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        checks = list(ex.map(_verify_roundtrip, pairs))
    bad = [c for c in checks if not c[1]]
    report["lossless_roundtrip"] = {
        "checked": len(checks),
        "identical": len(checks) - len(bad),
        "failed": [{"file": c[0], "detail": c[2]} for c in bad],
    }
    print(f"无损逐像素复核: {len(checks) - len(bad)}/{len(checks)} 完全一致")
    if bad:
        for b in bad[:5]:
            print("  FAIL", b)

    (ASSETS / "webp-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"产物: {WEBP}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
