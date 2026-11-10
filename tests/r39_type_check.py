#!/usr/bin/env python3
"""R39 苹果式排版整改专项探针（20261028）

用法：
    python tests/r39_type_check.py --skip-w3c
    python tests/r39_type_check.py
    python tests/r39_type_check.py --baseline-json tests/r39-baseline.json --report tests/r39-baseline.txt
    python tests/r39_type_check.py --compare-json tests/r39-baseline.json --report tests/r39-final-report.txt --shots

口径：file:// 协议；playwright + html5lib + 标准库；无新增依赖。
未跑项显式 NOT-RUN，不当作通过。
"""
from __future__ import annotations

import argparse
import html5lib
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "Meow Star Map 官网.html"
URL = SRC.resolve().as_uri()
SHOTS = ROOT / "tests" / "r39-shots"

ROUTES = [
    ("#/", "landing"),
    ("#/identity", "identity"),
    ("#/tutorial", "home"),
    ("#/dev", "dev"),
    ("#/dev/d-overview", "devcat"),
    ("#/dev/d-overview/doc001", "devdoc"),
    ("#/m3", "module"),
    ("#/m3/m3p1", "page"),
    ("#/all", "all"),
]
WIDTHS = [390, 768, 1024, 1440, 1920, 2560]
EXPECTED = {
    "landing": {"fs": 128.0, "fw": "700", "align": "center"},
    "identity": {"fs": 72.0, "fw": "700", "align": "center"},
    "home": {"fs": 76.0, "fw": "700", "align": "left"},
    "dev": {"fs": 60.0, "fw": "700", "align": "left"},
    "devcat": {"fs": 48.0, "fw": "600", "align": "left"},
    "devdoc": {"fs": 48.0, "fw": "600", "align": "left"},
    "module": {"fs": 48.0, "fw": "600", "align": "left"},
    "page": {"fs": 48.0, "fw": "600", "align": "left"},
    "all": None,
}


class Ledger:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expected, actual, note=""):
        self.rows.append({"name": name, "status": "PASS" if ok else "FAIL",
                          "expected": _fmt(expected), "actual": _fmt(actual), "note": note})
        return bool(ok)

    def skip(self, name, expected, note):
        self.rows.append({"name": name, "status": "NOT-RUN", "expected": _fmt(expected),
                          "actual": None, "note": note})

    def report(self, path=None):
        bad = [r for r in self.rows if r["status"] == "FAIL"]
        skip = [r for r in self.rows if r["status"] == "NOT-RUN"]
        lines = ["=" * 78, "R39 苹果式排版专项探针", "=" * 78]
        for r in self.rows:
            mark = "  ok  " if r["status"] == "PASS" else " FAIL " if r["status"] == "FAIL" else " skip "
            lines.append(mark + r["name"])
            if r["status"] == "FAIL":
                lines.append(f"        期望: {r['expected']}")
                lines.append(f"        实测: {r['actual']}")
                if r["note"]:
                    lines.append(f"        备注: {r['note']}")
            elif r["status"] == "NOT-RUN":
                lines.append(f"        原因: {r['note']}")
        lines.append("-" * 78)
        lines.append(f"合计 {len(self.rows)} | PASS {len(self.rows)-len(bad)-len(skip)} | FAIL {len(bad)} | NOT-RUN {len(skip)}")
        text = "\n".join(lines)
        print(text)
        if path:
            p = pathlib.Path(path)
            if not p.is_absolute():
                p = ROOT / p
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text + "\n", encoding="utf-8")
        return 0 if not bad else 1


def _fmt(value, limit=1600):
    if isinstance(value, (dict, list, tuple)):
        s = json.dumps(value, ensure_ascii=False, default=str)
    else:
        s = str(value)
    return s if len(s) <= limit else s[:limit] + " …"


def parse_color(value):
    if not value:
        return None
    s = value.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16),
                    int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)
        except ValueError:
            return None
    m = re.search(r"rgba?\(([^)]+)\)", s)
    if not m:
        return None
    parts = [p.strip() for p in re.split(r"[,/ ]+", m.group(1)) if p.strip()]
    if len(parts) < 3:
        return None
    try:
        alpha = float(parts[3]) if len(parts) > 3 else 1.0
        return (float(parts[0]), float(parts[1]), float(parts[2]), alpha)
    except ValueError:
        return None


