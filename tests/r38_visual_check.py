#!/usr/bin/env python3
"""R38 全站 Apple 收官 + 三态外观专项探针（20261027）

用法：
    python tests/r38_visual_check.py                 # 全量（含 html5lib strict，约 2-4 分钟）
    python tests/r38_visual_check.py --skip-w3c      # 跳过 html5lib strict
    python tests/r38_visual_check.py --skip-browser-fallback  # 跳过字体/无 JS 的额外内核

口径：file:// 协议；零新增依赖（playwright + html5lib + 标准库）。
未跑项显式 NOT-RUN，不当作通过。
"""
import argparse
import html5lib
import pathlib
import re
import sys
import tempfile

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "Meow Star Map 官网.html"
URL = SRC.resolve().as_uri()
SHOTS = ROOT / "tests" / "r38-shots"
HASHES = [("#/", "landing"), ("#/identity", "identity"), ("#/tutorial", "home"),
          ("#/dev", "dev"), ("#/m1", "module"), ("#/m1/m1p1", "page"), ("#/all", "all")]
LIGHT_BG = "#F5F5F7"
DARK_BG = "#1D1D1F"


class Ledger:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expected, actual, note=""):
        self.rows.append({"name": name, "status": "PASS" if ok else "FAIL",
                          "expected": str(expected), "actual": str(actual)[:600], "note": note})
        return bool(ok)

    def skip(self, name, expected, note):
        self.rows.append({"name": name, "status": "NOT-RUN", "expected": expected,
                          "actual": None, "note": note})

    def report(self):
        bad = [r for r in self.rows if r["status"] == "FAIL"]
        skip = [r for r in self.rows if r["status"] == "NOT-RUN"]
        print("\n" + "=" * 78 + "\nR38 全站 Apple 收官 + 三态外观专项探针\n" + "=" * 78)
        for r in self.rows:
            mark = "  ok  " if r["status"] == "PASS" else " FAIL " if r["status"] == "FAIL" else " skip "
            print(mark + r["name"])
            if r["status"] == "FAIL":
                print(f"        期望: {r['expected']}\n        实测: {r['actual']}")
                if r["note"]:
                    print(f"        备注: {r['note']}")
            elif r["status"] == "NOT-RUN":
                print(f"        原因: {r['note']}")
        print("-" * 78)
        print(f"合计 {len(self.rows)} | PASS {len(self.rows)-len(bad)-len(skip)} | FAIL {len(bad)} | NOT-RUN {len(skip)}")
        return 0 if not bad else 1


def _num(s):
    return float(re.sub(r"[^0-9.]", "", s or "0") or 0)


def parse_color(s):
    if not s:
        return None
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (1.0,)
    m = re.search(r"rgba?\(([^)]+)\)", s)
    if not m:
        return None
    parts = [p.strip() for p in re.split(r"[,/ ]+", m.group(1)) if p.strip()]
    if len(parts) < 3:
        return None
    alpha = float(parts[3]) if len(parts) > 3 else 1.0
    return (float(parts[0]), float(parts[1]), float(parts[2]), alpha)


def blend(fg, bg):
    if not fg or not bg:
        return None
    a = fg[3]
    return tuple(round(fg[i] * a + bg[i] * (1 - a)) for i in range(3)) + (1.0,)


