#!/usr/bin/env python3
"""生成 Open Graph 分享图 site/assets/og-cover.jpg（1200×630）。

用站点自己的应用图标 + 中文字体合成，不引入外链/第三方素材。
用法：python perf/tools/make_og.py
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
HTML = REPO / "Meow Star Map 官网.html"
OUT = REPO / "site" / "assets" / "og-cover.jpg"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"


def main() -> int:
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r'--app-icon:url\("data:image/webp;base64,([^"]+)"\)', html)
    if not m:
        print("FAIL: 未找到内联应用图标")
        return 1
    icon = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGBA")
    icon = icon.resize((300, 300), Image.LANCZOS)

    bg = Image.new("RGB", (1200, 630), (245, 245, 247))
    d = ImageDraw.Draw(bg)

    # 柔和主色光斑（纯绘制，无外部素材）
    glow = Image.new("RGB", (1200, 630), (245, 245, 247))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((760, -220, 1420, 440), fill=(232, 238, 255))
    gd.ellipse((-260, 300, 360, 920), fill=(240, 234, 255))
    bg = Image.blend(bg, glow, 0.55)
    d = ImageDraw.Draw(bg)

    # 图标卡片
    d.rectangle((72, 147, 420, 495), fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    bg.paste(icon, (96, 171), icon)

    def font(path: str, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(path, size, index=0)

    d.text((462, 158), "喵星图", font=font(FONT_BOLD, 84), fill=(17, 24, 39))
    d.text((464, 268), "Meow Star Map", font=font(FONT_REG, 48), fill=(47, 111, 237))
    d.line((464, 348, 1040, 348), fill=(209, 213, 219), width=2)
    d.text((464, 372), "无限暖暖桌面相册工具", font=font(FONT_BOLD, 36), fill=(55, 65, 81))
    d.text((464, 428), "自动扫描 · 本地整理 · 编辑分享", font=font(FONT_REG, 28), fill=(107, 114, 128))
    d.text((464, 486), "Windows 10 / 11 · 数据只保存在本机", font=font(FONT_REG, 24), fill=(107, 114, 128))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    bg.save(OUT, "JPEG", quality=92, optimize=True)
    im = Image.open(OUT)
    print(f"OK {OUT} {OUT.stat().st_size:,} B {im.size[0]}x{im.size[1]}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
