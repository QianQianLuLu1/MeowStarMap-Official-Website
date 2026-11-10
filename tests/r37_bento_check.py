#!/usr/bin/env python3
"""R37 Bento Grid 专项探针（Apple 风格便当布局 + 非黑即白配色 + 短边比例圆角 · 20261026）

用法：
    python tests/r37_bento_check.py --baseline     # 改造前落基线：R37 视觉项预期 FAIL（证明用例可复现）
    python tests/r37_bento_check.py                # 改造后全量校验，并与基线逐项比对功能一致性
    python tests/r37_bento_check.py --skip-w3c     # 跳过 html5lib strict 解析（单次约 74s）

口径说明：
  * file:// 协议（同 r24 无端口先例）：源文件 34MB，走 HTTP 反复导航会重复搬运巨量数据；R37 不需要 fetch/CORS。
  * 零新增依赖：仅 playwright + html5lib（requirements.txt 既有）+ 标准库。
  * 圆角工程式 r = clamp(16, 0.07 x min(w,h), 34)。字面 18% 系数在实测卡尺寸区间（短边 213~748px）
    会给出 15~135px、Hero 近胶囊，故按已确认的工程修正取 7% + 34px 上限；见 AGENTS.md R37 已知限制。
  * 本机 prefers-reduced-transparency 恒激活（EnableTransparency=0），玻璃分支必须双态覆盖。
  * 未跑项以 NOT-RUN 显式记账，不当作通过。
"""
import io
import json
import pathlib
import re
import subprocess
import sys

from playwright.sync_api import sync_playwright

try:  # Windows 控制台默认 GBK，中文报告需强制 UTF-8（与既有探针同口径）
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "Meow Star Map 官网.html"
URL = SRC.resolve().as_uri()
HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE / "r37-baseline.json"

GEOM_VIEWPORTS = [390, 768, 1440, 1920, 2560]
HASHES = ["#/", "#/identity", "#/tutorial", "#/dev", "#/m1", "#/m1/m1p1", "#/all"]

R_MIN, R_K, R_MAX = 16.0, 0.07, 34.0
LIGHT_PAGE, DARK_PAGE = "rgb(245, 245, 247)", "rgb(29, 29, 31)"
LIGHT_CARD, DARK_CARD = "rgb(255, 255, 255)", "rgb(0, 0, 0)"
FALLBACK_R = 26.0  # CSS var(--r-bento, var(--r37-r)) 的兜底值

# --------------------------------------------------------------------------- JS

JS_GEOM = """() => {
  const n = s => parseFloat(s) || 0;
  const out = {grids: [], cards: [], scopeLeak: [], baselineRadii: {},
               scrollWidth: 0, clientWidth: 0, textGradient: 0};
  for (const sel of ['.cover-grid', '.mod-grid', '.skel-grid', '.quick-grid', '.pagecards']) {
    const g = document.querySelector(sel);
    if (!g) continue;
    const cs = getComputedStyle(g);
    out.grids.push({sel, cols: cs.gridTemplateColumns.split(' ').length, tracks: cs.gridTemplateColumns,
                    trackNums: cs.gridTemplateColumns.split(' ').map(parseFloat),
                    columnGap: cs.columnGap, rowGap: cs.rowGap});
  }
  for (const c of document.querySelectorAll('.cover-grid>*, .mod-grid>*')) {
    const r = c.getBoundingClientRect(), cs = getComputedStyle(c);
    out.cards.push({
      first: c === c.parentElement.firstElementChild,
      w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
      short: Math.round(Math.min(r.width, r.height) * 100) / 100,
      radius: n(cs.borderTopLeftRadius), radiusTR: n(cs.borderTopRightRadius),
      radiusBR: n(cs.borderBottomRightRadius),
      bg: cs.backgroundColor, shadow: cs.boxShadow, bgImage: cs.backgroundImage,
      colStart: cs.gridColumnStart, rowStart: cs.gridRowStart,
      colEnd: cs.gridColumnEnd, rowEnd: cs.gridRowEnd,
      inlineVar: (c.style.getPropertyValue('--r-bento') || '').trim() || null,
      left: Math.round(r.left * 100) / 100, right: Math.round(r.right * 100) / 100,
      top: Math.round(r.top * 100) / 100, bottom: Math.round(r.bottom * 100) / 100,
      // 封面填充度：封面盒高 - 内部 img 实绘高（>2px 即露出 #eceff4 灰底）
      coverGapPx: (() => {
        const cv = c.querySelector('.ms-cover'); if (!cv) return null;
        const im = cv.querySelector('img'); if (!im) return null;
        if (!(im.complete && im.naturalWidth > 0)) return -1;
        return Math.round((cv.getBoundingClientRect().height - im.getBoundingClientRect().height) * 100) / 100;
      })()
    });
  }
  for (const e of document.querySelectorAll('*')) {
    if (e.style && e.style.getPropertyValue('--r-bento') && !e.closest('.cover-grid, .mod-grid'))
      out.scopeLeak.push(e.className || e.tagName);
  }
  for (const sel of ['.gate-role', '.pagecard', '.quick', '.step', '.ms-card'])
    if (document.querySelector(sel)) out.baselineRadii[sel] = n(getComputedStyle(document.querySelector(sel)).borderTopLeftRadius);
  const hero = document.querySelector('.cover-grid>:first-child, .mod-grid>:first-child');
  if (hero) {
    out.ringRadius = n(getComputedStyle(hero, '::before').borderTopLeftRadius);
    const g = hero.parentElement, cs = getComputedStyle(g);
    out.trackWidths = cs.gridTemplateColumns.split(' ').map(parseFloat);
    out.trackGap = parseFloat(cs.columnGap);
  }
  const w = document.querySelector('.wrap-home, .wrap-dev');
  out.wrapBg = w ? getComputedStyle(w).backgroundColor : null;
  out.secTipMargin = (() => { const s = document.querySelector('.sec-tip'); return s ? getComputedStyle(s).marginBottom : null; })();
  out.htmlBg = getComputedStyle(document.documentElement).backgroundColor;
  const isTrans = s => !s || s === 'transparent' || /^rgba\\(\\s*\\d+\\s*,\\s*\\d+\\s*,\\s*\\d+\\s*,\\s*0\\s*\\)$/.test(s);
  out.textGradient = [...document.querySelectorAll('*')].filter(e => {
    const cs = getComputedStyle(e);
    const clip = cs.webkitBackgroundClip === 'text' || cs.backgroundClip === 'text';
    // 真正「呈渐变文字」需三条件同时成立：clip:text + 有背景图 + 文字填充透明
    // 注意 Chrome 把 -webkit-text-fill-color:transparent 计算成 rgba(0,0,0,0)，不是字面 transparent
    return clip && cs.backgroundImage !== 'none' && (isTrans(cs.webkitTextFillColor) || isTrans(cs.color));
  }).length;
  out.scrollWidth = document.documentElement.scrollWidth;
  out.clientWidth = document.documentElement.clientWidth;
  out.view = document.body.dataset.view;
  return out;
}"""