def luminance(c):
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def ratio(a, b):
    if not a or not b:
        return 0
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-w3c", action="store_true")
    ap.add_argument("--skip-browser-fallback", action="store_true")
    args = ap.parse_args()
    L = Ledger()
    raw = SRC.read_text(encoding="utf-8")
    scan = "\n".join(line for line in raw.splitlines() if len(line) <= 100000)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ── 源码级：HTML / JS / 注释 / 外链 / R38 token ──
        if args.skip_w3c:
            L.skip("S1 html5lib strict 解析", "0 错误", "--skip-w3c")
        else:
            parser = html5lib.HTMLParser(strict=True)
            try:
                parser.parse(raw)
                err = parser.errors
            except Exception as e:  # noqa: BLE001 - strict parser raises on first error in some versions
                err = [str(e)]
            L.check("S1 html5lib strict 解析", not err, "0 错误", f"{len(err)} 个 | {err[:3]}")

        blank = browser.new_page()
        blocks = []
        for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", raw, re.S | re.I):
            attrs, code = m.group(1), m.group(2)
            if re.search(r"application/json", attrs, re.I) or re.search(r"\bsrc\s*=", attrs, re.I):
                continue
            if len(code) > 2_000_000:
                continue
            blocks.append((m.start(), code))
        bad_js = []
        for pos, code in blocks:
            if not code.strip():
                continue
            try:
                blank.evaluate("(c)=>{new Function(c);return true;}", code)
            except Exception as e:  # noqa: BLE001
                bad_js.append(f"@{pos}: {e}")
        blank.close()
        L.check("S2 全部 JS 块编译", not bad_js, "0 错误", f"块 {len(blocks)}；失败 {bad_js[:2]}")

        comments = re.findall(r"<!--(.*?)-->", raw, re.S)
        bad_comments = [c[:60] for c in comments if "--" in c]
        markers = raw.count("R38:BEGIN") == 1 and raw.count("R38:END") == 1 and \
                  raw.count("R38-UI:BEGIN") == 1 and raw.count("R38-UI:END") == 1
        L.check("S3 R38 注释对成对 + HTML 注释无连续双连字符", markers and not bad_comments,
                "4 标记各 1；注释 0 双连字符", f"markers={markers} bad={bad_comments[:2]}")

        external = {
            # R43 起 data: 内联的图标 link 不计外链（favicon / apple-touch-icon 自包含）。
            "<link http(s)>": len(re.findall(r"""<link\b(?![^>]*href=["']data:)""", scan, re.I)),
            "<script src>": len(re.findall(r"<script\b[^>]*\bsrc\s*=", scan, re.I)),
            "<iframe>": len(re.findall(r"<iframe\b", scan, re.I)),
            "@import": len(re.findall(r"@import\b", scan, re.I)),
            "url(http)": len(re.findall(r"url\(\s*['\"]?https?:", scan, re.I)),
            "img(http)": len(re.findall(r"<img\b[^>]*\bsrc\s*=\s*['\"]https?:", scan, re.I)),
        }
        fonts = len(re.findall(r"@font-face\s*\{", raw, re.I))
        L.check("S4 零外链资源 + 字体声明仍 2 处", all(v == 0 for v in external.values()) and fonts == 2,
                "全 0；@font-face 2", f"{external}; @font-face={fonts}")

        block_m = re.search(r"/\* ═══════ R38:BEGIN.*?/\* ═══════ R38:END ═══════ \*/", raw, re.S)
        block = block_m.group(0) if block_m else ""
        token_m = re.search(r":root\s*\{.*?\n\}", block, re.S)
        token_block = token_m.group(0) if token_m else ""
        rest = block.replace(token_block, "") if token_block else block
        hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", rest)
        tokens = re.findall(r"--([a-z0-9-]+)\s*:", token_block)
        unused = [t for t in dict.fromkeys(tokens) if not re.search(r"var\(--" + re.escape(t) + r"\b", raw)]
        L.check("S5 R38 新规则 hex 仅在 token 定义", bool(block) and not hexes,
                "R38 块存在；token 外 hex=0", f"块 {len(block)}B；token 外 {hexes[:8]}")
        L.check("S5b R38 新 token 均有消费", bool(tokens) and not unused,
                "全部 token 至少一处 var()", f"tokens={len(tokens)} unused={unused[:8]}")

        L.check("S6 data-look 静态默认 + head 读取",
                '<html lang="zh-CN" data-look="neutral">' in raw and "getItem('nikki_look')" in raw,
                "html data-look=neutral；head nikki_look", "found" if '<html lang="zh-CN" data-look="neutral">' in raw else "missing")
        L.check("S6b 数据块在位",
                'id="tut-data"' in raw and 'id="dev-data"' in raw and
                any(len(line) > 1_000_000 for line in raw.splitlines()),
                "tut-data/dev-data + 巨型行", "ok")

        # ── 浏览器主流程 ──
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        logs, pageerrors, reqfailed = [], [], []
        page.on("console", lambda m: logs.append((m.type, m.text)))
        page.on("pageerror", lambda e: pageerrors.append(str(e)))
        page.on("requestfailed", lambda r: reqfailed.append(r.url))
        page.goto(URL, wait_until="load", timeout=120000)
        page.wait_for_timeout(1600)
        page.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)

        def ev(expr, arg=None):
            return page.evaluate(expr) if arg is None else page.evaluate(expr, arg)

        def css(sel, prop):
            return page.evaluate("([s,p])=>{const e=document.querySelector(s);return e?getComputedStyle(e)[p]:null}", [sel, prop])

        def rect(sel):
            return page.evaluate("s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};}", sel)

        def set_look(v):
            page.evaluate("v=>document.documentElement.setAttribute('data-look',v)", v)

        def set_theme(v):
            page.evaluate("v=>{const e=document.documentElement;if(v==='dark')e.setAttribute('data-theme','dark');else e.removeAttribute('data-theme');}", v)

        def nav(h):
            page.evaluate("h=>{location.hash=h}", h)
            page.wait_for_timeout(650)

        def visible(sel):
            r = rect(sel)
            return bool(r and r["w"] > 1 and r["h"] > 1 and css(sel, "display") != "none")

        # U1 默认状态
        u1 = ev("""() => ({
          look: document.documentElement.getAttribute('data-look'),
          n: document.querySelectorAll('.look-btn').length,
          text: [...document.querySelectorAll('.look-btn')].map(b=>b.textContent.trim()),
          hidden: document.getElementById('look-menu').hidden,
          display: getComputedStyle(document.getElementById('look-menu')).display,
          bodyHasMenuText: document.body.innerText.includes('视觉风格')
        })""")
        L.check("U1 默认 neutral / 3 触发器 / 菜单隐藏 / 无额外 body 文本",
                u1["look"] == "neutral" and u1["n"] == 3 and u1["text"] == ["", "", ""] and
                u1["hidden"] and u1["display"] == "none" and not u1["bodyHasMenuText"],
                "neutral; 3; 空文本; hidden; 无菜单文本", u1)

        # U2 打开菜单 + 锚点 + 标签
        page.click("#lp-nav .look-btn")
        page.wait_for_timeout(150)
        u2 = ev("""() => {const m=document.getElementById('look-menu');const r=m.getBoundingClientRect();const n=document.querySelector('#lp-nav').getBoundingClientRect();return {open:!m.hidden,opts:document.querySelectorAll('.look-opt').length,labels:[...document.querySelectorAll('.look-opt b')].map(e=>e.textContent),role:m.getAttribute('role'),top:r.top,navBottom:n.bottom,expanded:document.querySelector('#lp-nav .look-btn').getAttribute('aria-expanded')};}""")
        L.check("U2 菜单打开 / 3 项 / 锚定导航下方 / aria",
                u2["open"] and u2["opts"] == 3 and u2["labels"] == ["中性黑白", "彩色氛围", "极简全白"] and
                u2["role"] == "group" and u2["top"] >= u2["navBottom"] + 6 and u2["expanded"] == "true",
                "open; 3 labels; top>=nav+6; aria-expanded=true", u2)

        # U3 选择 color + 存储隔离
        page.evaluate("()=>{localStorage.setItem('nikki_theme','light');localStorage.setItem('nikki_role','dev');localStorage.setItem('nikki_lp_theme','spectrum')}")
        page.click('.look-opt[data-look="color"]')
        page.wait_for_timeout(180)
        u3 = ev("""() => ({look:document.documentElement.getAttribute('data-look'), ls:localStorage.getItem('nikki_look'), hidden:document.getElementById('look-menu').hidden, theme:localStorage.getItem('nikki_theme'), role:localStorage.getItem('nikki_role'), lp:localStorage.getItem('nikki_lp_theme'), expanded:document.querySelector('#lp-nav .look-btn').getAttribute('aria-expanded')})""")
        L.check("U3 选择 color / 持久化 / 既有键隔离",
                u3["look"] == "color" and u3["ls"] == "color" and u3["hidden"] and
                u3["theme"] == "light" and u3["role"] == "dev" and u3["lp"] == "spectrum" and
                u3["expanded"] == "false",
                "color; hidden; keys unchanged", u3)

        # U4 刷新持久化 + 非法值回落
        page.reload(wait_until="load", timeout=120000)
        page.wait_for_timeout(1400)
        page.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)
        persisted = page.evaluate("document.documentElement.getAttribute('data-look')")
        page.evaluate("localStorage.setItem('nikki_look','not-a-look')")
        page.reload(wait_until="load", timeout=120000)
        page.wait_for_timeout(1400)
        page.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)
        fallback = page.evaluate("document.documentElement.getAttribute('data-look')")
        L.check("U4 刷新保持 color / 非法值回落 neutral", persisted == "color" and fallback == "neutral",
                "color -> neutral", f"{persisted} -> {fallback}")
        page.evaluate("window.__r38.set('neutral')")
        page.wait_for_timeout(120)

        # U5 Escape / 外点 / scroll / resize / hashchange / 焦点归还
        page.evaluate("()=>location.hash='#/'")
        page.wait_for_timeout(650)
        page.click("#lp-nav .look-btn")
        page.wait_for_timeout(120)
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        esc = page.evaluate("""() => ({hidden:document.getElementById('look-menu').hidden, focus:document.activeElement.classList.contains('look-btn'), exp:document.querySelector('#lp-nav .look-btn').getAttribute('aria-expanded')})""")
        page.click("#lp-nav .look-btn")
        page.wait_for_timeout(100)
        page.mouse.click(720, 520)
        page.wait_for_timeout(150)
        outside = page.evaluate("document.getElementById('look-menu').hidden")
        page.evaluate("location.hash='#/tutorial'")
        page.wait_for_timeout(650)
        page.click("#topbar .look-btn")
        page.wait_for_timeout(100)
        page.evaluate("window.scrollTo(0,260)")
        page.wait_for_timeout(350)
        scrolled = page.evaluate("document.getElementById('look-menu').hidden")
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(200)
        page.click("#topbar .look-btn")
        page.wait_for_timeout(100)
        page.set_viewport_size({"width": 1400, "height": 900})
        page.wait_for_timeout(250)
        resized = page.evaluate("document.getElementById('look-menu').hidden")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(250)
        page.click("#topbar .look-btn")
        page.wait_for_timeout(100)
        page.evaluate("location.hash='#/dev'")
        page.wait_for_timeout(500)
        routed = page.evaluate("document.getElementById('look-menu').hidden")
        L.check("U5 Escape/外点/滚动/resize/路由关闭 + 焦点归还",
                esc["hidden"] and esc["focus"] and esc["exp"] == "false" and outside and scrolled and resized and routed,
                "全部 close；Escape 焦点回触发器", f"esc={esc} outside={outside} scroll={scrolled} resize={resized} route={routed}")

        # U6 键盘打开
        page.evaluate("()=>{const b=document.querySelector('#topbar .look-btn');b.focus();}")
        page.keyboard.press("Enter")
        page.wait_for_timeout(150)
        kb = page.evaluate("""() => ({open:!document.getElementById('look-menu').hidden, focus:document.activeElement.classList.contains('look-opt')})""")
        page.keyboard.press("Escape")
        page.wait_for_timeout(120)
        kb_focus = page.evaluate("document.activeElement.classList.contains('look-btn')")
        L.check("U6 键盘 Enter 打开 / 焦点入选项 / Escape 归还", kb["open"] and kb["focus"] and kb_focus,
                "open; focus opt; Escape -> trigger", f"{kb}; focusBack={kb_focus}")

        # U7 三视图触发点 + identity fab 不挡内容
        nav("#/tutorial")
        top_visible = visible("#topbar .look-btn")
        nav("#/identity")
        fab_visible = visible(".look-fab")
        fab = rect(".look-fab")
        h1 = rect(".gate h1")
        card = rect(".gate-role")
        def overlap(a, b):
            return bool(a and b and not (a["right"] <= b["x"] or a["x"] >= b["right"] or a["bottom"] <= b["y"] or a["y"] >= b["bottom"]))
        fab_hit = overlap(fab, h1) or overlap(fab, card)
        nav("#/")
        lp_visible = visible("#lp-nav .look-btn")
        L.check("U7 topbar/lp-nav/identity fab 三处挂载 + fab 不挡门页内容",
                top_visible and fab_visible and lp_visible and not fab_hit,
                "topbar=visible; fab=visible; lp-nav=visible; 不重叠", f"top={top_visible} fab={fab_visible} lp={lp_visible} overlap={fab_hit}")

        # U8 菜单在 390/561 视口内且位于宿主下方
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(200)
        nav("#/tutorial")
        page.click("#topbar .look-btn")
        page.wait_for_timeout(130)
        m390 = ev("""() => {const m=document.getElementById('look-menu').getBoundingClientRect(),t=document.getElementById('topbar').getBoundingClientRect();return {x:m.x,y:m.y,right:m.right,bottom:m.bottom,top:m.top,vw:innerWidth,vh:innerHeight,hostBottom:t.bottom};}""")
        page.keyboard.press("Escape")
        page.set_viewport_size({"width": 561, "height": 800})
        page.wait_for_timeout(200)
        nav("#/")
        page.click("#lp-nav .look-btn")
        page.wait_for_timeout(130)
        m561 = ev("""() => {const m=document.getElementById('look-menu').getBoundingClientRect(),n=document.querySelector('#lp-nav').getBoundingClientRect();return {x:m.x,y:m.y,right:m.right,bottom:m.bottom,top:m.top,vw:innerWidth,vh:innerHeight,hostBottom:n.bottom};}""")
        page.keyboard.press("Escape")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(200)
        okfit = all(m["x"] >= 0 and m["y"] >= 0 and m["right"] <= m["vw"] + 1 and m["bottom"] <= m["vh"] + 1 and m["top"] >= m["hostBottom"] + 6 for m in (m390, m561))
        L.check("U8 390/561 菜单视口内 + 宿主下方", okfit, "fit + below host", f"390={m390} 561={m561}")

        # V1 neutral 表面
        set_theme("light"); set_look("neutral")
        nav("#/tutorial")
        v1a = ev("""() => {const h=getComputedStyle(document.querySelector('.hero'));return {bg:h.backgroundColor,img:h.backgroundImage,r:h.borderTopLeftRadius,sh:h.boxShadow};}""")
        nav("#/dev")
        v1b = ev("""() => {const h=getComputedStyle(document.querySelector('.dev-hero'));return {bg:h.backgroundColor,img:h.backgroundImage,r:h.borderTopLeftRadius,sh:h.boxShadow,title:getComputedStyle(document.querySelector('.dev-hero .page-title')).color};}""")
        nav("#/identity")
        v1c = ev("""() => {const g=getComputedStyle(document.querySelector('.gate-role'));return {r:g.borderTopLeftRadius,sh:g.boxShadow,bg:g.backgroundColor,emoji:getComputedStyle(document.querySelector('.gr-emoji')).width};}""")
        nav("#/m1")
        v1d = ev("""() => {const p=getComputedStyle(document.querySelector('.pagecard'));return {bg:p.backgroundColor,r:p.borderTopLeftRadius,sh:p.boxShadow};}""")
        nav("#/m1/m1p1")
        v1e = ev("""() => {const w=getComputedStyle(document.querySelector('.wrap'));const r=getComputedStyle(document.querySelector('.rel'));const g=getComputedStyle(document.querySelector('.pager a'));return {wr:w.borderTopLeftRadius,wsh:w.boxShadow,wb:w.borderTopWidth,rr:r.borderTopLeftRadius,rsh:r.boxShadow,gr:g.borderTopLeftRadius,gsh:g.boxShadow};}""")
        nav("#/")
        v1f = ev("""() => ({cta:getComputedStyle(document.querySelector('.lp-cta')).borderTopLeftRadius,dl:getComputedStyle(document.querySelector('.lp-dl-btn')).borderTopLeftRadius,dlsh:getComputedStyle(document.querySelector('.lp-dl-btn')).boxShadow})""")
        v1 = (v1a["bg"] == "rgb(255, 255, 255)" and v1a["img"] == "none" and _num(v1a["r"]) == 28 and v1a["sh"] == "none" and
              v1b["bg"] == "rgb(0, 0, 0)" and v1b["img"] == "none" and _num(v1b["r"]) == 28 and v1b["sh"] == "none" and v1b["title"] == "rgb(255, 255, 255)" and
              _num(v1c["r"]) == 22 and v1c["sh"] == "none" and v1c["emoji"] == "56px" and
              v1d["bg"] == "rgb(245, 245, 247)" and _num(v1d["r"]) == 24 and v1d["sh"] == "none" and
              _num(v1e["wr"]) == 28 and v1e["wsh"] == "none" and _num(v1e["wb"]) == 1 and _num(v1e["rr"]) == 22 and v1e["rsh"] == "none" and _num(v1e["gr"]) == 22 and v1e["gsh"] == "none" and
              _num(v1f["cta"]) >= 100 and _num(v1f["dl"]) >= 100 and v1f["dlsh"] == "none")
        L.check("V1 neutral 表面（hero/dev/gate/card/wrap/目录/胶囊按钮）", v1,
                "hero 白/28/无阴影；dev 黑/28；gate 22；pagecard 灰/24；wrap 28；按钮胶囊",
                f"{v1a} {v1b} {v1c} {v1d} {v1e} {v1f}")

        # V2 color 表面
        set_look("color")
        nav("#/tutorial")
        v2a = ev("""() => ({hero:getComputedStyle(document.querySelector('.hero')).backgroundImage,ambient:getComputedStyle(document.body,'::before').backgroundImage,shadow:getComputedStyle(document.querySelector('.hero')).boxShadow})""")
        nav("#/dev")
        v2b = ev("""() => ({hero:getComputedStyle(document.querySelector('.dev-hero')).backgroundImage,color:getComputedStyle(document.querySelector('.dev-hero')).color,stat:getComputedStyle(document.querySelector('.dev-hero .dev-stats .stat i')).color})""")
        L.check("V2 color 恢复彩色 hero/环境光且保持新半径/无阴影",
                "linear-gradient" in (v2a["hero"] or "") and "gradient" in (v2a["ambient"] or "") and v2a["shadow"] == "none" and
                "linear-gradient" in (v2b["hero"] or "") and v2b["color"] == "rgb(38, 42, 51)" and v2b["stat"] == "rgb(78, 93, 104)",
                "彩色 hero + ambient；无阴影；正文深色", f"{v2a} {v2b}")

        # V3 plain 表面 + plain×dark
        set_look("plain")
        nav("#/tutorial")
        v3a = ev("""() => {const h=getComputedStyle(document.querySelector('.hero'));return {img:h.backgroundImage,bg:h.backgroundColor,word:getComputedStyle(document.querySelector('.hero'),'::before').display};}""")
        nav("#/dev")
        v3b = ev("""() => {const d=getComputedStyle(document.querySelector('.dev-hero'));return {img:d.backgroundImage,bg:d.backgroundColor,color:d.color,title:getComputedStyle(document.querySelector('.dev-hero .page-title')).color,sub:getComputedStyle(document.querySelector('.dev-hero-sub')).color};}""")
        nav("#/")
        v3c = ev("""() => {const t=getComputedStyle(document.querySelector('.lp-title'));return {img:t.backgroundImage,color:t.color,fill:t.webkitTextFillColor,word:getComputedStyle(document.querySelector('.lp-hero'),'::before').display,dots:getComputedStyle(document.querySelector('.lp-thdots')).display,about:getComputedStyle(document.querySelector('.about-sec')).backgroundColor,soc:getComputedStyle(document.querySelector('.about-soc-btn svg')).filter};}""")
        set_theme("dark"); set_look("plain")
        nav("#/tutorial")
        v3d = ev("""() => ({bg:getComputedStyle(document.querySelector('.hero')).backgroundColor,wrap:getComputedStyle(document.querySelector('.wrap-home')).backgroundColor,title:getComputedStyle(document.querySelector('.hero h1')).color})""")
        nav("#/dev")
        v3e = ev("""() => ({bg:getComputedStyle(document.querySelector('.dev-hero')).backgroundColor,color:getComputedStyle(document.querySelector('.dev-hero')).color,sub:getComputedStyle(document.querySelector('.dev-hero-sub')).color})""")
        set_theme("light"); set_look("neutral")
        L.check("V3 plain 去色/去水印/隐藏圆点 + plain×dark 单色",
                v3a["img"] == "none" and v3a["bg"] == "rgb(255, 255, 255)" and v3a["word"] == "none" and
                v3b["img"] == "none" and v3b["bg"] == "rgb(255, 255, 255)" and v3b["color"] == "rgb(38, 42, 51)" and v3b["title"] == "rgb(38, 42, 51)" and v3b["sub"] == "rgb(107, 114, 128)" and
                v3c["img"] == "none" and v3c["color"] != "rgba(0, 0, 0, 0)" and v3c["fill"] != "rgba(0, 0, 0, 0)" and v3c["word"] == "none" and v3c["dots"] == "none" and v3c["about"] == "rgb(255, 255, 255)" and "grayscale" in (v3c["soc"] or "") and
                v3d["bg"] == "rgb(0, 0, 0)" and v3d["wrap"] == "rgb(0, 0, 0)" and v3d["title"] == "rgb(232, 236, 244)" and
                v3e["bg"] == "rgb(0, 0, 0)" and v3e["color"] == "rgb(232, 236, 244)" and v3e["sub"] == "rgb(154, 166, 189)",
                "plain 白/黑单色；无水印/渐变/圆点；暗色墨黑", f"{v3a} {v3b} {v3c} {v3d} {v3e}")

        # V4 排版
        nav("#/tutorial")
        v4a = ev("""() => {const b=getComputedStyle(document.body);const h=getComputedStyle(document.querySelector('.hero h1'));const s=getComputedStyle(document.querySelector('.hero-sub'));return {font:b.fontFamily,hw:h.fontWeight,hs:parseFloat(h.fontSize),sw:s.fontWeight};}""")
        v4c = ev("""() => {const e=document.querySelector('.sec-tip');return {small:e?parseFloat(getComputedStyle(e).fontSize):0};}""")
        nav("#/m1")
        v4b = ev("""() => ({w:getComputedStyle(document.querySelector('h1.page-title')).fontWeight,size:parseFloat(getComputedStyle(document.querySelector('h1.page-title')).fontSize)})""")
        v4e = ev("""() => {const e=document.querySelector('.crumbs');return {crumb:e?parseFloat(getComputedStyle(e).fontSize):0};}""")
        nav("#/")
        v4d = ev("""() => ({title:getComputedStyle(document.querySelector('.lp-title')).fontFamily,weight:getComputedStyle(document.querySelector('.lp-title')).fontWeight,eyebrow:parseFloat(getComputedStyle(document.querySelector('.lp-eyebrow')).fontSize)})""")
        L.check("V4 Inter/Noto 栈、700 主视觉、600 页标题、300 副文、≥12px 小字",
                "Inter" in v4a["font"] and "Noto Sans SC" in v4a["font"] and v4a["hw"] == "700" and v4a["hs"] >= 60 and v4a["sw"] == "300" and
                v4b["w"] == "600" and v4b["size"] >= 30 and v4c["small"] >= 12 and v4e["crumb"] >= 12 and
                "Inter" in v4d["title"] and v4d["weight"] == "700" and v4d["eyebrow"] >= 12,
                "Inter+Noto; hero 700/≥60; page 600; sub 300; ≥12",
                f"{v4a} {v4b} {v4c} {v4e} {v4d}")

        # V5 AA 对比度（含四套 landing 主题）
        def var(name):
            return page.evaluate("n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim()", name)

        def contrast_ok(fg, bg, need):
            f, b = parse_color(fg), parse_color(bg)
            if f and f[3] < 1:
                f = blend(f, b)
            return ratio(f, b), ratio(f, b) >= need

        light_bg = var("--bg"); light_card = var("--card")
        checks = []
        for fg_name, bg_val, need, label in [
            ("--tx", light_bg, 4.5, "light text"),
            ("--color-slim-1", light_bg, 4.5, "light slim-1"),
            ("--mut", light_card, 4.5, "light mut/card"),
            ("--ac-deep", light_bg, 4.5, "light ac-deep"),
            ("--color-ink-on-dark-2", "#000000", 7.0, "on-dark-2"),
        ]:
            got, ok = contrast_ok(var(fg_name), bg_val, need)
            checks.append((label, round(got, 2), need, ok))
        # landing themes
        theme_reports = []
        page.evaluate("()=>{const r=document.querySelector('.lp-root');r.className='lp-root lp-theme-slim';}")
        page.wait_for_timeout(80)
        for tid, bg, need, min_need in [("slim", light_bg, 3.0, 3.0), ("spectrum", light_bg, 3.0, 3.0), ("energy", "#0B0C10", 3.0, 3.0), ("deep", "#0E5CA5", 3.0, 3.0)]:
            page.evaluate("t=>{const r=document.querySelector('.lp-root');r.className='lp-root lp-theme-'+t;}", tid)
            page.wait_for_timeout(60)
            grad = css(".lp-title", "backgroundImage")
            stops = [f"rgb({m[0]},{m[1]},{m[2]})" for m in re.findall(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", grad or "")]
            stops_got = [ratio(parse_color(s), parse_color(bg)) for s in stops]
            fallback = page.evaluate("()=>getComputedStyle(document.querySelector('.lp-root')).getPropertyValue('--lp-grad-fallback').trim()")
            t_ok = bool(stops_got) and min(stops_got) >= need
            fb, fok = contrast_ok(fallback, bg, min_need)
            if tid == "deep":
                eyebrow = css(".lp-eyebrow", "color"); foot = css(".lp-foot", "color")
                e1, ok1 = contrast_ok(eyebrow, "#024F97", 4.5); e2, ok2 = contrast_ok(foot, "#1D6EB6", 4.5)
                t_ok = t_ok and ok1 and ok2
                theme_reports.append((tid, "stops", round(min(stops_got), 2) if stops_got else 0, t_ok, "eyebrow/foot", round(min(e1, e2), 2), "fallback", round(fb, 2), fok))
            else:
                theme_reports.append((tid, len(stops), round(min(stops_got), 2) if stops_got else 0, t_ok, "fallback", round(fb, 2), fok))
        page.evaluate("()=>{const r=document.querySelector('.lp-root');r.className='lp-root lp-theme-slim';}")
        set_theme("dark")
        dark_bg = var("--bg"); dark_card = var("--card")
        for fg_name, bg_val, need, label in [
            ("--tx", dark_bg, 4.5, "dark text"),
            ("--color-slim-3", dark_bg, 4.5, "dark slim-3"),
            ("--mut", dark_card, 4.5, "dark mut/card"),
        ]:
            got, ok = contrast_ok(var(fg_name), bg_val, need)
            checks.append((label, round(got, 2), need, ok))
        dark_themes = []
        for tid in ("slim", "spectrum"):
            page.evaluate("t=>{const r=document.querySelector('.lp-root');r.className='lp-root lp-theme-'+t;}", tid)
            page.wait_for_timeout(60)
            grad = css(".lp-title", "backgroundImage")
            dstops = [f"rgb({m[0]},{m[1]},{m[2]})" for m in re.findall(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", grad or "")]
            dgot = [ratio(parse_color(s), parse_color(dark_bg)) for s in dstops]
            dfallback = page.evaluate("()=>getComputedStyle(document.querySelector('.lp-root')).getPropertyValue('--lp-grad-fallback').trim()")
            dfb, dfok = contrast_ok(dfallback, dark_bg, 3.0)
            dark_themes.append((tid, round(min(dgot), 2) if dgot else 0, bool(dgot) and min(dgot) >= 3.0, round(dfb, 2), dfok))
        page.evaluate("()=>{const r=document.querySelector('.lp-root');r.className='lp-root lp-theme-slim';}")
        set_theme("light")
        all_ok = all(c[3] for c in checks) and all(r[3] and r[-1] for r in theme_reports) and all(r[2] and r[4] for r in dark_themes)
        L.check("V5 WCAG AA 关键文本 + landing 渐变（亮/暗）",
                all_ok, "正文 ≥4.5；大字/渐变 ≥3；深蓝 eyebrow/footer ≥4.5",
                f"base={checks}; light={theme_reports}; dark={dark_themes}")

        # V6 横向溢出矩阵（5 视口 × 2 主题 × 7 路由 + 窄档）
        overflow = []
        for w, h in [(390, 844), (768, 900), (1440, 900), (1920, 1000), (2560, 1200)]:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(160)
            for theme in ("light", "dark"):
                set_theme(theme)
                page.wait_for_timeout(80)
                for hsh, name in HASHES:
                    nav(hsh)
                    sw, cw = page.evaluate("[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
                    if sw > cw + 1:
                        overflow.append(f"{w}/{theme}/{name}:{sw}>{cw}")
        set_theme("light")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(150)
        for w, h in [(360, 800), (561, 800)]:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(150)
            for hsh in ("#/", "#/tutorial", "#/dev"):
                nav(hsh)
                sw, cw = page.evaluate("[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
                if sw > cw + 1:
                    overflow.append(f"{w}/light/{hsh}:{sw}>{cw}")
        page.set_viewport_size({"width": 1440, "height": 900})
        nav("#/")
        L.check("V6 全断点/双主题/七路由零横向溢出", not overflow, "0", overflow[:6])

        # V7 路由映射
        route_bad = []
        for hsh, expected in HASHES:
            nav(hsh)
            got = page.evaluate("document.body.dataset.view")
            if got != expected:
                route_bad.append(f"{hsh}:{got}!={expected}")
        L.check("V7 七路由 data-view 不变", not route_bad, "逐位一致", route_bad)

        # V8 控制台累计
        errs = [x for x in logs if x[0] == "error"]
        warn = [x for x in logs if x[0] == "warning"]
        L.check("V8 控制台 0 error / 0 pageerror / 0 资源失败", not errs and not pageerrors and not reqfailed,
                "0/0/0", f"console={errs[:3]} pageerror={pageerrors[:3]} reqfailed={reqfailed[:3]}；warnings={warn[:2]}")
        ctx.close()

        # V9 reduced motion
        if args.skip_browser_fallback:
            L.skip("V9 prefers-reduced-motion", "新层无动画", "--skip-browser-fallback")
        else:
            rm = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            rp = rm.new_page()
            rp.goto(URL, wait_until="load", timeout=120000)
            rp.wait_for_timeout(1200)
            rp.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)
            rp.evaluate("()=>location.hash='#/tutorial'")
            rp.wait_for_timeout(600)
            rp.click("#topbar .look-btn")
            rp.wait_for_timeout(120)
            rmv = rp.evaluate("""() => ({mq:matchMedia('(prefers-reduced-motion: reduce)').matches, menuAnim:getComputedStyle(document.getElementById('look-menu')).animationName, btn:getComputedStyle(document.querySelector('#topbar .look-btn')).transitionDuration, heroAnim:getComputedStyle(document.querySelector('.hero')).animationName})""")
            rm.close()
            L.check("V9 prefers-reduced-motion 新层无动画", rmv["mq"] and rmv["menuAnim"] == "none" and rmv["heroAnim"] == "none",
                    "mq=true; animation none", rmv)

        # V10 降低透明度（本机恒 reduce）
        rt = browser.new_context(viewport={"width": 1440, "height": 900})
        tp = rt.new_page()
        tp.goto(URL, wait_until="load", timeout=120000)
        tp.wait_for_timeout(1100)
        tp.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)
        rt_mq = tp.evaluate("matchMedia('(prefers-reduced-transparency: reduce)').matches")
        if rt_mq:
            tp.evaluate("()=>{document.documentElement.removeAttribute('data-theme');document.documentElement.setAttribute('data-look','color');location.hash='#/identity'}")
            tp.wait_for_timeout(600)
            gate = tp.evaluate("getComputedStyle(document.querySelector('.gate-role')).backgroundColor")
            menu = tp.evaluate("getComputedStyle(document.getElementById('look-menu')).backdropFilter")
            L.check("V10 降低透明度：彩色门卡/菜单回实底", gate == "rgb(255, 255, 255)" and menu == "none", "gate=card; menu no backdrop", f"{gate} / {menu}")
        else:
            L.skip("V10 降低透明度", "reduce", "当前环境 no-preference")
        rt.close()

        # V11 no-JS
        if args.skip_browser_fallback:
            L.skip("V11 禁用 JS 默认 neutral 不破版", "中性骨架", "--skip-browser-fallback")
        else:
            nj = browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            np = nj.new_page()
            np.goto(URL, wait_until="load", timeout=120000)
            njr = np.evaluate("""() => ({look:document.documentElement.getAttribute('data-look'), ui:document.querySelectorAll('.look-btn').length, text:document.body.innerText.length, sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth})""")
            nj.close()
            L.check("V11 禁用 JS 默认 neutral 不破版", njr["look"] == "neutral" and njr["ui"] == 0 and njr["text"] > 0 and njr["sw"] <= njr["cw"] + 1, "neutral; no UI; no overflow", njr)

        # V12 字体回退（临时移除两处 data: 字体声明）
        if args.skip_browser_fallback:
            L.skip("V12 字体移除后系统兜底", "可读", "--skip-browser-fallback")
        else:
            tmp = ROOT / "tests" / "r38-fontfallback.tmp.html"
            try:
                lines = []
                for line in raw.splitlines(True):
                    if "@font-face" in line and "base64" in line:
                        lines.append("/* R38 font fallback test: face removed */\n")
                    else:
                        lines.append(line)
                tmp.write_text("".join(lines), encoding="utf-8")
                fc = browser.new_context(viewport={"width": 1440, "height": 900})
                fp = fc.new_page()
                fp.goto(tmp.resolve().as_uri(), wait_until="load", timeout=120000)
                fp.wait_for_timeout(1000)
                fr = fp.evaluate("""() => ({faces:[...document.fonts].map(f=>f.family.replace(/\\"/g,'')), text:document.body.innerText.length, sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth})""")
                fc.close()
                embedded = [f for f in fr["faces"] if f in ("Inter", "Noto Sans SC")]
                L.check("V12 字体移除后系统兜底", not embedded and fr["text"] > 0 and fr["sw"] <= fr["cw"] + 1,
                        "无内嵌 Inter/Noto FontFace；文本仍可读、无溢出", fr)
            finally:
                try:
                    tmp.unlink()
                except Exception:
                    pass

        # V13 background-clip 关闭后纯色兜底
        fc = browser.new_context(viewport={"width": 1440, "height": 900})
        fp = fc.new_page()
        fp.goto(URL, wait_until="load", timeout=120000)
        fp.wait_for_timeout(1200)
        fp.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)
        fp.evaluate("""()=>{const s=document.createElement('style');s.id='r38-clip-off';s.textContent='.lp-title.text-gradient{background-image:none!important;-webkit-background-clip:border-box!important;background-clip:border-box!important;color:var(--lp-grad-fallback)!important;-webkit-text-fill-color:currentColor!important}';document.head.appendChild(s);}""")
        fp.wait_for_timeout(100)
        clip = fp.evaluate("""() => {const t=getComputedStyle(document.querySelector('.lp-title'));return {img:t.backgroundImage,color:t.color,fill:t.webkitTextFillColor,fb:getComputedStyle(document.querySelector('.lp-root')).getPropertyValue('--lp-grad-fallback').trim()};}""")
        fc.close()
        cgot, cok = contrast_ok(clip["fb"], light_bg, 3.0)
        L.check("V13 background-clip 关闭后纯色可读", clip["img"] == "none" and clip["color"] != "rgba(0, 0, 0, 0)" and clip["fill"] != "rgba(0, 0, 0, 0)" and cok,
                "无背景图；color 非透明；fallback ≥3", f"{clip} ratio={round(cgot,2)}")

        # V14 plain×energy 与存储隔离
        fc = browser.new_context(viewport={"width": 1440, "height": 900})
        fp = fc.new_page()
        fp.goto(URL, wait_until="load", timeout=120000)
        fp.evaluate("()=>{localStorage.setItem('nikki_theme','light');localStorage.setItem('nikki_role','dev');localStorage.setItem('nikki_lp_theme','energy');localStorage.setItem('nikki_look','plain')}")
        fp.reload(wait_until="load", timeout=120000)
        fp.wait_for_timeout(1300)
        fp.wait_for_function("window.__r38 && window.__r38.ver==='r38.0'", timeout=15000)
        pe = fp.evaluate("""() => {const t=getComputedStyle(document.querySelector('.lp-title'));return {look:document.documentElement.getAttribute('data-look'),cls:document.querySelector('.lp-root').className,img:t.backgroundImage,color:t.color,dots:getComputedStyle(document.querySelector('.lp-thdots')).display,nav:getComputedStyle(document.querySelector('#lp-nav')).backgroundColor,theme:localStorage.getItem('nikki_theme'),role:localStorage.getItem('nikki_role'),lp:localStorage.getItem('nikki_lp_theme')};}""")
        fc.close()
        L.check("V14 plain 压过 landing energy / 三键隔离",
                pe["look"] == "plain" and "lp-theme-energy" in pe["cls"] and pe["img"] == "none" and pe["color"] != "rgba(0, 0, 0, 0)" and pe["dots"] == "none" and
                pe["theme"] == "light" and pe["role"] == "dev" and pe["lp"] == "energy",
                "plain 生效；theme/role/lp 不变", pe)

        browser.close()

    return L.report()


if __name__ == "__main__":
    sys.exit(main())
