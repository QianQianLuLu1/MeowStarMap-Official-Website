#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R45 专项探针：landing 暗底舞台色彩作用域收口（R36 色点 + R38 外观 × R40–R44 新增板块）

用法：
    py tests/r45_theme_scope_check.py              全量（含断点矩阵与对比度矩阵）
    py tests/r45_theme_scope_check.py --skip-slow   跳过断点矩阵与逐路由对比度扫描

协议：file:// 直开，无端口自起。依赖 playwright + html5lib（与 r37/r38/r39/r41/r42/r43 同一口径，
不新增第三方依赖）。骨架抄 r42_migration_check.py，取色/对比度函数抄 r38_visual_check.py L97-107。

口径要点：
  * 暗底主题只有 lp-theme-energy(#0B0C10→#181A22) 与 lp-theme-deep(#024F97→#1D6EB6) 两个，
    且 body::before 是 position:fixed 的视口渐变 —— 故对比度必须「扫遍整条渐变取最劣端」，
    与当前滚动位置无关；只按元素当前屏幕位置取样会系统性高估。
  * 前景须按祖先链上不透明底色逐层合成到舞台之上；body/html 自身的背景在 body::before
    之下（伪元素是 body 的子盒子，画在 body 背景之上、正文之下），故不参与合成，否则
    会把暗底误判成浅底 —— 这是本探针最容易犯的错。
  * 主题态用 localStorage.nikki_lp_theme + reload 驱动，不手改 className（R36-UI 的
    applyTo 与 r38 V5 都会覆写同类）；data-theme / data-look / 视口用属性与 set_viewport_size
    驱动级联，不重载（r43 B5 纪律）。
  * slim / spectrum 与深色模式与 plain 三态须「零变化」：不比对截图，而比对冻结的 computed
    令牌值，可直接证伪 R45 泄漏。
"""
import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "Meow Star Map 官网.html"
URL = SRC.resolve().as_uri()

THEMES = ["slim", "spectrum", "energy", "deep"]
DARK_STAGE = ["energy", "deep"]
LANDING_ROUTES = ["#/", "#/features", "#/resonance", "#/privacy", "#/download", "#/download/start"]
WIDTHS = [390, 768, 900, 1440, 1920, 2560]
BAND = [769, 820, 860, 900]          # 触发器折叠档
AA_TEXT = 4.5

# 冻结基线：R45 之外的既有值，逐字取自源文件 L27（浅色 :root）与 L849（暗色）
TOKENS_LIGHT = {"--tx": "rgb(38, 42, 51)", "--mut": "rgb(107, 114, 128)",
                "--bd": "rgb(228, 232, 239)", "--card": "rgb(255, 255, 255)"}
TOKENS_DARK = {"--tx": "rgb(232, 236, 244)", "--mut": "rgb(154, 166, 189)",
               "--bd": "rgb(58, 58, 60)", "--card": "rgb(0, 0, 0)"}
# r20 / r25 / r29 精确色值断言占用，R45 不得触碰
LP_DL_BTN = {"background-color": "rgb(142, 203, 255)", "color": "rgb(11, 46, 79)"}

# 对比度扫描清单：(选择器, 人类标签, 所在路由)
AUDIT = [
    ("#/", ".lpx-title", "区块标题(R40)"), ("#/", ".lpx-kicker", "区块眉题(R40)"),
    ("#/", ".lpx-lead", "区块副文(R40)"), ("#/", ".lpx-num", "指标数字(R40)"),
    ("#/", ".lpx-card h3", "卡片标题(R40,继承)"), ("#/", ".lpx-more", "查看全部链接(R40)"),
    ("#/", ".lpx-stat", "统计卡面(R40)"),
    ("#/", ".lp-footnav h3", "页脚栏目头(R40)"), ("#/", ".lp-footnav a", "页脚链接(R40)"),
    ("#/", ".lp-footnote", "页脚注(R40)"),
    ("#/", "#lp-nav .lp-gh", "GitHub 圆钮(R42)"),
    ("#/", "#lp-nav .lp-themebtn", "主题钮(R7)"), ("#/", "#lp-nav .look-btn", "视觉风格钮(R38)"),
    ("#/features", ".pg-title", "二级页 H1(R40)"),
    ("#/features", ".pg-sec h2", "小节标题(R40,继承)"),
    ("#/features", ".pg-data strong", "数据大字(R40,继承)"),
    ("#/features", ".pg-link", "页内链接(R40)"), ("#/features", ".pg-back", "返回链(R40)"),
    ("#/features", ".pg-card h3", "卡标题(R40)"),
    ("#/download", ".pg-card .lp-dl-name", "网盘名(R44)"),
    ("#/download", ".pg-card .lp-dl-desc", "网盘说明(R44)"),
    ("#/download", ".pg-card .lp-dl-go", "网盘箭头(R44)"),
    ("#/download", ".pg-badge", "版本徽标(R40)"),
]

# R41 详情面板是惰性创建的，须先点开一张卡才有测量对象
DET_OPEN = ("#/", ".lpx-adv-grid>.lpx-card>.lpx-card-toggle", [
    (".lpx-det-in", "详情面板文字(R41)"), (".lpx-det-list li", "要点列表(R41)"),
    (".lpx-det-link", "了解更多(R41)"), (".lpx-det-close", "收起按钮(R41)"),
])

# 注入页内的取样器：合成祖先链 → 舞台最劣端 → WCAG 2.x 比值
SAMPLER = r"""
window.__R45 = (function () {
  function parse(s) { if (!s) return null; var m = /rgba?\(([^)]+)\)/.exec(s); if (!m) return null;
    var p = m[1].split(",").map(function (v) { return parseFloat(v); });
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; }
  function stage() { var bi = getComputedStyle(document.body, "::before").backgroundImage;
    var g = /linear-gradient\((.+)\)/.exec(bi), stops = [];
    if (g) { var re2 = /rgba?\([^)]+\)(?:\s+[\d.]+%)?/g, m;
      while ((m = re2.exec(g[1]))) stops.push(parse(m[0])); }
    if (stops.length >= 2) return stops;
    var flat = parse(bi) || parse(getComputedStyle(document.body).backgroundColor);
    return flat ? [flat] : null; }
  function gradAt(st, t) { if (st.length === 1) return st[0];
    var i = Math.min(st.length - 2, Math.max(0, Math.floor(t * (st.length - 1))));
    var a = st[i], b = st[i + 1], lo = i / (st.length - 1), hi = (i + 1) / (st.length - 1);
    var k = Math.max(0, Math.min(1, (t - lo) / (hi - lo)));
    return { r: a.r + (b.r - a.r) * k, g: a.g + (b.g - a.g) * k, b: a.b + (b.b - a.b) * k, a: 1 }; }
  function over(fg, bg) { if (fg.a >= 1) return fg;
    return { r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a),
             b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 }; }
  function surfaceOn(el, base) { var chain = [], n = el;
    while (n && n.nodeType === 1 && n !== document.body) {        // body/html 底色在舞台之下
      var c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0) chain.push(c);
      n = n.parentElement; }
    var acc = base; for (var i = chain.length - 1; i >= 0; i--) acc = over(chain[i], acc);
    return acc; }
  function lum(c) { function f(v) { v = v / 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); }
  function ratio(fg, bg) { var a = lum(over(fg, bg)), b = lum(bg);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); }
  function txt(el) { var fg = parse(getComputedStyle(el).color), st = stage(), w = 999, ws = null;
    for (var t = 0; t <= 1.0001; t += 0.05) {                    // 扫遍固定渐变取最劣端
      var bg = surfaceOn(el, st ? gradAt(st, t) : { r: 247, g: 247, b: 249, a: 1 });
      var c = ratio(fg, bg); if (c < w) { w = c; ws = bg; } }
    return { cr: w, fg: getComputedStyle(el).color,
             surf: "rgb(" + ["r", "g", "b"].map(function (k) { return Math.round(ws[k]); }).join(",") + ")" }; }
  return {
    text: function (sel) { var e = document.querySelector(sel); return e ? txt(e) : null; },
    nav: function () { var l = document.querySelector("#lp-nav .lp-links");
      return { delta: l ? l.scrollWidth - l.clientWidth : -1,
               doc: document.documentElement.scrollWidth - document.documentElement.clientWidth,
               brandH: Math.round((document.querySelector(".lp-brand") || { getBoundingClientRect: function () { return { height: 0 }; } }).getBoundingClientRect().height) }; },
    band: function () { var t = document.querySelector("#lp-nav .lp-thdots-toggle"), d = document.querySelector("#lp-nav .lp-thdots");
      var ids = [].map.call(d ? d.querySelectorAll(".lp-thdot") : [], function (x) { return x.getAttribute("data-lp-theme"); });
      return { hasTog: !!t, togShown: t ? getComputedStyle(t).display !== "none" : false,
               expanded: t ? t.getAttribute("aria-expanded") : null,
               hasPopup: t ? t.getAttribute("aria-haspopup") : null,
               label: t ? t.getAttribute("aria-label") : null,
               dotCount: ids.length, dup: ids.length !== new Set(ids).size,
               pressed: [].filter.call(d ? d.querySelectorAll(".lp-thdot") : [], function (x) { return x.getAttribute("aria-pressed") === "true"; }).length,
               open: d ? d.classList.contains("is-open") : false,
               dotBg: t ? getComputedStyle(t).backgroundColor : null }; }
  };
})();
"""


class Ledger:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expected, actual, note=""):
        self.rows.append({"name": name, "status": "PASS" if ok else "FAIL", "expected": expected,
                          "actual": str(actual)[:400], "note": note})
        return bool(ok)

    def skip(self, name, expected, why):
        self.rows.append({"name": name, "status": "NOT-RUN", "expected": expected,
                          "actual": None, "note": why})

    def report(self, title):
        p = f = s = 0
        print("\n" + "=" * 78 + "\n" + title + "\n" + "=" * 78)
        for r in self.rows:
            print(f"  {r['status']:4}  {r['name']}")
            if r["status"] == "FAIL":
                print(f"        期望: {r['expected']}\n        实际: {r['actual']}")
            elif r["status"] == "NOT-RUN":
                print(f"        跳过: {r['note']}")
            elif r["note"]:
                print(f"        {r['note']}")
            p += r["status"] == "PASS"; f += r["status"] == "FAIL"; s += r["status"] == "NOT-RUN"
        print("-" * 78 + f"\n合计 {len(self.rows)} | PASS {p} | FAIL {f} | NOT-RUN {s}")
        return f


# ── 源码级（纯 stdlib，不开浏览器）──────────────────────────────────────────
def source_checks(L, raw):
    lines = raw.split("\n")
    L.check("A1 R45 注释对成对", raw.count("R45:BEGIN") == 1 and raw.count("R45:END") >= 1
            and raw.count("R45-UI:BEGIN") == 1 and raw.count("R45-UI:END") == 1,
            "各恰 1 对", f"CSS {raw.count('R45:BEGIN')}/{raw.count('R45:END')}, "
            f"UI {raw.count('R45-UI:BEGIN')}/{raw.count('R45-UI:END')}")
    L.check("A2 HTML 注释内无连续双连字符",
            not [c for c in re.findall(r"<!--(.*?)-->", raw, re.S) if "--" in c], "0 条",
            sum(1 for c in re.findall(r"<!--(.*?)-->", raw, re.S) if "--" in c))
    ext_link = re.findall(r'<link\b(?![^>]*href=["\']data:)', raw)
    icon_link = re.findall(r'<link\b[^>]*href=["\']data:', raw)
    L.check("A3 外链 link 恒 0（data: 内联豁免）", len(ext_link) == 0, "0", len(ext_link))
    L.check("A4 图标 link 仍恰 2 枚且均 data:", len(icon_link) == 2, "2", len(icon_link))
    L.check("A5 零 script src / iframe / url(http) / 外链 img",
            raw.count("<script src") == 0 and raw.count("<iframe") == 0
            and raw.count("url(http") == 0
            and not re.findall(r'<img[^>]*src=["\']https?:', raw),
            "全 0", f"scriptsrc={raw.count('<script src')} iframe={raw.count('<iframe')} "
            f"urlhttp={raw.count('url(http')}")
    L.check("A6 @font-face 恒 2", raw.count("@font-face{") == 2, "2", raw.count("@font-face{"))
    sizes = {}
    for name, marker in (("tut", 'id="tut-data"'), ("dev", 'id="dev-data"')):
        hit = [l for l in lines if marker in l and len(l) > 100000]
        sizes[name] = len(hit[0]) if hit else -1
    L.check("A7 两条巨型数据行未被触碰", sizes == {"tut": 30924428, "dev": 1545974},
            "tut 30924428 / dev 1545974", f"tut {sizes['tut']} / dev {sizes['dev']}")
    js = re.findall(r"<script(?![^>]*type=)[^>]*>(.*?)</script>", raw, re.S)
    bad = []
    with tempfile.TemporaryDirectory() as td:
        for i, block in enumerate(js):
            f = pathlib.Path(td) / f"b{i}.js"
            f.write_text(block, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            if r.returncode:
                bad.append((i, r.stderr.strip().split("\n")[-1][:120]))
    L.check(f"A8 全部 {len(js)} 个 JS 块 node 编译通过（不执行）", not bad, "0 语法错", bad)
    # A9–A11：R45 层的令牌改写面。源码级断言，不依赖对 computed 字符串的猜测，
    #   故不可被「改探针迁就实测」反向污染。r20/r25/r29/r38 的精确色值断言全押在这些值上。
    m = re.search(r"/\* ═══════ R45:BEGIN.*?R45:END ═══════ \*/", raw, re.S)
    body = re.sub(r"/\*.*?\*/", "", m.group(0), flags=re.S) if m else None
    if body is None:
        L.check("A9 R45 层未重指派受保护令牌", False, "层体可定位", "未找到 R45 CSS 层体")
        return len(js)
    never = ["--lp-eyebrow-ink:", "--lp-sub-ink:", "--lp-foot-ink:", "--lp-title-grad:",
             "--lp-grad-fallback:", "--lp-wm-ink:", "--lp-ink-bright:", "--lp-font:",
             "--ac:", "--ac-deep:", "--ac-soft:"]
    hit = [t for t in never if t in body]
    L.check("A9 R45 层未重指派 landing 墨口与强调色族", not hit, f"{len(never)} 个令牌全部未出现", hit)
    # --card / --bg 只允许改写在与 .lp-root 隔离的两个浮层/导航作用域内（N1、M1）：
    #   它们的 subject 分别是 #lp-nav 与 #look-menu，够不着 .lp-dl-btn / .lp-dl-menu / .lpx-card
    #   等被 r20/r29 断言的消费点。:has(.lp-root…) 是关系选择器，不是祖先作用域，须先剥掉再判。
    isolated = {"#lp-nav", "#look-menu"}
    scope_bad = []
    for tok in ("--card:", "--bg:"):
        for rule in re.findall(r"([^{}]*)\{[^{}]*" + tok + r"[^{}]*\}", body, re.S):
            for sel in re.sub(r":has\([^()]*(?:\([^()]*\)[^()]*)*\)", "", rule).split(","):
                s = sel.strip()
                if not s.endswith(tuple(isolated)) or ".lp-root" in s or s.startswith(":root"):
                    scope_bad.append(f"{tok} → {s[-60:]}")
    L.check("A10 --card/--bg 改写仅限 #lp-nav 与 #look-menu 隔离作用域", not scope_bad,
            "每条选择器的 subject 均为 #lp-nav 或 #look-menu，且不含 .lp-root", scope_bad)
    allowed = sorted(set(re.findall(r"--([a-z0-9-]+)\s*:", body)))
    L.check("A11 R45 层改写面恰为 tx/mut/bd/card/bg + 新墨口 lp-ac-ink",
            allowed == ["bd", "bg", "card", "lp-ac-ink", "mut", "tx"],
            "['bd','bg','card','lp-ac-ink','mut','tx']", allowed)
    return len(js)


def w3c(L, raw):
    import html5lib
    try:
        html5lib.HTMLParser(strict=True).parse(raw)
        L.check("G1 html5lib strict 原件 0 错误", True, "0 错误", "无异常抛出")
    except Exception as e:
        L.check("G1 html5lib strict 原件 0 错误", False, "0 错误", repr(e)[:300])


# ── 浏览器侧 ────────────────────────────────────────────────────────────────
def prepare(p, theme):
    p.goto(URL); p.wait_for_load_state("networkidle")
    p.evaluate("(t)=>{localStorage.setItem('nikki_lp_theme',t);"
               "localStorage.setItem('nikki_theme','light');"
               "localStorage.setItem('nikki_look','neutral');}", theme)
    p.reload(); p.wait_for_load_state("networkidle")
    p.add_script_tag(content=SAMPLER)
    p.evaluate("v=>location.hash=v", "#/"); p.wait_for_timeout(250)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-slow", action="store_true", help="跳过断点矩阵与逐路由对比度扫描")
    args = ap.parse_args()
    L = Ledger()
    raw = SRC.read_text(encoding="utf-8")
    njs = source_checks(L, raw)
    w3c(L, raw)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={"width": 1440, "height": 1000})
        console_err, reqfail = [], []
        p.on("console", lambda m: console_err.append(m.text) if m.type in ("error", "warning") else None)
        p.on("pageerror", lambda e: console_err.append(str(e)))
        p.on("requestfailed", lambda r: reqfail.append(r.url))

        for theme in THEMES:
            prepare(p, theme)
            tag = f"{theme}/light/neutral"

            # B 组：R45 泄漏 / 惰性
            stage = theme in DARK_STAGE
            # B1：slim / spectrum 不得被 R45 波及。比「实际着色的 computed rgb」而非
            #     getPropertyValue('--tx')（自定义属性按 spec 原样返回 "#262a33"，不是 rgb）
            used = p.evaluate("()=>({root:getComputedStyle(document.querySelector('.lp-root')).color,"
                              "kick:(document.querySelector('.lpx-kicker')"
                              "&&getComputedStyle(document.querySelector('.lpx-kicker')).color)})")
            if not stage:
                L.check(f"B1 {tag} 令牌未泄漏",
                        used["root"] == TOKENS_LIGHT["--tx"]
                        and used["kick"] == TOKENS_LIGHT["--mut"],
                        f"root={TOKENS_LIGHT['--tx']} kick={TOKENS_LIGHT['--mut']}", used)
            else:
                L.check(f"B1 {tag} 舞台墨色已翻转",
                        used["root"] in ("rgb(232, 236, 244)", "rgb(255, 255, 255)"),
                        "--lp-ink-bright 或 --color-neutral-1", used)
            card = p.evaluate("s=>{const e=document.querySelector(s);"
                              "return e?getComputedStyle(e).backgroundColor:null}", ".lpx-card")
            if stage:
                L.check(f"B2 {tag} 卡面转暗玻璃", card == "rgba(22, 28, 42, 0.62)",
                        "rgba(22, 28, 42, 0.62)", card)
            else:
                L.check(f"B2 {tag} 卡面未被动", card == "rgb(255, 255, 255)",
                        "rgb(255, 255, 255)", card)

            # C 组：r20 / r25 / r29 精确色值占用
            btn = p.evaluate("s=>{const e=document.querySelector(s);const c=getComputedStyle(e);"
                             "return {'background-color':c.backgroundColor,color:c.color};}", ".lp-dl-btn")
            L.check(f"C1 {tag} .lp-dl-btn 色值未动", btn == LP_DL_BTN, LP_DL_BTN, btn)

            # D 组：暗色模式与 plain 态惰性（属性驱动，不重载）
            p.evaluate("()=>document.documentElement.setAttribute('data-theme','dark')")
            p.wait_for_timeout(150)
            cardD = p.evaluate("s=>{const e=document.querySelector(s);"
                               "return e?getComputedStyle(e).backgroundColor:null}", ".lpx-card")
            want = TOKENS_DARK["--card"]
            L.check(f"D1 {theme}/dark R45 保持惰性", cardD == want, want, cardD)
            p.evaluate("()=>document.documentElement.setAttribute('data-theme','light')")
            p.evaluate("()=>window.__r38&&window.__r38.set('plain')")
            p.wait_for_timeout(150)
            cardP = p.evaluate("s=>{const e=document.querySelector(s);"
                               "return e?getComputedStyle(e).backgroundColor:null}", ".lpx-card")
            L.check(f"D2 {theme}/plain 未被 R45 覆写", cardP == "rgb(255, 255, 255)",
                    "rgb(255, 255, 255)", cardP)
            dotsDisp = p.evaluate("()=>{const d=document.querySelector('#lp-nav .lp-thdots');"
                                  "return d?getComputedStyle(d).display:null}")
            L.check(f"D3 {theme}/plain 色点仍隐藏（R38 L1972 未被推翻）", dotsDisp == "none", "none", dotsDisp)
            p.evaluate("()=>window.__r38&&window.__r38.set('neutral')")
            p.wait_for_timeout(150)

            # E 组：对比度矩阵（暗底主题须达 AA）+ R41 惰性面板 + 卡面一致性
            if stage and not args.skip_slow:
                worst, missed = [], []
                for route, sel, label in AUDIT:
                    p.evaluate("v=>location.hash=v", route); p.wait_for_timeout(240)
                    r = p.evaluate("s=>window.__R45.text(s)", sel)
                    if r is None:
                        missed.append(label); continue
                    if r["cr"] < AA_TEXT:
                        worst.append(f"{label}={r['cr']:.2f} fg={r['fg']} 面={r['surf']}")
                route, trigger, det = DET_OPEN
                p.evaluate("v=>location.hash=v", route); p.wait_for_timeout(240)
                p.evaluate("t=>{const e=document.querySelector(t);if(e)e.click();}", trigger)
                p.wait_for_timeout(600)
                for sel, label in det:
                    r = p.evaluate("s=>window.__R45.text(s)", sel)
                    if r is None:
                        missed.append(label); continue
                    if r["cr"] < AA_TEXT:
                        worst.append(f"{label}={r['cr']:.2f} fg={r['fg']} 面={r['surf']}")
                L.check(f"E1 {tag} 暗底舞台全量达 AA", not worst, f"全部 ≥{AA_TEXT}", worst)
                L.check(f"E2 {tag} 审计清单无选择器落空", not missed, "全部命中", missed)
                bg = p.evaluate("()=>{const q=s=>{const e=document.querySelector(s);"
                                "return e?getComputedStyle(e).backgroundColor:null};"
                                "return {about:q('.about-sec'),stat:q('.lpx-stat'),"
                                "card:q('.lpx-card'),det:q('.lpx-det-in')};}")
                p.evaluate("t=>{const e=document.querySelector(t);if(e)e.click();}", trigger)
                p.wait_for_timeout(200)
                p.evaluate("v=>location.hash=v", "#/features"); p.wait_for_timeout(260)
                pg = p.evaluate("()=>{const q=s=>{const e=document.querySelector(s);"
                                "return e?getComputedStyle(e).backgroundColor:null};"
                                "return {card:q('.pg-card'),next:q('.pg-next')};}")
                vals = [bg["about"], bg["stat"], bg["card"], bg["det"], pg["card"], pg["next"]]
                L.check(f"E3 {tag} 新板块卡面与既有 .about-sec 同值",
                        all(v == "rgba(22, 28, 42, 0.62)" for v in vals),
                        "全部 rgba(22, 28, 42, 0.62)", dict(bg, **pg))

        # F 组：窄屏折叠触发器
        for w, expect in [(1440, False), (900, True), (820, True), (769, True), (768, False), (390, False)]:
            p.set_viewport_size({"width": w, "height": 900}); p.wait_for_timeout(160)
            st = p.evaluate("()=>window.__R45.band()")
            L.check(f"F1 触发器可见性 @{w}px", st["togShown"] is expect and st["hasTog"],
                    f"shown={expect}", f"shown={st['togShown']} hasTog={st['hasTog']}")
            if expect:
                L.check(f"F2 @{w}px 色点仍为同批 4 枚且无重复 data-lp-theme",
                        st["dotCount"] == 4 and not st["dup"] and st["pressed"] == 1,
                        "count=4 dup=False pressed=1",
                        f"count={st['dotCount']} dup={st['dup']} pressed={st['pressed']}")
                p.evaluate("()=>document.querySelector('#lp-nav .lp-thdots-toggle').click()")
                p.wait_for_timeout(120)
                o = p.evaluate("()=>window.__R45.band()")
                L.check(f"F3 @{w}px 点击开合 + aria-expanded 同步", o["open"] and o["expanded"] == "true",
                        "open=True expanded=true", f"open={o['open']} expanded={o['expanded']}")
                # F8：浮层「不被 .lp-links 的 overflow-x:auto 裁切」是本轮最容易因后续改动而
                #     静默退化的性质（它依赖 #lp-nav 仍是 abspos 包含块），只能靠几何断言守住
                geo = p.evaluate("""()=>{const d=document.querySelector('#lp-nav .lp-thdots');
                  const nav=document.getElementById('lp-nav').getBoundingClientRect();
                  const r=d.getBoundingClientRect();
                  const dots=[].map.call(d.querySelectorAll('.lp-thdot'),x=>x.getBoundingClientRect());
                  return {panel:[r.x,r.y,r.width,r.height].map(Math.round), navBottom:Math.round(nav.bottom),
                          vw:innerWidth,
                          clipped:d.scrollWidth>d.clientWidth+1||d.scrollHeight>d.clientHeight+1,
                          allVisible:dots.every(b=>b.width>0&&b.height>0&&b.right<=innerWidth&&b.left>=0),
                          belowNav:r.top>=nav.bottom-1, n:dots.length};}""")
                L.check(f"F8 @{w}px 浮层未被裁且四枚色点完整可见于导航下方",
                        (not geo["clipped"]) and geo["allVisible"] and geo["belowNav"]
                        and geo["n"] == 4 and geo["panel"][0] >= 0
                        and geo["panel"][0] + geo["panel"][2] <= geo["vw"],
                        "未裁切 + 4 枚均可见 + 在导航下沿之下 + 不出视口", geo)
                p.evaluate("()=>document.querySelector('#lp-nav .lp-thdot[data-lp-theme=\"deep\"]').click()")
                p.wait_for_timeout(200)
                c = p.evaluate("()=>window.__R45.band()")
                ls = p.evaluate("()=>localStorage.getItem('nikki_lp_theme')")
                L.check(f"F4 @{w}px 浮层内选色即关闭并持久化",
                        not c["open"] and c["expanded"] == "false" and ls == "deep",
                        "closed + expanded=false + storage=deep",
                        f"open={c['open']} expanded={c['expanded']} storage={ls}")
                p.evaluate("()=>document.querySelector('#lp-nav .lp-thdots-toggle').click()")
                p.wait_for_timeout(120)
                p.keyboard.press("Escape"); p.wait_for_timeout(120)
                e = p.evaluate("()=>window.__R45.band()")
                af = p.evaluate("()=>document.activeElement===document.querySelector('.lp-thdots-toggle')")
                L.check(f"F5 @{w}px Escape 关闭且焦点归还", not e["open"] and af,
                        "closed + focus 归还", f"open={e['open']} focus={af}")
                # E3 把页面留在了 #/features；若目标 hash 与当前相同则不触发 hashchange，
                # 须先离开该路由再重进，才能真的测到「路由变更关闭」
                p.evaluate("()=>{if(location.hash==='#/features')location.hash='#/';}")
                p.wait_for_timeout(220)
                p.evaluate("()=>document.querySelector('#lp-nav .lp-thdots-toggle').click()")
                p.wait_for_timeout(120)
                p.evaluate("v=>location.hash=v", "#/features"); p.wait_for_timeout(220)
                h = p.evaluate("()=>window.__R45.band()")
                L.check(f"F6 @{w}px hashchange 关闭", not h["open"], "closed", f"open={h['open']}")
                p.evaluate("v=>location.hash=v", "#/"); p.wait_for_timeout(200)
                p.evaluate("()=>window.__r38&&window.__r38.set('plain')"); p.wait_for_timeout(150)
                pl = p.evaluate("()=>{const t=document.querySelector('.lp-thdots-toggle');"
                                "return t?getComputedStyle(t).display:null}")
                L.check(f"F7 @{w}px plain 下不显示配色入口", pl in (None, "none"),
                        "none", pl)
                p.evaluate("()=>window.__r38&&window.__r38.set('neutral')"); p.wait_for_timeout(150)

        # G 组：溢出矩阵
        if not args.skip_slow:
            over_bad = []
            p.evaluate("k=>localStorage.setItem('nikki_lp_theme',k)", "slim")
            p.reload(); p.wait_for_load_state("networkidle")
            p.add_script_tag(content=SAMPLER)
            for w in WIDTHS + BAND:
                p.set_viewport_size({"width": w, "height": 900}); p.wait_for_timeout(150)
                n = p.evaluate("()=>window.__R45.nav()")
                budget = 58 if w in BAND else 0
                if n["doc"] > 0 and w >= 768:
                    over_bad.append(f"doc@{w}={n['doc']}")
                if n["brandH"] > 52:
                    over_bad.append(f"brandH@{w}={n['brandH']}")
                if w in BAND and n["delta"] > budget:
                    over_bad.append(f"lp-links@{w}={n['delta']}>{budget}")
            L.check("G1 视口矩阵零文档溢出 + 触发器档 ≤58px + 品牌 ≤52px", not over_bad,
                    "doc=0(≥768) delta≤58(769–900) brandH≤52", over_bad)

        # H 组：运行时洁净
        L.check("H1 console 零 error/warning", not console_err, "0", console_err[:6])
        L.check("H2 requestfailed 恒 0", not reqfail, "0", reqfail[:6])
        b.close()

    print(f"\n（JS 块共 {njs} 个）")
    sys.exit(L.report("R45 landing 暗底舞台色彩作用域收口"))


if __name__ == "__main__":
    main()