JS_FUNC = """() => {
  const q = s => document.querySelector(s);
  const all = s => [...document.querySelectorAll(s)];
  return {
    view: document.body.dataset.view,
    ms: all('.ms-card').length, mod: all('.mod-card').length,
    gate: all('.gate-role').length, pagecard: all('.pagecard').length,
    quick: all('.quick').length, step: all('.step').length,
    sidebarLinks: all('#sidebar a').length, crumbs: all('.crumbs a').length,
    pager: all('.pager a').length, rel: all('.rel a, .mod-rel a').length,
    dlItems: all('.lp-dl-item').map(a => a.getAttribute('href')),
    dlBtnText: q('.lp-dl-btn') ? q('.lp-dl-btn').textContent.trim().replace(/\\s+/g,' ') : null,
    cta: q('.lp-cta') ? q('.lp-cta').getAttribute('href') : null,
    heroTitle: q('.lp-title') ? q('.lp-title').textContent.trim() : null,
    aboutBtns: all('.about-soc-btn').length, aboutSec: !!q('.about-sec'),
    docTitle: document.title, empty: !!q('.empty-ill'),
    statNums: all('.stat b').map(b => b.textContent.trim()),
    modNames: all('.ms-name, .mc-name').map(e => e.textContent.trim()),
    imgSrcPrefix: all('.ms-cover img').map(i => i.getAttribute('src').slice(0, 11)),
    imgAlts: all('.ms-cover img').map(i => i.getAttribute('alt')),
    bodyTextLen: document.body.innerText.replace(/\\s+/g,'').length
  };
}"""


class Ledger:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expected, actual, note=""):
        self.rows.append({"name": name, "status": "PASS" if ok else "FAIL",
                          "expected": expected, "actual": str(actual)[:400], "note": note})
        return bool(ok)

    def skip(self, name, expected, note):
        self.rows.append({"name": name, "status": "NOT-RUN", "expected": expected,
                          "actual": None, "note": note})

    def report(self, title):
        bad = [r for r in self.rows if r["status"] == "FAIL"]
        skip = [r for r in self.rows if r["status"] == "NOT-RUN"]
        print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)
        for r in self.rows:
            print(f"{'  ok  ' if r['status']=='PASS' else ' FAIL ' if r['status']=='FAIL' else ' skip '}{r['name']}")
            if r["status"] == "FAIL":
                print(f"        期望: {r['expected']}\n        实测: {r['actual']}")
                if r["note"]:
                    print(f"        备注: {r['note']}")
            if r["status"] == "NOT-RUN":
                print(f"        原因: {r['note']}")
        print("-" * 78)
        print(f"合计 {len(self.rows)} | PASS {len(self.rows)-len(bad)-len(skip)} | FAIL {len(bad)} | NOT-RUN {len(skip)}")
        return 1 if bad else 0


def radius_target(short):
    return min(max(R_K * short, R_MIN), R_MAX)