def blend(fg, bg):
    if not fg:
        return None
    a = fg[3]
    if a >= 1:
        return fg
    return (fg[0] * a + bg[0] * (1 - a), fg[1] * a + bg[1] * (1 - a), fg[2] * a + bg[2] * (1 - a), 1.0)


def luminance(c):
    def ch(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(fg, bg):
    f = parse_color(fg)
    b = parse_color(bg)
    if not f or not b:
        return 0.0
    if f[3] < 1:
        f = blend(f, b)
    l1, l2 = luminance(f), luminance(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def source_checks(L, raw, args):
    # R43 起 data: 内联的图标 link（favicon / apple-touch-icon）属自包含资源，不计外链。
    link_count = len(re.findall(r"""<link\b(?![^>]*href=["']data:)""", raw, re.I))
    icon_link_count = len(re.findall(r"""<link\b[^>]*href=["']data:image/""", raw, re.I))
    script_src = len(re.findall(r"<script\b[^>]*\bsrc\s*=", raw, re.I))
    font_faces = len(re.findall(r"@font-face\s*\{", raw, re.I))
    form_count = len(re.findall(r"<form\b", raw, re.I))
    L.check("S0 资源不变量（零外链 / 2 内嵌字体 / 无表单）",
            link_count == 0 and icon_link_count == 2 and script_src == 0
            and font_faces == 2 and form_count == 0,
            "external-link=0 data-icon-link=2 script-src=0 font-face=2 form=0",
            f"external-link={link_count} data-icon-link={icon_link_count} "
            f"script-src={script_src} font-face={font_faces} form={form_count}")

    if args.skip_w3c:
        L.skip("S1 html5lib strict 解析", "0 错误", "--skip-w3c")
    else:
        parser = html5lib.HTMLParser(strict=True)
        try:
            parser.parse(raw)
            err = parser.errors
        except Exception as exc:  # noqa: BLE001 - strict parser may raise on first error
            err = [str(exc)]
        L.check("S1 html5lib strict 解析", not err, "0 错误", f"{len(err)} 个 | {err[:3]}")

    begin_count = raw.count("R39:BEGIN")
    if begin_count != 1 or "R39:END" not in raw:
        L.check("S2 R39 注释对唯一", False, "1 对", f"BEGIN={begin_count} END={'R39:END' in raw}")
        for name in ["S3 R39 仅排版度量", "S4 R39 screen 包裹", "S5 R39 :has 渐进门控",
                     "S6 R39 间距/行宽令牌", "S7 R39 图片左对齐声明"]:
            L.skip(name, "R39 存在后检查", "R39 注释对缺失")
        return None

    begin = raw.index("R39:BEGIN")
    end = raw.index("R39:END", begin) + len("R39:END")
    block = raw[begin:end]
    L.check("S2 R39 注释对唯一", True, "1 对", "ok")

    problems = []
    if "!important" in block:
        problems.append("!important")
    if re.search(r"@keyframes|(?<![\w-])animation\s*:|(?<![\w-])transition\s*:", block, re.I):
        problems.append("animation/transition")
    if re.search(r"(?<![\w-])color\s*:", block, re.I):
        problems.append("color 声明")
    if re.search(r"#[0-9a-fA-F]{3,8}\b", block):
        problems.append("hex 颜色")
    if re.search(r"https?://|url\(", block, re.I):
        problems.append("外部 url")
    L.check("S3 R39 仅排版度量（无颜色/动效/hex/外链/important）",
            not problems, "clean", problems or "clean")

    L.check("S4 R39 全部包在 @media screen", "@media screen" in block, "存在", "存在" if "@media screen" in block else "缺失")
    L.check("S5 R39 :has 受 @supports 门控",
            "@supports selector" in block and ":has(" in block, "存在", "ok" if "@supports selector" in block and ":has(" in block else "缺失")
    tokens = ["--type-h3", "--type-body", "--space-title-top", "--space-title-bottom",
              "--space-para", "--measure-prose"]
    missing = [t for t in tokens if t not in block]
    L.check("S6 R39 间距/行宽/字号令牌齐全", not missing, ",".join(tokens), missing or "all")
    L.check("S7 R39 图片左对齐声明",
            ".page-body img" in block and "margin-left:0" in block,
            ".page-body img + margin-left:0", "ok" if ".page-body img" in block and "margin-left:0" in block else "缺失")
    return block


METRICS_JS = r"""
() => {
  const cs = e => getComputedStyle(e);
  const rb = e => e.getBoundingClientRect();
  const n = v => { const x = parseFloat(v); return Number.isFinite(x) ? +x.toFixed(2) : 0; };
  const info = e => {
    if (!e) return null;
    const s = cs(e), r = rb(e);
    return {
      fs: n(s.fontSize), lh: n(s.lineHeight), fw: s.fontWeight, ls: n(s.letterSpacing),
      mt: n(s.marginTop), mb: n(s.marginBottom), pl: n(s.paddingLeft), pr: n(s.paddingRight),
      blw: n(s.borderLeftWidth),
      ta: s.textAlign, color: s.color, bg: s.backgroundColor, maxw: s.maxWidth,
      left: n(r.left), top: n(r.top), w: n(r.width), h: n(r.height)
    };
  };
  const pageBodies = [...document.querySelectorAll('.page-body')];
  const hasDirect = (el, tag) => [...el.children].some(c => c.tagName === tag);
  const page = document.body.dataset.view === 'all'
    ? (pageBodies.find(el => hasDirect(el, 'P') && hasDirect(el, 'H3')) ||
       pageBodies.find(el => hasDirect(el, 'P')) || pageBodies[0])
    : pageBodies[0];
  const direct = tag => page ? [...page.children].filter(el => el.tagName === tag) : [];
  const h3s = direct('H3').slice(0, 5).map(info);
  const firstTextP = page ? [...page.children].find(el => el.tagName === 'P' && !el.querySelector('img')) : null;
  const firstImgP = page ? [...page.children].find(el => el.tagName === 'P' && el.querySelector('img')) : null;
  const firstImg = page ? page.querySelector('img') : null;
  const h1 = document.querySelector('h1');
  const eyebrow = document.querySelector('.hero-badges span, .dev-badge, .lp-eyebrow, .crumbs');
  const sub = document.querySelector('.hero-sub, .dev-hero-sub, .gate-sub, .lp-sub');
  const lead = document.querySelector('.lead');
  const wrap = document.querySelector('.wrap, .allwrap');
  const app = document.querySelector('#app');
  const hero = document.querySelector('.hero, .dev-hero, .lp-hero');
  const panel = document.querySelector('.mod-overview');
  const faqH3 = document.querySelector('.faq-index h3');
  const h1Rect = h1 ? rb(h1) : null;
  const isTrans = s => !s || s === 'transparent' || /^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0\s*\)$/.test(s);
  const gradients = [...document.querySelectorAll('*')].filter(e => {
    const s = cs(e);
    const clip = s.webkitBackgroundClip === 'text' || s.backgroundClip === 'text';
    return clip && s.backgroundImage !== 'none' && (isTrans(s.webkitTextFillColor) || isTrans(s.color));
  }).length;
  return {
    view: document.body.dataset.view,
    h1: info(h1),
    h1Text: h1 ? (h1.textContent || '').trim().slice(0, 80) : '',
    h1Center: h1Rect ? +(h1Rect.left + h1Rect.width / 2).toFixed(2) : null,
    vw: window.innerWidth,
    eyebrow: info(eyebrow),
    sub: info(sub),
    lead: info(lead),
    p: info(firstTextP),
    imgP: info(firstImgP),
    img: info(firstImg),
    h3s: h3s,
    faqH3: info(faqH3),
    wrap: info(wrap),
    app: info(app),
    hero: info(hero),
    panel: info(panel),
    gate: info(document.querySelector('.gate h1')),
    about: info(document.querySelector('.about-sec')),
    body: { fs: n(cs(document.body).fontSize), lh: n(cs(document.body).lineHeight) },
    scrollW: document.documentElement.scrollWidth,
    clientW: document.documentElement.clientWidth,
    gradients: gradients
  };
}
"""

SNAPSHOT_JS = r"""
() => {
  const root = document.querySelector('.wrap, .allwrap, .gate, .lp-root') || document.body;
  const h1 = document.querySelector('h1');
  return {
    h1: h1 ? (h1.textContent || '').trim() : '',
    textLen: (root.innerText || '').replace(/\s+/g, ' ').trim().length,
    links: [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')),
    cards: {
      cover: document.querySelectorAll('.cover-grid > *').length,
      mod: document.querySelectorAll('.mod-grid > *').length,
      pagecards: document.querySelectorAll('.pagecards > *').length,
      quick: document.querySelectorAll('.quick-grid > *').length
    }
  };
}
"""


def resolve_path(value):
    if not value:
        return None
    p = pathlib.Path(value)
    return p if p.is_absolute() else ROOT / p


def set_theme(page, theme):
    page.evaluate("t => { if (t === 'dark') document.documentElement.setAttribute('data-theme', 'dark');"
                  " else document.documentElement.removeAttribute('data-theme'); }", theme)


def set_look(page, look):
    page.evaluate("v => document.documentElement.setAttribute('data-look', v)", look)


def nav(page, h, wait=240):
    page.evaluate("h => { if (location.hash !== h) location.hash = h; window.scrollTo(0, 0); }", h)
    page.wait_for_timeout(wait)


def run(args):
    L = Ledger()
    raw = SRC.read_text(encoding="utf-8")
    source_checks(L, raw, args)

    console_errors, page_errors, failed_requests, warnings = [], [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = ctx.new_page()
        page.on("console", lambda m: (console_errors if m.type == "error" else warnings).append(m.text)
                if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("requestfailed", lambda r: failed_requests.append(f"{r.url} {r.failure}"))
        page.goto(URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(450)
        set_theme(page, "light")
        set_look(page, "neutral")

        # 功能快照（改造前写入；改造后逐位比对）
        snapshot = {}
        for h, name in ROUTES:
            nav(page, h, 420 if name == "all" else 240)
            snapshot[name] = page.evaluate(SNAPSHOT_JS)
        baseline_path = resolve_path(args.baseline_json)
        compare_path = resolve_path(args.compare_json)
        if baseline_path:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
            L.check("F0 功能快照基线已写入", True, "写入", str(baseline_path))
        if compare_path:
            if not compare_path.exists():
                L.check("F1 功能快照逐位一致", False, "基线存在", f"缺失 {compare_path}")
            else:
                base = json.loads(compare_path.read_text(encoding="utf-8"))
                bad = [name for name, _ in ROUTES if snapshot.get(name) != base.get(name)]
                L.check("F1 功能快照逐位一致（文案/链接/卡片数）", not bad,
                        "9/9 一致", bad or "9/9 一致")

        # 1440 排版度量
        page.set_viewport_size({"width": 1440, "height": 900})
        set_theme(page, "light")
        set_look(page, "neutral")
        M = {}
        for h, name in ROUTES:
            nav(page, h, 300 if name == "all" else 220)
            M[name] = page.evaluate(METRICS_JS)

        # T1 字号/字重
        issues = []
        for name, exp in EXPECTED.items():
            if exp is None:
                continue
            h1 = M[name]["h1"]
            if not h1:
                issues.append(f"{name}: no h1")
                continue
            if abs(h1["fs"] - exp["fs"]) > 1.5:
                issues.append(f"{name}: fs {h1['fs']} != {exp['fs']}")
            if str(h1["fw"]) != exp["fw"]:
                issues.append(f"{name}: fw {h1['fw']} != {exp['fw']}")
        L.check("T1 1440 字号/字重阶梯", not issues,
                "page 48/600 · hero 76/700 · dev 60/700 · gate 72/700 · landing 128/700",
                issues or "all")

        # T2 标题间距 / 行高
        issues = []
        for name, exp in EXPECTED.items():
            if exp is None:
                continue
            h1 = M[name]["h1"]
            if not h1:
                issues.append(f"{name}: no h1")
                continue
            mt, mb, lh = h1["mt"] / h1["fs"], h1["mb"] / h1["fs"], h1["lh"] / h1["fs"]
            if not 0.47 <= mt <= 0.53:
                issues.append(f"{name}: mt/T={mt:.3f}")
            if not 0.72 <= mb <= 0.78:
                issues.append(f"{name}: mb/T={mb:.3f}")
            if not 1.14 <= lh <= 1.18:
                issues.append(f"{name}: lh/T={lh:.3f}")
        L.check("T2 标题 0.5T / 0.75T / 1.16 行高", not issues,
                "mt/T .5 · mb/T .75 · lh/T 1.16", issues or "all")

        # T3 眉题 / 副文
        issues = []
        for name in ["landing", "home", "dev", "module", "page", "devcat", "devdoc", "all"]:
            e = M[name]["eyebrow"]
            if not e:
                issues.append(f"{name}: no eyebrow")
                continue
            if not 13 <= e["fs"] <= 15:
                issues.append(f"{name}: eyebrow fs={e['fs']}")
            try:
                if int(float(e["fw"])) < 500:
                    issues.append(f"{name}: eyebrow fw={e['fw']}")
            except ValueError:
                issues.append(f"{name}: eyebrow fw={e['fw']}")
            if abs(e["ls"]) > 0.8:
                issues.append(f"{name}: eyebrow ls={e['ls']}px")
        for name in ["landing", "home", "dev", "identity"]:
            s = M[name]["sub"]
            if not s or str(s["fw"]) != "300":
                issues.append(f"{name}: sub fw={s and s['fw']}")
        L.check("T3 眉题 13–14px/500+/字距克制 · 副文 300", not issues,
                "eyebrow 13–14 / >=500 / |ls|<=0.8px; sub 300", issues or "all")

        # T4 正文节奏
        issues = []
        for name in ["module", "page", "devdoc", "all"]:
            p = M[name]["p"]
            if not p:
                issues.append(f"{name}: no p")
                continue
            if not 16.5 <= p["fs"] <= 17.5:
                issues.append(f"{name}: p fs={p['fs']}")
            if not 1.55 <= p["lh"] / p["fs"] <= 1.65:
                issues.append(f"{name}: p lh/fs={p['lh']/p['fs']:.3f}")
            if p["mb"] < p["lh"] * 1.05:
                issues.append(f"{name}: p mb={p['mb']} < 1.05*lh={p['lh']*1.05:.2f}")
            if p["mb"] + p["lh"] < p["lh"] * 1.8:
                issues.append(f"{name}: p pitch={p['mb']+p['lh']} < 1.8*lh")
            if not 630 <= p["w"] <= 701:
                issues.append(f"{name}: p w={p['w']}")
        L.check("T4 正文 17px / 1.6 / 段距>行距 / 40em", not issues,
                "fs 16.5–17.5 · lh/fs 1.55–1.65 · mb>=1.05lh · w 630–701", issues or "all")

        # T5 lead 左基线
        issues = []
        for name in ["page", "devdoc", "devcat"]:
            m = M[name]
            lead, h1 = m["lead"], m["h1"]
            if not lead or not h1:
                issues.append(f"{name}: no lead/h1")
                continue
            if lead["pl"] != 0 or lead["blw"] != 0:
                issues.append(f"{name}: lead pl={lead['pl']} blw={lead['blw']}")
            if abs(lead["left"] - h1["left"]) > 1:
                issues.append(f"{name}: lead.left={lead['left']} h1.left={h1['left']}")
            if not 17 <= lead["fs"] <= 19:
                issues.append(f"{name}: lead fs={lead['fs']}")
            if not 1.55 <= lead["lh"] / lead["fs"] <= 1.65:
                issues.append(f"{name}: lead lh/fs={lead['lh']/lead['fs']:.3f}")
        L.check("T5 lead 无左条/缩进，与 h1 同基线", not issues,
                "pl=0 blw=0 left=h1 · fs 17–19 · lh/fs 1.6", issues or "all")

        # T6 区块 h3 / FAQ
        issues = []
        for name in ["page", "devdoc", "all"]:
            hs = M[name]["h3s"]
            if not hs:
                issues.append(f"{name}: no h3")
                continue
            for i, h3 in enumerate(hs):
                if not 20 <= h3["fs"] <= 23:
                    issues.append(f"{name}.h3[{i}]: fs={h3['fs']}")
                if not 1.15 <= h3["lh"] / h3["fs"] <= 1.25:
                    issues.append(f"{name}.h3[{i}]: lh/fs={h3['lh']/h3['fs']:.3f}")
                if i == 0 and name in ("page", "all"):
                    if h3["mt"] > 1:
                        issues.append(f"{name}.h3[0]: mt={h3['mt']} not reset")
                elif h3["mt"] > 0 and not 2.0 <= h3["mt"] / h3["fs"] <= 2.5:
                    issues.append(f"{name}.h3[{i}]: mt/fs={h3['mt']/h3['fs']:.3f}")
        faq = M["all"]["faqH3"]
        if not faq:
            issues.append("all: no .faq-index h3")
        else:
            if not 20 <= faq["fs"] <= 23:
                issues.append(f"faq: fs={faq['fs']}")
            if not 0 <= faq["mb"] <= 6:
                issues.append(f"faq: mb={faq['mb']}")
        L.check("T6 区块 h3/FAQ 层级与首项复位", not issues,
                "h3 20–23 · first mt=0 · later mt≈2.25em · FAQ mb≈4", issues or "all")

        # T7 左对齐 / 面板
        issues = []
        for name in ["page", "devdoc", "devcat"]:
            m = M[name]
            lefts = []
            for key in ("h1", "crumbs", "lead", "p"):
                if m.get(key):
                    lefts.append(m[key]["left"])
            if len(lefts) < 2 or max(lefts) - min(lefts) > 1:
                issues.append(f"{name}: lefts={lefts}")
        mod = M["module"]
        if not mod["h1"] or not mod["panel"] or abs(mod["h1"]["left"] - mod["panel"]["left"]) > 1:
            issues.append("module: panel outer != h1")
        if not mod["p"] or not mod["img"] or abs(mod["p"]["left"] - mod["img"]["left"]) > 1:
            issues.append("module: p != img inside panel")
        al = M["all"]
        lefts = [x["left"] for x in (al["h3s"][0] if al["h3s"] else None, al["p"], al["img"]) if x]
        if len(lefts) < 2 or max(lefts) - min(lefts) > 1:
            issues.append(f"all: lefts={lefts}")
        L.check("T7 主阅读列同一左基线 / 面板外缘对齐", not issues,
                "page/devdoc/devcat 同线；module 面板外缘=h1、内文=图；all 同线", issues or "all")

        # T8 行宽 / 不缩图
        issues = []
        for name, lo, hi in [("page", 660, 700), ("module", 660, 700), ("all", 660, 700), ("devdoc", 630, 660)]:
            p = M[name]["p"]
            if not p:
                issues.append(f"{name}: no p")
            elif not lo <= p["w"] <= hi:
                issues.append(f"{name}: p.w={p['w']} not {lo}-{hi}")
        for name in ["module", "all"]:
            m = M[name]
            if not m["p"] or not m["imgP"] or not m["img"]:
                issues.append(f"{name}: missing p/img")
                continue
            if m["imgP"]["w"] < m["p"]["w"] + 40:
                issues.append(f"{name}: imgP.w={m['imgP']['w']} vs p.w={m['p']['w']}")
            if m["img"]["w"] < 620:
                issues.append(f"{name}: img.w={m['img']['w']}")
        L.check("T8 40em 行宽 + 含图段落不缩图 + 图宽达标", not issues,
                "p 660–700 · imgP >= p+40 · img >=620", issues or "all")

        # T9 居中模块唯一
        issues = []
        for name in ["landing", "identity"]:
            m = M[name]
            h1 = m["h1"]
            if not h1 or m["h1Center"] is None or abs(m["h1Center"] - m["vw"] / 2) > 3:
                issues.append(f"{name}: not centered ({m['h1Center']})")
        for name in ["home", "dev", "module", "page", "devcat", "devdoc"]:
            h1 = M[name]["h1"]
            if not h1 or h1["ta"] not in ("start", "left"):
                issues.append(f"{name}: ta={h1 and h1['ta']}")
        L.check("T9 仅 Landing/门页居中，其余左对齐", not issues,
                "landing/identity center; others start", issues or "all")

        # T10 390 移动端
        page.set_viewport_size({"width": 390, "height": 844})
        set_theme(page, "light")
        set_look(page, "neutral")
        MM = {}
        for h, name in [("#/m3/m3p1", "page"), ("#/tutorial", "home"), ("#/identity", "identity")]:
            nav(page, h, 240)
            MM[name] = page.evaluate(METRICS_JS)
        issues = []
        pg = MM["page"]
        app, wrap, lead = pg["app"], pg["wrap"], pg["lead"]
        if not app or app["pl"] != 16 or app["pr"] != 16:
            issues.append(f"page app padding={app and (app['pl'], app['pr'])}")
        if not wrap or wrap["pl"] != 16:
            issues.append(f"page wrap pl={wrap and wrap['pl']}")
        if not lead or lead["pl"] != 0:
            issues.append(f"page lead pl={lead and lead['pl']}")
        if not pg["h1"] or not pg["p"] or not pg["h3s"]:
            issues.append("page missing h1/p/h3")
        else:
            if abs(pg["h1"]["fs"] - 32) > 1:
                issues.append(f"page h1={pg['h1']['fs']}")
            if not (pg["h1"]["fs"] > pg["h3s"][0]["fs"] > pg["p"]["fs"]):
                issues.append("page hierarchy collapsed")
            if abs(pg["h1"]["left"] - pg["p"]["left"]) > 1:
                issues.append("page p not on h1 baseline")
            if not 1.55 <= pg["p"]["lh"] / pg["p"]["fs"] <= 1.65:
                issues.append("page body lh != 1.6")
        hm = MM["home"]
        if not hm["app"] or hm["app"]["pl"] != 16:
            issues.append(f"home app pl={hm['app'] and hm['app']['pl']}")
        if not hm["hero"] or hm["hero"]["pl"] != 18:
            issues.append(f"home hero pl={hm['hero'] and hm['hero']['pl']}")
        if not hm["h1"] or abs(hm["h1"]["fs"] - 36) > 1:
            issues.append(f"home h1={hm['h1'] and hm['h1']['fs']}")
        if not hm["sub"] or not hm["h1"] or not (hm["h1"]["fs"] > hm["sub"]["fs"]):
            issues.append("home hierarchy collapsed")
        if not MM["identity"]["gate"] or MM["identity"]["gate"]["top"] < 0:
            issues.append(f"identity gate top={MM['identity']['gate'] and MM['identity']['gate']['top']}")
        L.check("T10 390 移动端留白 / 层级 / 无顶部裁切", not issues,
                "app 16 · wrap 16 · hero 18 · h1 32/36 > h3 20 > p 16", issues or "all")

        # T11 渐变文字（不新增）
        page.set_viewport_size({"width": 1440, "height": 900})
        set_theme(page, "light")
        set_look(page, "neutral")
        nav(page, "#/", 240)
        g_neutral = page.evaluate(METRICS_JS)["gradients"]
        set_look(page, "plain")
        nav(page, "#/", 240)
        g_plain = page.evaluate(METRICS_JS)["gradients"]
        set_look(page, "color")
        nav(page, "#/", 240)
        g_color = page.evaluate(METRICS_JS)["gradients"]
        set_look(page, "neutral")
        issues = []
        if g_neutral != 1:
            issues.append(f"landing neutral gradients={g_neutral} (expect 1)")
        if g_plain != 0:
            issues.append(f"landing plain gradients={g_plain} (expect 0)")
        if g_color != 1:
            issues.append(f"landing color gradients={g_color} (expect 1)")
        for name, m in M.items():
            if name != "landing" and m["gradients"] > 1:
                issues.append(f"{name} gradients={m['gradients']}")
        L.check("T11 渐变文字每页 <=1（landing neutral/color=1, plain=0）", not issues,
                "neutral 1 · plain 0 · color 1 · others <=1", issues or "all")

        # T12 AA 对比度
        def tokens():
            return page.evaluate("""() => { const s = getComputedStyle(document.documentElement);
              const g = n => s.getPropertyValue(n).trim();
              return {tx:g('--tx'), card:g('--card'), mut:g('--mut'), slim1:g('--color-slim-1'),
                      slim3:g('--color-slim-3'), bg:g('--bg')}; }""")
        set_theme(page, "light")
        tl = tokens()
        set_theme(page, "dark")
        td = tokens()
        set_theme(page, "light")
        issues = []
        for label, fg, bg, need in [
            ("light tx/card", tl["tx"], tl["card"], 4.5),
            ("light mut/card", tl["mut"], tl["card"], 4.5),
            ("light slim1/card", tl["slim1"], tl["card"], 4.5),
            ("dark tx/card", td["tx"], td["card"], 4.5),
            ("dark mut/card", td["mut"], td["card"], 4.5),
            ("dark slim3/card", td["slim3"], td["card"], 4.5),
        ]:
            got = contrast(fg, bg)
            if got < need:
                issues.append(f"{label} {got:.2f} < {need}")
        ltx = parse_color(tl["tx"])
        if ltx and ltx[:3] == (0, 0, 0):
            issues.append("light body ink is pure black")
        L.check("T12 明暗 AA 对比度（正文/辅助/眉题）", not issues,
                ">=4.5:1 light/dark; light ink not #000", issues or "all")

        # T13 打印
        set_theme(page, "light")
        nav(page, "#/m3/m3p1", 240)
        page.emulate_media(media="print")
        page.wait_for_timeout(100)
        print_fs = page.evaluate("() => { const e=document.querySelector('h1'); return e ? parseFloat(getComputedStyle(e).fontSize) : 0; }")
        page.emulate_media(media="screen")
        L.check("T13 打印 h1=30px（R39 仅 screen）", abs(print_fs - 30) < 0.6, "30", print_fs)

        # T14 全断点溢出
        issues = []
        for w in WIDTHS:
            page.set_viewport_size({"width": w, "height": 900})
            for theme in ("light", "dark"):
                set_theme(page, theme)
                for h, name in ROUTES:
                    nav(page, h, 100 if name != "all" else 190)
                    sw, cw = page.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                    if sw > cw + 1:
                        issues.append(f"{w}/{theme}/{name}: {sw}>{cw}")
        L.check("T14 6 断点 × 双主题 × 9 路由零横向溢出", not issues,
                "scrollWidth<=clientWidth+1", issues[:8] or "all")
        page.set_viewport_size({"width": 1440, "height": 900})
        set_theme(page, "light")

        # T15 console
        L.check("T15 控制台 0 error / 0 pageerror / 0 失败请求",
                not console_errors and not page_errors and not failed_requests,
                "0/0/0", {"errors": console_errors[:5], "pageerrors": page_errors[:3], "failed": failed_requests[:3]})
        L.check("T16 控制台无警告", not warnings, "0", warnings[:5] or "0")

        # 截图
        if args.shots:
            SHOTS.mkdir(parents=True, exist_ok=True)
            set_look(page, "neutral")
            for w, hh in ((390, 844), (768, 900), (1440, 900), (1920, 1080)):
                page.set_viewport_size({"width": w, "height": hh})
                for theme in ("light", "dark"):
                    set_theme(page, theme)
                    for h, name in ROUTES:
                        nav(page, h, 260 if name != "all" else 520)
                        page.evaluate("window.scrollTo(0, 0)")
                        page.screenshot(path=str(SHOTS / f"{theme}-{w}-{name}.png"))
            set_theme(page, "light")

        ctx.close()
        browser.close()

    return L.report(args.report)


def main():
    ap = argparse.ArgumentParser(description="R39 苹果式排版专项探针")
    ap.add_argument("--skip-w3c", action="store_true", help="跳过 html5lib strict")
    ap.add_argument("--report", help="报告输出路径（相对项目根或绝对路径）")
    ap.add_argument("--baseline-json", help="写入功能快照基线 JSON")
    ap.add_argument("--compare-json", help="与功能快照基线 JSON 比对")
    ap.add_argument("--shots", action="store_true", help="截图到 tests/r39-shots")
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