def static_checks(L):
    raw = SRC.read_text(encoding="utf-8", errors="replace")
    lines = raw.split("\n")
    # 两段口径（历轮 r31_links_check 的同款陷阱）：
    #   * 标记级计数用全文（真实 <link>/<script src> 只可能是标记）
    #   * 文本级计数（@import / url(http / src="http）必须先剥离 >100000 字符的巨型数据行，
    #     否则 dev-data 文档正文里的 CSS 讲解文字（实测 4 处 "@import"）会造成假阳性。
    stripped = "\n".join(l for l in lines if len(l) <= 100000)
    cr = lambda p: len(re.findall(p, raw))
    cs = lambda p: len(re.findall(p, stripped))

    pairs = (cr(r"R37:BEGIN"), cr(r"R37:END"), cr(r"R37-UI:BEGIN"), cr(r"R37-UI:END"))
    L.check("S3 R37 回滚注释对成对平衡", pairs == (1, 1, 1, 1),
            "(BEGIN,END,UI-BEGIN,UI-END) == (1,1,1,1)", pairs)

    offenders = [m[4:-3].replace("\n", " ")[:70] for m in re.findall(r"<!--.*?-->", raw, re.S)
                 if "--" in m[4:-3]]
    L.check("S4 HTML 注释内无连续双连字符（W3C 合规；本项目历史上踩过两次）", not offenders,
            "0 处", f"{len(offenders)} 处", " | ".join(offenders[:3]))

    # R43 口径：favicon / apple-touch-icon 以 <link href="data:"> 内联，属自包含资源而非外链，
    # 故 link 标记只计「href 非 data:」者。base64 字母表不含 > 与引号，前瞻不会被载荷截断。
    markup = {"external <link": cr(r"""<link\b(?![^>]*href=["']data:)"""),
              "<script src": cr(r"<script[^>]*\bsrc\s*="), "<iframe": cr(r"<iframe")}
    textlev = {"@import": cs(r"@import"), "url(http": cs(r"url\(\s*['\"]?http"),
               'src="http': cs(r"""\bsrc\s*=\s*['"]https?://""")}
    L.check("S5 零外链不变量 · 标记级", all(v == 0 for v in markup.values()), "全部 0", markup)
    icon_links = re.findall(r"""<link\b[^>]*href=["']data:image/""", raw)
    L.check("S5c 图标 link 恰 2 枚且均为 data: 内联（R43）", len(icon_links) == 2,
            "2", len(icon_links))
    L.check("S5a 零外链不变量 · 文本级（已剥离巨型数据行）", all(v == 0 for v in textlev.values()),
            "全部 0", textlev,
            "全文直算 @import 会得 4：均在 L1667 dev-data 文档正文的 CSS 讲解文本内，非真声明")
    L.check("S5b @font-face 计数保持 2（均 data:；口径须带花括号且用全文）", cr(r"@font-face\s*\{") == 2,
            "2", cr(r"@font-face\s*\{"),
            "裸 grep '@font-face' 得 3：R36 注释文本含该词，非真实声明")

    tut_at = [i for i, l in enumerate(lines, 1) if l.lstrip().startswith('<script id="tut-data"')]
    dev_at = [i for i, l in enumerate(lines, 1) if 'id="dev-data"' in l]
    L.check("S6 两个巨型数据行仍在位且未被触碰（按内容定位，行号随轮次漂移属正常）",
            len(tut_at) == 1 and len(dev_at) == 1 and len(lines[tut_at[0] - 1]) > 1_000_000
            and len(lines[dev_at[0] - 1]) > 100_000,
            "各 1 行，且 tut-data >1MB / dev-data >100KB",
            f"tut-data@L{tut_at} len={len(lines[tut_at[0]-1]) if tut_at else 0} | "
            f"dev-data@L{dev_at} len={len(lines[dev_at[0]-1]) if dev_at else 0}")

    contracts = {
        "R31A TILT 宿主串(L3119)": ".ms-card,.mod-card,.pagecard,.quick,.step,.gate-role" in raw,
        "R21 涟漪 SEL 含两网格卡": "'ms-card'" in raw.replace("\"ms-card\"", "'ms-card'") or ".ms-card" in raw,
        "GSAP clearProps 串含 cover/mod 网格": ".cover-grid>*,.mod-grid>*" in raw.replace(
            ".cover-grid>*, .mod-grid>*", ".cover-grid>*,.mod-grid>*"),
        "GSAP grids 入场串": ".cover-grid,.mod-grid,.pagecards,.quick-grid,.gate-roles" in raw,
        "卡片类名未被改名": raw.count("ms-card") > 10 and raw.count("mod-card") > 10,
    }
    L.check("S7 跨轮次选择器契约完好（类名/SEL/TILT/GSAP 串未被改名）", all(contracts.values()),
            "全部 True", contracts)
    return raw


def js_block_check(L, raw):
    blocks = re.findall(r"<script(?![^>]*application/json)[^>]*>(.*?)</script>", raw, re.S)
    tmp = HERE / "_r37_block.js"
    bad = []
    for i, b in enumerate(blocks):
        if not b.strip():
            continue
        tmp.write_text(b, encoding="utf-8")
        r = subprocess.run(["node", "-e",
                            "const f=require('fs').readFileSync(process.argv[1],'utf8');"
                            "try{new Function(f)}catch(e){console.log(e.message);process.exit(1)}",
                            str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"block#{i}: {r.stdout.strip()[:70]}")
    tmp.unlink(missing_ok=True)
    L.check("S2 全部 JS 块通过编译（new Function，不执行）", not bad,
            f"{len(blocks)} 块 0 错误", f"{len(blocks)} 块 / {len(bad)} 错误", "; ".join(bad[:3]))


def w3c_check(L, skip):
    """html5lib = 项目 r19_w3c_check 用的等价官方解析器。
    口径：非 strict 解析收集 parser.errors 全量，并与改造前快照（R36 备份）逐项对比，
    要求「零新增错误」。strict=True 只能报第一处错误，且不是 parse() 的形参。"""
    if skip:
        L.skip("S1 html5lib 解析零新增错误", "与 R36 快照错误数相等", "--skip-w3c 显式跳过（最终交付前必须补跑）")
        return
    try:
        import html5lib
    except ImportError:
        L.skip("S1 html5lib 解析零新增错误", "与 R36 快照错误数相等", "html5lib 不可用")
        return

    def errs(path):
        parser = html5lib.HTMLParser()
        with io.open(str(path), encoding="utf-8") as f:
            parser.parse(f)
        return sorted({(e[1]) for e in parser.errors})

    snap = sorted(ROOT.glob("Meow Star Map 官网.backup-r36-*.html"))
    try:
        cur = errs(SRC)
    except Exception as e:
        L.check("S1 html5lib 解析零新增错误", False, "解析成功", f"{type(e).__name__}: {str(e)[:200]}")
        return
    if not snap:
        L.check("S1 html5lib 解析（无 R36 快照可比，仅报绝对错误数）", not cur,
                "0 类错误", f"{len(cur)} 类: {cur[:5]}")
        return
    before = errs(snap[0])
    L.check("S1 html5lib 解析零新增错误（vs R36 快照）", len(cur) <= len(before) and not set(cur) - set(before),
            f"错误类型不多于快照 {len(before)} 类且无新类型",
            f"当前 {len(cur)} 类 / 快照 {len(before)} 类 / 新增 {sorted(set(cur) - set(before))[:5]}")


def set_rt(page, mode):
    """返回是否真正切到了该透明度偏好。"""
    try:
        page.emulate_media(reduced_transparency=mode)
        return True
    except (TypeError, Exception):
        return False


def run():
    baseline_mode = "--baseline" in sys.argv
    L = Ledger()

    raw = static_checks(L)
    js_block_check(L, raw)
    w3c_check(L, "--skip-w3c" in sys.argv)

    errs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:120]))
        page.on("console", lambda m: errs.append("console: " + m.text[:120]) if m.type == "error" else None)

        rt_ok = set_rt(page, "reduce")
        if not rt_ok:
            L.skip("R6 prefers-reduced-transparency 双态", "reduce/no-preference 两态均满足 V1~V3",
                   "当前 playwright 不支持 reduced_transparency 形参；本机 RT 恒为 reduce，实跑即该机真实态")

        # ---- 1) 功能快照（7 hash × 浅/深）
        def snapshot():
            cur = {}
            set_rt(page, "no-preference")
            for theme in ("light", "dark"):
                page.emulate_media(color_scheme=theme)
                for h in HASHES:
                    page.goto(URL + h, wait_until="load")
                    page.wait_for_timeout(1500)
                    cur[f"{theme}|{h}"] = page.evaluate(JS_FUNC)
            return cur

        snap = snapshot()
        L.check("F11 控制台零报错 / 零未捕获异常（全导航累计）", not errs, "0", f"{len(errs)}", "; ".join(errs[:3]))

        # ---- 2) 交互回归
        page.emulate_media(color_scheme="light")
        page.goto(URL + "#/", wait_until="load")
        page.wait_for_timeout(1700)
        try:
            page.click("#lp-dl-btn")
            page.wait_for_timeout(1200)
            opened = page.evaluate("!document.querySelector('#lp-dl-menu').hidden")
            items = page.evaluate("[...document.querySelectorAll('.lp-dl-item')].map(a=>a.getAttribute('href'))")
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            closed = page.evaluate("document.querySelector('#lp-dl-menu').hidden")
            L.check("F5 资源下载面板开合 + 三网盘 href 逐字未变",
                    opened and closed and len(items) == 3 and items == snap["light|#/"]["dlItems"],
                    "展开→Escape 收起；href 与快照一致",
                    f"opened={opened} closed={closed} items={items}")
        except Exception as e:
            L.check("F5 资源下载面板开合 + 三网盘 href 逐字未变", False, "同上", f"异常 {e}")

        try:
            page.click("#about-qq-btn")
            page.wait_for_timeout(1000)
            qq = page.evaluate("document.querySelector('#about-qq-panel').classList.contains('is-open')")
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            qqc = page.evaluate("document.querySelector('#about-qq-panel').hidden")
            page.click("#about-wx-btn")
            page.wait_for_timeout(1000)
            wx = page.evaluate("!document.querySelector('#about-wx').hidden")
            page.keyboard.press("Escape")
            page.wait_for_timeout(800)
            wxc = page.evaluate("document.querySelector('#about-wx').hidden")
            ghosts = page.evaluate("[...document.querySelectorAll('.r31-ghost,.r28-ghost')].length")
            gr = page.evaluate("[...document.querySelectorAll('.r31-ghost,.r28-ghost')].map(g=>g.style.borderRadius||getComputedStyle(g).borderRadius)")
            L.check("F6+F10 关于板块 QQ/微信弹层 + 残影壳自删 + 残影圆角不被 --r-bento 污染",
                    qq and qqc and wx and wxc and ghosts == 0
                    and all("r-bento" not in (x or "") for x in gr),
                    "开→关→开→关；结束后残影壳计数 0 且其 radius 快照不含 r-bento",
                    f"qq={qq}/{qqc} wx={wx}/{wxc} ghost={ghosts} radii={gr}")
        except Exception as e:
            L.check("F6+F10 关于板块 QQ/微信弹层 + 残影壳自删 + 残影圆角不被 --r-bento 污染",
                    False, "同上", f"异常 {e}")

        try:
            page.goto(URL + "#/identity", wait_until="load")
            page.wait_for_timeout(1300)
            page.click("[data-role-pick='dev']")
            page.wait_for_timeout(1300)
            h1 = page.evaluate("location.hash")
            page.goto(URL + "#/identity", wait_until="load")
            page.wait_for_timeout(1200)
            page.click("[data-role-pick='user']")
            page.wait_for_timeout(1300)
            h2 = page.evaluate("location.hash")
            L.check("F3 门页双卡分流", h1 == "#/dev" and h2 == "#/tutorial",
                    "#/dev 与 #/tutorial", f"{h1} / {h2}")
        except Exception as e:
            L.check("F3 门页双卡分流", False, "#/dev 与 #/tutorial", f"异常 {e}")

        page.goto(URL + "#/tutorial", wait_until="load")
        page.wait_for_timeout(1600)
        try:
            page.fill("#searchbox", "水印")
            page.wait_for_timeout(800)
            hits = page.evaluate("document.querySelectorAll('#searchdrop .sr').length")
            page.fill("#searchbox", "zzz不存在zzz")
            page.wait_for_timeout(800)
            emptytxt = page.evaluate("document.querySelector('#searchdrop') ? document.querySelector('#searchdrop').textContent : ''")
            L.check("F4 搜索联想命中 + 空态文案", hits > 0 and "没有找到相关内容" in emptytxt,
                    "命中>0；乱码命中空态文案", f"hits={hits} empty={'没有找到相关内容' in emptytxt}")
        except Exception as e:
            L.check("F4 搜索联想命中 + 空态文案", False, "同上", f"异常 {e}")

        try:
            seq = []
            page.evaluate("localStorage.removeItem('nikki_theme')")
            for _ in range(3):
                page.click("#themebtn")
                page.wait_for_timeout(300)
                seq.append(page.evaluate(
                    "[document.documentElement.getAttribute('data-theme'),localStorage.getItem('nikki_theme')]"))
            page.reload(wait_until="load")
            page.wait_for_timeout(1500)
            persisted = page.evaluate("document.documentElement.getAttribute('data-theme')")
            # 既有设计事实：light/auto 态有意不设 data-theme 属性，仅 dark 态写入（AGENTS.md 主题机制）
            triples = [tuple(s) for s in seq]
            L.check("F7 主题三态循环 + 写 localStorage + 刷新持久化",
                    len(set(triples)) == 3 and ("dark", "dark") in triples
                    and persisted == seq[-1][0],
                    "三态互不相同、含 ('dark','dark')、reload 后属性等于末态；"
                    "light/auto 无 data-theme 属性属既有设计",
                    f"seq={seq} persisted={persisted}")
        except Exception as e:
            L.check("F7 主题三态循环 + 写 localStorage + 刷新持久化", False, "同上", f"异常 {e}")

        # ---- 3) 跨断点 × 跨主题 视觉硬指标
        fails = {k: [] for k in "v1 v2 v3 v4 v5 v6 r1 r2 r3 r5 nojs".split()}
        r5_checked = False
        for vp in GEOM_VIEWPORTS:
            page.set_viewport_size({"width": vp, "height": 900})
            for theme in ("light", "dark"):
                page.emulate_media(color_scheme=theme)
                for h in ("#/tutorial", "#/dev"):
                    page.goto(URL + h, wait_until="load")
                    page.wait_for_timeout(1800)
                    # 封面是 loading="lazy"，必须先滚进视口并等解码，否则 coverGapPx 测不到真值
                    page.evaluate("""async () => {
                      const g = document.querySelector('.cover-grid,.mod-grid');
                      if (g) g.scrollIntoView();
                      await new Promise(r => setTimeout(r, 400));
                      await Promise.all([...document.querySelectorAll('.ms-cover img')].map(i =>
                        (i.complete && i.naturalWidth) ? 1 : new Promise(res => {
                          i.onload = res; i.onerror = res; setTimeout(res, 2500); })));
                    }""")
                    g = page.evaluate(JS_GEOM)
                    k = f"{vp}/{theme}/{h}"
                    if g["scrollWidth"] > g["clientWidth"] + 1:
                        fails["r1"].append(f"{k} sw={g['scrollWidth']} cw={g['clientWidth']}")
                    grid = next((x for x in g["grids"] if x["sel"] in (".cover-grid", ".mod-grid")), None)
                    if not grid:
                        fails["v3"].append(f"{k} 未找到 Bento 网格")
                        continue
                    if grid["columnGap"] != "16px" or grid["rowGap"] != "16px":
                        fails["v3"].append(f"{k} {grid['sel']} gap={grid['columnGap']}/{grid['rowGap']}")
                    hero = next((c for c in g["cards"] if c["first"]), None)
                    if not hero:
                        fails["v4"].append(f"{k} 无首卡")
                        continue
                    wc, wp = (LIGHT_CARD, LIGHT_PAGE) if theme == "light" else (DARK_CARD, DARK_PAGE)
                    if hero["bg"] != wc:
                        fails["v1"].append(f"{k} 卡面={hero['bg']} 期望={wc}")
                    if g["htmlBg"] != wp:
                        fails["v1"].append(f"{k} 页面={g['htmlBg']} 期望={wp}")
                    if g["wrapBg"] not in (wp, None):
                        fails["v1"].append(f"{k} .wrap={g['wrapBg']} 期望=页面底 {wp}")
                    if hero["shadow"] != "none":
                        fails["v2"].append(f"{k} 静置投影未清 {hero['shadow'][:40]}")
                    if hero["bgImage"] != "none":
                        fails["v2"].append(f"{k} L973 渐变描边仍在")
                    if hero["inlineVar"] is None:
                        fails["v2"].append(f"{k} 未写 --r-bento（JS 兜底未生效？）")
                    for cd in g["cards"]:
                        t = radius_target(cd["short"])
                        if abs(cd["radius"] - t) > 0.7:
                            fails["v2"].append(f"{k} r={cd['radius']} 期望={round(t,2)} 短边={cd['short']}")
                        if not (abs(cd["radius"] - cd["radiusTR"]) < .01 and abs(cd["radius"] - cd["radiusBR"]) < .01):
                            fails["v2"].append(f"{k} 四角不等")
                        if cd.get("coverGapPx") is not None and cd["coverGapPx"] > 2:
                            fails["v6"].append(f"{k} 封面未填满，露灰底 {cd['coverGapPx']}px")
                    if g.get("ringRadius") and abs(g["ringRadius"] - hero["radius"]) > 0.7:
                        fails["v2"].append(f"{k} border-radius:inherit 环={g['ringRadius']} 卡面={hero['radius']}")
                    others = [c for c in g["cards"] if not c["first"]]
                    if vp >= 768:
                        # 注意：grid-column:span 2 解析为 start="span 2" / end="auto"，必须断 start
                        if hero["colStart"] != "span 2" or hero["rowStart"] != "span 2":
                            fails["v4"].append(f"{k} colStart={hero['colStart']} rowStart={hero['rowStart']}")
                        if others and hero["w"] * hero["h"] <= max(o["w"] * o["h"] for o in others):
                            fails["v4"].append(f"{k} Hero 面积非最大")
                        # 「边缘必须落在网格线上」= Hero 宽度恰等于前两列轨 + 一个列间距
                        tn = grid["trackNums"]
                        if len(tn) >= 2:
                            want = tn[0] + tn[1] + float(grid["columnGap"][:-2])
                            if abs(hero["w"] - want) > 0.8:
                                fails["v4"].append(f"{k} Hero 宽 {hero['w']} != 前两列轨之和 {round(want,2)}")
                        # Hero 左缘必须与第一列卡左缘同线
                        if others:
                            col1 = min(o["left"] for o in others)
                            if abs(hero["left"] - col1) > 0.8 and hero["left"] > col1 + 0.8:
                                fails["v4"].append(f"{k} Hero 左缘 {hero['left']} != 首列左缘 {col1}")
                        filled = 1 + len(others)
                        area_cells = filled + 3  # hero 占 4 格
                        if area_cells % grid["cols"] != 0:
                            trailing = grid["cols"] - (area_cells % grid["cols"])
                            if trailing > 1:
                                fails["v5"].append(f"{k} 尾部空洞 {trailing} 格（cols={grid['cols']}）")
                    else:
                        if grid["cols"] != 1:
                            fails["r2"].append(f"{k} 单列档列数={grid['cols']} 期望 1")
                        if hero["colStart"] != "auto":
                            fails["r2"].append(f"{k} ≤767px 未解跨列 colStart={hero['colStart']}")
                        if others and hero["h"] <= max(o["h"] for o in others):
                            fails["r3"].append(f"{k} 手机档 Hero 高度未大于兄弟卡")
            # 骨架同构（只测一次）。注意：静态骨架（L1664）在 domcontentloaded 之前就被 render()
            # 覆写，无法靠 wait_until 抢读到；改用等价脚手架复现 .skel-grid 的级联结果。
            if not r5_checked:
                page.emulate_media(color_scheme="light")
                page.set_viewport_size({"width": 1440, "height": 900})
                page.goto(URL + "#/tutorial", wait_until="load")
                page.wait_for_timeout(2200)
                sk = page.evaluate("""() => {
                  const real = document.querySelector('.cover-grid');
                  const W = real.getBoundingClientRect().width;
                  const host = document.createElement('div');
                  host.style.cssText = 'width:' + W + 'px';
                  const sk = document.createElement('div'); sk.className = 'skel-grid';
                  for (let i = 0; i < 9; i++) {
                    const c = document.createElement('div'); c.className = 'skel-cell';
                    const cv = document.createElement('div'); cv.className = 'skel skel-cover';
                    const bd = document.createElement('div'); bd.className = 'skel-body';
                    c.append(cv, bd); sk.append(c);
                  }
                  host.append(sk); document.body.append(host);
                  const cs = getComputedStyle(sk), f = getComputedStyle(sk.firstElementChild);
                  const r = {cols: cs.gridTemplateColumns.split(' ').length, gap: cs.columnGap,
                             colStart: f.gridColumnStart, rowStart: f.gridRowStart,
                             tracks: cs.gridTemplateColumns, w: sk.getBoundingClientRect().width};
                  host.remove();
                  return r;
                }""")
                real = page.evaluate("""() => {
                  const g = document.querySelector('.cover-grid'); if (!g) return null;
                  const cs = getComputedStyle(g), f = getComputedStyle(g.firstElementChild);
                  return {cols: cs.gridTemplateColumns.split(' ').length, gap: cs.columnGap,
                          colStart: f.gridColumnStart, rowStart: f.gridRowStart,
                          tracks: cs.gridTemplateColumns};
                }""")
                same = (sk and real and sk["cols"] == real["cols"] and sk["gap"] == real["gap"]
                        and sk["colStart"] == real["colStart"] and sk["rowStart"] == real["rowStart"]
                        and sk["tracks"] == real["tracks"])
                L.check("R4 骨架与真卡同构（列数/列轨/间距/Hero 跨列，防首屏 CLS）", bool(same),
                        "同容器宽下轨道串、间距与 Hero 跨列全等",
                        f"skeleton={sk} real={real}")
                r5_checked = True

        # CSS 兜底：无内联 --r-bento 时（JS 未跑/异常/不支持 RO）必须回落到 --r37-r
        fb = page.evaluate("""() => {
          const g = document.createElement('div'); g.className = 'cover-grid';
          g.style.cssText = 'width:600px';
          const c = document.createElement('a'); c.className = 'ms-card';
          g.append(c); document.body.append(g);
          const r = {radius: parseFloat(getComputedStyle(c).borderTopLeftRadius),
                     colStart: getComputedStyle(c).gridColumnStart,
                     hasVar: c.style.getPropertyValue('--r-bento') || null};
          g.remove(); return r;
        }""")
        L.check("R8a 无内联变量时 CSS 兜底圆角 = --r37-r 且 Hero 跨列仍成立",
                abs(fb["radius"] - FALLBACK_R) < 0.7 and fb["colStart"] == "span 2" and fb["hasVar"] is None,
                f"radius={FALLBACK_R} / colStart=span 2 / 无内联变量", fb)
        ctx2 = browser.new_context(java_script_enabled=False, viewport={"width": 1440, "height": 900})
        np = ctx2.new_page()
        np.goto(URL, wait_until="load")
        np.wait_for_timeout(900)
        ns = np.evaluate("""() => ({noscript: !!document.querySelector('noscript') &&
                /需要|启用/.test(document.querySelector('noscript').textContent),
                overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
                skel: !!document.querySelector('.skel-grid')})""")
        L.check("R8b 禁用 JS 时页面不破版（保留骨架与 noscript 提示，无横向溢出）",
                ns["noscript"] and not ns["overflow"],
                "noscript 提示在位 + 零横向溢出", ns)
        ctx2.close()

        for tag, label in [
            ("v1", "V1 配色非黑即白（浅 #F5F5F7/#FFF · 深 #1D1D1F/#000，含 .wrap 让位）"),
            ("v2", "V2 圆角 = clamp(16, 0.07x短边, 34) + 四角相等 + 静置零投影零渐变描边"),
            ("v3", "V3 Bento 网格横竖间距 = 16px"),
            ("v4", "V4 Hero 跨 2x2 + 面积/高度主导 + 边缘对齐网格线"),
            ("v5", "V5 空洞普查（内部无洞，尾部至多 1 格）"),
            ("v6", "V6 封面填满无灰带（L300 height:auto 不得压过 L143 height:100%）"),
            ("r1", "R1 全断点全主题零横向溢出"),
            ("r2", "R2 单列档解跨列（防 2px 隐式轨道复现）"),
            ("r3", "R3 手机档 Hero 仍为最大卡（高度口径）"),
        ]:
            L.check(label, not fails[tag], "全部断点 × 主题 × 视图通过",
                    f"{len(fails[tag])} 处不符", "; ".join(fails[tag][:8]))

        page.emulate_media(color_scheme="light")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(URL + "#/tutorial", wait_until="load")
        page.wait_for_timeout(1800)
        gt = page.evaluate(JS_GEOM)
        page.goto(URL + "#/m1", wait_until="load")
        page.wait_for_timeout(1600)
        gm = page.evaluate(JS_GEOM)
        page.goto(URL + "#/identity", wait_until="load")
        page.wait_for_timeout(1400)
        gi = page.evaluate(JS_GEOM)
        L.check("V2b 作用域收口：非 Bento 元素零内联 --r-bento",
                not gt["scopeLeak"] and not gm["scopeLeak"] and not gi["scopeLeak"], "0 处",
                f"tutorial={gt['scopeLeak']} m1={gm['scopeLeak']} identity={gi['scopeLeak']}")
        # 作用域外卡片：本轮明确不动，逐视图取真实存在的选择器
        keep = {".gate-role(门卡)": (gi, ".gate-role", 22.0),
                ".pagecard(列表卡)": (gm, ".pagecard", 24.0),
                ".quick(快捷卡)": (gt, ".quick", 24.0),
                ".step(步骤卡)": (gt, ".step", 16.0)}
        got = {}
        bad = []
        for name, (gr, sel, exp) in keep.items():
            v = gr["baselineRadii"].get(sel)
            got[name] = v
            if v is None or abs(v - exp) > 0.7:
                bad.append(f"{name}={v} 期望 {exp}")
        L.check("V2c 作用域外既有卡片圆角零回归（本轮只动两网格）", not bad,
                str({k: v[2] for k, v in keep.items()}), f"{got} | {bad}")
        L.check("V3b 区块级留白 = 24px（.sec-tip，同组 16 / 区块 24 的另一半）",
                gt["secTipMargin"] == "24px", "24px", str(gt["secTipMargin"]))

        page.goto(URL + "#/", wait_until="load")
        page.wait_for_timeout(1600)
        lp = page.evaluate(JS_GEOM)["textGradient"]
        page.goto(URL + "#/dev", wait_until="load")
        page.wait_for_timeout(1600)
        dv = page.evaluate(JS_GEOM)["textGradient"]
        L.check("V7 渐变文字每页至多一处（landing 的 lp-title 保留，dev 指标数字已去渐变）",
                lp >= 1 and dv == 0, "landing>=1 且 #/dev==0", f"landing={lp} dev={dv}")

        # ---- 4) 功能一致性比对
        snap2 = snapshot()
        if baseline_mode:
            BASE.write_text(json.dumps(snap2, ensure_ascii=False, indent=1), encoding="utf-8")
            L.skip("F1/F2/F12 改造前后功能一致性", "与 r37-baseline.json 逐位一致",
                   f"--baseline 模式已写入基线 {BASE.name}；改造完成后复跑本脚本即可比对")
        elif BASE.exists():
            old = json.loads(BASE.read_text(encoding="utf-8"))
            vdiff, cdiff = [], []
            for k in sorted(set(old) | set(snap2)):
                a, b = old.get(k, {}), snap2.get(k, {})
                if a.get("view") != b.get("view"):
                    vdiff.append(f"{k}: {a.get('view')} -> {b.get('view')}")
                for f in sorted(set(a) | set(b)):
                    if a.get(f) != b.get(f):
                        cdiff.append(f"{k}.{f}: {str(a.get(f))[:40]} -> {str(b.get(f))[:40]}")
            L.check("F1 七视图 × 双主题 data-view 路由映射与改造前逐位一致", not vdiff,
                    "0 处差异", f"{len(vdiff)} 处", "; ".join(vdiff[:4]))
            L.check("F2 卡片计数/链接/文案/图片属性/正文字数与改造前逐位一致", not cdiff,
                    "0 处差异", f"{len(cdiff)} 处", "; ".join(cdiff[:6]))
        else:
            L.skip("F1/F2 功能一致性比对", "逐位一致", f"{BASE.name} 不存在，先跑 --baseline")

        browser.close()

    sys.exit(L.report("R37 Bento Grid 专项探针 · " +
                      ("改造前基线捕获（R37 视觉项应 FAIL）" if baseline_mode else "改造后校验")))


if __name__ == "__main__":
    run()
