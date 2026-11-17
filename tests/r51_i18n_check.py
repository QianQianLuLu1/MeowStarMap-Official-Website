#!/usr/bin/env python3
"""R52 六语国际化专项探针。

用法：
    python tests/r51_i18n_check.py            全量（源码级 + 运行时级）
    python tests/r51_i18n_check.py --skip-slow 跳过六语 × 四断点的溢出矩阵

协议：file:// 直开，无端口自起（与 r37/r38/r39/r41/r42/r43/r45 同口径）。
依赖：playwright（运行时级）+ 标准库（源码级；html5lib 不参与）。

口径要点：
  * 语言判定链是 `__i18nPin > ?lang= > localStorage.nikki_lang > navigator.languages > zh`，
    故「zh 基线」用 add_init_script 钉住，不依赖浏览器 locale。
  * 切换语言必须走 `window.__i18n.set()`（等同于点击菜单项），不手改 html 属性——手改会绕过
    缓存失效与重渲，测不到真实行为。
  * 「无中文残留」只对**营销侧 + 教程正文**断言，开发者文档库按设计永久中文，跳过。
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "Meow Star Map 官网.html"
LOCALES = ROOT / "locales"
LANGS = ["zh", "en", "fr", "es", "ru", "ar"]
CJK = re.compile(r"[\u4e00-\u9fff]")
BI_PREFIX = ("doc.", "gate.", "top.", "tut.", "dev.", "search.", "notice.")
# 品牌与专有名词白名单：这些词在中英混排里保留中文属预期
BRAND_OK = ("纤璐不会玩摄影", "喵星图")


class L:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expect="", actual=""):
        self.rows.append((bool(ok), name, expect, actual))

    def skip(self, name, why):
        self.rows.append((None, name, why, "NOT-RUN"))

    def report(self):
        p = sum(1 for ok, *_ in self.rows if ok is True)
        f = sum(1 for ok, *_ in self.rows if ok is False)
        s = sum(1 for ok, *_ in self.rows if ok is None)
        for ok, name, expect, actual in self.rows:
            tag = "PASS" if ok is True else ("FAIL" if ok is False else "SKIP")
            print(f"[{tag}] {name}")
            if ok is not True and (expect or actual):
                print(f"        期望: {expect}\n        实测: {actual}")
        print(f"\n合计 {len(self.rows)} 项：PASS {p} / FAIL {f} / SKIP {s}")
        return 1 if f else 0


def src_checks(ck: L, raw: str):
    # ── 1. 五个数据块可解析，且与 zh 键表分层 parity ──
    zh_keys = {}
    if (LOCALES / "ui.zh.json").exists():
        zh_keys = json.loads((LOCALES / "ui.zh.json").read_text(encoding="utf-8"))
    ck.check("A1 ui.zh.json 在位且非空", len(zh_keys) > 200, ">200 键", len(zh_keys))

    packs = {}
    for lg in LANGS[1:]:
        m = re.search(r'<script id="i18n-%s" type="application/json">(.*?)</script>' % lg, raw, re.S)
        ok = bool(m)
        data = {}
        if ok:
            try:
                data = json.loads(m.group(1))
            except Exception:
                ok = False
        packs[lg] = data
        ck.check("A2 #i18n-%s 可解析" % lg, ok, "合法 JSON", "解析失败" if not ok else "%d 键" % len(data))

    mkt = {k for k in zh_keys if not k.startswith(BI_PREFIX)}
    bi = {k for k in zh_keys if k.startswith(BI_PREFIX)}
    for lg in LANGS[1:]:
        got = set(packs.get(lg, {}))
        miss = mkt - got
        extra = got - mkt - (bi if lg == "en" else set())
        ck.check("A3 ui.%s 与 zh 键表对位（MKT %d 条）" % (lg, len(mkt)),
                 not miss and not extra, "缺 0 / 多 0", "缺 %d / 多 %d %s" % (len(miss), len(extra), sorted(miss)[:3]))
        if lg != "en":
            semi = bi & got
            ck.check("A3b ui.%s 不含工作区侧键（只做中英）" % lg, not semi, "0 条", sorted(semi)[:3])

    # ── 2. 空值 / 非法字符 ──
    bad = []
    for lg, pack in packs.items():
        for k, v in pack.items():
            if not isinstance(v, str) or not v.strip():
                bad.append("%s:%s 空值" % (lg, k))
            elif "</script" in v or "\u2028" in v or "\u2029" in v or "\x00" in v or "undefined" in v:
                bad.append("%s:%s 非法字符" % (lg, k))
    ck.check("A4 译文无空值/非法字符", not bad, "0 处", bad[:3])

    # ── 3. 教程英文包：页数、图片占位 ──
    mt = re.search(r'<script id="tut-data" type="application/json">(.*?)</script>', raw, re.S)
    base = json.loads(mt.group(1)) if mt else {}
    me = re.search(r'<script id="i18n-tut-en" type="application/json">(.*?)</script>', raw, re.S)
    tut = {}
    try:
        tut = json.loads(me.group(1)) if me else {}
    except Exception:
        tut = {}
    ck.check("A5 教程英文包可解析", bool(tut.get("pages")), "36 页", len(tut.get("pages") or {}))
    ck.check("A5b 教程页数与中文一致", len(tut.get("pages") or {}) == len(base.get("pages") or []),
             len(base.get("pages") or []), len(tut.get("pages") or {}))
    bp = {p["id"]: p for p in base.get("pages", [])}
    bm = {x["id"]: x for x in base.get("modules", [])}
    total = 0
    wrong = []
    for pid, p in (tut.get("pages") or {}).items():
        want = len(re.findall(r"<img\b", bp.get(pid, {}).get("html", "")))
        got = len(re.findall(r"\{\{img\d+\}\}", p.get("html", "")))
        total += got
        if want != got:
            wrong.append("%s: %d≠%d" % (pid, got, want))
    for mid, mm in (tut.get("mods") or {}).items():
        want = len(re.findall(r"<img\b", bm.get(mid, {}).get("overview", "")))
        got = len(re.findall(r"\{\{img\d+\}\}", mm.get("overview", "") or ""))
        total += got
        if want != got:
            wrong.append("mods.%s: %d≠%d" % (mid, got, want))
    ck.check("A6 教程图片占位逐页对齐（总数 48）", total == 48 and not wrong, "48 且逐页相等", "%d %s" % (total, wrong[:2]))

    # ── 4. 空占位/残留 ──
    ck.check("A7 英文包无未替换的 {{imgN}} 之外的占位", "{{" not in json.dumps(tut.get("home", ""), ensure_ascii=False).replace("{{img", ""), "0", "")

    # ── 5. 零外链与字体不变量 ──
    ck.check("A8 @font-face{ 恒 2", raw.count("@font-face{") == 2, 2, raw.count("@font-face{"))
    ck.check("A9 无非 data: 的 <link>", not re.findall(r'<link\b(?![^>]*href="data:)', raw), "0",
             len(re.findall(r'<link\b(?![^>]*href="data:)', raw)))
    ck.check("A10 无 <script src>", "<script src" not in raw, "0", raw.count("<script src"))
    ck.check("A11 无 url(http)", "url(http" not in raw, "0", raw.count("url(http"))
    ck.check("A12 无 <iframe>", "<iframe" not in raw, "0", raw.count("<iframe"))

    # ── 6. 数据行未被触碰（r45 A7 同口径：整行长度） ──
    sizes = {}
    for name, marker in (("tut", 'id="tut-data"'), ("dev", 'id="dev-data"')):
        hit = [ln for ln in raw.split("\n") if marker in ln and len(ln) > 100000]
        sizes[name] = len(hit[0].rstrip("\r")) if hit else -1
    ck.check("A13 两条巨型数据行未被触碰", sizes == {"tut": 21358276, "dev": 1545974},
             "tut 21358276 / dev 1545974", sizes)

    # ── 7. build_site.py 手术锚点 ──
    anchors = [
        "var DATA=null, MODS=null, ORDER=[], byId={}, modById={};",
        "var lowCache={};",
        "if(h==='/all'||h==='/tutorial'||/^\\/m\\d+(\\/|$)/.test(h)) ensureTut();",
        "  if(USER_SB!==null) return USER_SB;\r\n  ensureTut();",
        "var DEV_SB=(function(){",
        "var devCatById={}, devGrpById={}, devDocById={};",
        '<img\\b[^>]*\\bsrc="(data:image\\/[^"]+)"',
        "  ensureTut();  /* R46：搜索读 MODS/ORDER，首次输入时才解析数据 */",
    ]
    miss_a = [a for a in anchors if a not in raw]
    ck.check("A14 build_site 的 8 条手术锚点逐字在位", not miss_a, "8/8", miss_a[:2])

    # ── 8. 注释对成对 + i18next 许可头 ──
    ck.check("A15 I18N 注释对成对", raw.count("<!-- I18N:BEGIN") == 1 and raw.count("<!-- I18N:END -->") == 1,
             "1/1", (raw.count("<!-- I18N:BEGIN"), raw.count("<!-- I18N:END -->")))
    ck.check("A16 I18N-DATA 注释对成对", raw.count("<!-- I18N-DATA:BEGIN") == 1 and raw.count("<!-- I18N-DATA:END -->") == 1,
             "1/1", (raw.count("<!-- I18N-DATA:BEGIN"), raw.count("<!-- I18N-DATA:END -->")))
    ck.check("A17 i18next 版本与 MIT 许可头在位", "i18next 23.16.8" in raw and "MIT" in raw, "版本+MIT", "")

    # ── 9. RTL 层规范：零 !important、零 hex ──
    m = re.search(r"/\* ═══ R52-I18N-RTL:BEGIN.*?R52-I18N-RTL:END ═══ \*/", raw, re.S)
    rtl = m.group(0) if m else ""
    ck.check("A18 RTL 层存在", bool(rtl), "非空", len(rtl))
    rtl_body = re.sub(r"/\*.*?\*/", "", rtl, flags=re.S)  # 注释里出现「!important」是在讲规范，不算声明
    ck.check("A19 RTL 层零 !important", rtl_body.count("!important") == 0, 0, rtl_body.count("!important"))
    ck.check("A20 RTL 层零 hex 色值", not re.findall(r"#[0-9a-fA-F]{3,8}\b", rtl_body), 0, re.findall(r"#[0-9a-fA-F]{3,8}\b", rtl_body)[:3])

    # ── 10. 全部 JS 块 node 编译（不执行） ──
    blocks = re.findall(r"<script(?![^>]*type=)[^>]*>(.*?)</script>", raw, re.S)
    bad_js = []
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        for i, b in enumerate(blocks):
            fp = pathlib.Path(td) / ("b%d.js" % i)
            fp.write_text(b, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(fp)], capture_output=True, text=True)
            if r.returncode:
                bad_js.append((i, r.stderr.strip().split("\n")[-1][:100]))
    ck.check("A21 全部 %d 个 JS 块 node 编译通过" % len(blocks), not bad_js, "0 语法错", bad_js[:2])

    # ── 11. CRLF 一致性 ──
    n_lf = raw.count("\n")
    n_crlf = raw.count("\r\n")
    ck.check("A22 全文 CRLF 一致（无裸 LF）", n_lf == n_crlf, "相等", "%d/%d" % (n_lf, n_crlf))


async def runtime_checks(ck: L, skip_slow: bool):
    from playwright.async_api import async_playwright

    URL = SRC.resolve().as_uri()
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        async def new_ctx(w=1440, h=900, pin=None, locale="en-US"):
            ctx = await browser.new_context(viewport={"width": w, "height": h}, locale=locale)
            if pin:
                await ctx.add_init_script("try{window.__i18nPin='%s'}catch(e){}" % pin)
            return ctx

        errors = []

        # ── B1 zh 基线：与改造前逐字一致（抽三处硬指标） ──
        ctx = await new_ctx(pin="zh")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)[:120]))
        await pg.goto(URL + "#/", wait_until="load")
        zh = await pg.evaluate("""() => ({
          lang: document.documentElement.lang, dir: document.documentElement.getAttribute('dir'),
          slogan: (document.querySelector('.lp-slogan')||{}).textContent,
          dlBtn: (document.querySelector('#lp-dl-btn')||{}).textContent,
          title: document.title, nav: [...document.querySelectorAll('#lp-nav .lp-nav-link')].map(a=>a.textContent)
        })""")
        ck.check("B1 zh 默认：lang=zh-CN 且无 dir", zh["lang"] == "zh-CN" and zh["dir"] is None, "zh-CN / None",
                 (zh["lang"], zh["dir"]))
        ck.check("B2 zh 基线文案逐字未变", zh["slogan"] == "扫描、浏览、编辑、整理、分享，一站式完成。"
                 and zh["dlBtn"] == "资源下载" and zh["title"] == "Meow Star Map · 喵星图"
                 and zh["nav"][:3] == ["功能", "共鸣录", "隐私"], "中文原文", (zh["slogan"], zh["dlBtn"], zh["title"]))

        # ── B3 语言菜单 ──
        await pg.click("#lp-nav .lang-btn")
        menu = await pg.evaluate("""() => ({
          open: window.__i18n.isOpen(),
          opts: [...document.querySelectorAll('#lang-menu .lang-opt')].map(b=>b.getAttribute('data-lang')),
          pressed: (document.querySelector('#lang-menu .lang-opt[aria-pressed="true"]')||{}).getAttribute
                     ? document.querySelector('#lang-menu .lang-opt[aria-pressed="true"]').getAttribute('data-lang') : null,
          inViewport: (() => { const r=document.getElementById('lang-menu').getBoundingClientRect();
            return r.top>=0 && r.left>=0 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1; })()
        })""")
        ck.check("B3 语言菜单：6 项且当前项 aria-pressed", menu["open"] and menu["opts"] == LANGS and menu["pressed"] == "zh",
                 "6 项 / zh", menu)
        ck.check("B4 菜单完整落在视口内", menu["inViewport"], True, menu["inViewport"])
        await pg.keyboard.press("Escape")

        # ── B5 六语切换：营销侧文案与标题 ──
        labels = {}
        for lg in LANGS[1:]:
            await pg.evaluate("(l) => window.__i18n.set(l, true)", lg)
            got = await pg.evaluate("""() => ({
              lang: document.documentElement.lang, dir: document.documentElement.getAttribute('dir'),
              nav: [...document.querySelectorAll('#lp-nav .lp-nav-link')].map(a=>a.textContent.trim()),
              foot: (document.querySelector('.lp-footnote')||{}).textContent,
              title: document.title, slogan: (document.querySelector('.lp-slogan')||{}).textContent
            })""")
            labels[lg] = got
            want_dir = "rtl" if lg == "ar" else None
            ck.check("B5 %s：lang/dir 就位" % lg, got["lang"] == lg and got["dir"] == want_dir, (lg, want_dir), (got["lang"], got["dir"]))
            ck.check("B5b %s：导航与页脚已本地化（无中文残留）" % lg,
                     not CJK.search(" ".join(got["nav"])) and not CJK.search(got["foot"] or "") and not CJK.search(got["title"]),
                     "无 CJK", (got["nav"], got["foot"], got["title"]))
            ck.check("B5c %s：标语与 zh 不同（确实替换）" % lg, got["slogan"] != zh["slogan"], "≠ zh", got["slogan"][:40])

        # ── B6 持久化 + reload（不 pin：pin 会压过 localStorage，测不到持久化） ──
        ctx_np = await new_ctx()
        pg_np = await ctx_np.new_page()
        await pg_np.goto(URL + "#/", wait_until="load")
        await pg_np.evaluate("() => window.__i18n.set('fr', true)")
        await pg_np.reload(wait_until="load")
        keep = await pg_np.evaluate("() => ({lang: document.documentElement.lang, store: localStorage.getItem('nikki_lang')})")
        ck.check("B6 刷新后语言保持（localStorage.nikki_lang）", keep["lang"] == "fr" and keep["store"] == "fr", "fr/fr", keep)

        # ── B7 ?lang= 生效 / 非法值忽略 ──
        pg2 = await ctx_np.new_page()
        await pg2.evaluate("() => { try{localStorage.removeItem('nikki_lang')}catch(e){} }")
        await pg2.goto(URL + "?lang=ru#/privacy", wait_until="load")
        ru = await pg2.evaluate("() => ({lang: document.documentElement.lang, h1: (document.querySelector('.pg-title')||{}).textContent})")
        ck.check("B7 ?lang=ru 生效且隐私页为俄语", ru["lang"] == "ru" and not CJK.search(ru["h1"] or ""), "ru", ru)
        await pg2.goto(URL + "?lang=xx#/", wait_until="load")
        xx = await pg2.evaluate("() => ({lang: document.documentElement.lang, store: localStorage.getItem('nikki_lang')})")
        ck.check("B8 非法 ?lang=xx 被忽略（不写存储）", xx["store"] != "xx" and xx["lang"] in LANGS, "回落合法语种", xx)
        await pg2.close()

        # ── B9 阿拉伯语 RTL 几何 ──
        ctx3 = await new_ctx(pin="ar")
        pg3 = await ctx3.new_page()
        pg3.on("pageerror", lambda e: errors.append(str(e)[:120]))
        await pg3.goto(URL + "#/m1/m1p4", wait_until="load")
        await pg3.wait_for_timeout(250)
        rtl = await pg3.evaluate("""() => {
          const sb=getComputedStyle(document.getElementById('sidebar'));
          const app=getComputedStyle(document.getElementById('app'));
          const a=document.querySelector('#sidebar .sb-pages a');
          const pre=document.createElement('pre'); document.body.appendChild(pre);
          const preDir=getComputedStyle(pre).direction; pre.remove();
          const rect=document.getElementById('sidebar').getBoundingClientRect();
          return {dir: document.documentElement.dir, sbLeft: sb.left, sbRight: sb.right,
                  sbEdge: Math.round(rect.right), vw: innerWidth,
                  appPadRight: app.paddingRight, pagePadRight: a?getComputedStyle(a).paddingRight:null,
                  preDir, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth};
        }""")
        ck.check("B9 ar：侧栏镜像到右侧", rtl["dir"] == "rtl" and rtl["sbRight"] == "0px"
                 and rtl["sbEdge"] == rtl["vw"] and rtl["sbLeft"] != "0px",
                 "rtl / right:0 / 右缘贴视口", (rtl["dir"], rtl["sbRight"], rtl["sbEdge"], rtl["vw"]))
        ck.check("B10 ar：正文让位右侧 306px、侧栏缩进 32px", rtl["appPadRight"] == "306px" and rtl["pagePadRight"] == "32px",
                 ("306px", "32px"), (rtl["appPadRight"], rtl["pagePadRight"]))
        ck.check("B11 ar：代码块仍 LTR", rtl["preDir"] == "ltr", "ltr", rtl["preDir"])
        ck.check("B12 ar：文档零横向溢出", rtl["overflow"] <= 1, "<=1", rtl["overflow"])

        # ── B13 教程：英文包生效 + 图片数量 + 无占位残留 ──
        ctx4 = await new_ctx(pin="en")
        pg4 = await ctx4.new_page()
        pg4.on("pageerror", lambda e: errors.append(str(e)[:120]))
        await pg4.goto(URL + "#/m1/m1p3", wait_until="load")
        await pg4.wait_for_timeout(300)
        tp = await pg4.evaluate("""() => ({
          h1: (document.querySelector('h1.page-title')||{}).textContent,
          imgs: document.querySelectorAll('.page-body img').length,
          token: document.body.innerText.includes('{{img'),
          cjk: /[\\u4e00-\\u9fff]/.test((document.querySelector('.wrap')||document.body).innerText),
          side: [...document.querySelectorAll('#sidebar a')].slice(2,3).map(a=>a.textContent.trim())
        })""")
        ck.check("B13 en：教程页为英文且模块名同步", not tp["cjk"] and tp["h1"] == "Getting to know the main window"
                 and not CJK.search(tp["side"][0] if tp["side"] else ""), "English", (tp["h1"], tp["side"]))
        ck.check("B14 en：图片注入正常、无占位残留", tp["imgs"] == 1 and not tp["token"], "1 张 / 无 {{img", (tp["imgs"], tp["token"]))

        # ── B15 教程首页英文封面墙（buildHomeGrid 结构约束） ──
        await pg4.goto(URL + "#/tutorial", wait_until="load")
        await pg4.wait_for_timeout(400)
        home = await pg4.evaluate("""() => ({
          cards: document.querySelectorAll('.cover-grid > *').length,
          names: [...document.querySelectorAll('.ms-name')].map(x=>x.textContent.trim()),
          cjk: /[\\u4e00-\\u9fff]/.test((document.querySelector('.wrap-home')||document.body).innerText)
        })""")
        ck.check("B15 en：教程首页 9 卡且全英文", home["cards"] == 9 and not home["cjk"], "9 卡 / 无 CJK", (home["cards"], home["names"][:3]))

        # ── B16 非中英语种下工作区回落英文 + 通告 ──
        await pg4.evaluate("() => window.__i18n.set('ar', true)")
        await pg4.goto(URL + "#/identity", wait_until="load")
        await pg4.wait_for_timeout(250)
        gate = await pg4.evaluate("""() => ({
          sub: (document.querySelector('.gate-sub')||{}).textContent,
          notice: (document.querySelector('.i18n-bi')||{}).textContent,
          cjk: /[\\u4e00-\\u9fff]/.test(document.querySelector('.gate').innerText)
        })""")
        ck.check("B16 ar：身份门回落英文且带双语通告",
                 gate["sub"] == "Pick your role to enter the matching workspace" and bool(gate["notice"]) and not gate["cjk"],
                 "English + notice", gate)

        # ── B17 R41 卡片详情在译后仍可展开（h3 键解耦回归） ──
        await pg4.evaluate("() => window.__i18n.set('en', true)")
        await pg4.goto(URL + "#/", wait_until="load")
        await pg4.wait_for_timeout(250)
        await pg4.click('.lpx-card[data-dt="scan"] .lpx-card-cue')
        await pg4.wait_for_timeout(350)
        det = await pg4.evaluate("""() => {
          const p=document.querySelector('.lpx-detpanel');
          return p ? {n: p.querySelectorAll('li').length, first: p.querySelector('li').textContent} : null;
        }""")
        ck.check("B17 en：卡片详情仍可展开且要点已翻译", bool(det) and det["n"] == 2 and "Scan" in det["first"],
                 "2 条英文要点", det)

        # ── B18 幂等：连续 apply 不叠加 ──
        await pg4.goto(URL + "#/features", wait_until="load")
        await pg4.wait_for_timeout(200)
        a = await pg4.evaluate("() => { window.__i18n.apply(); const n=document.body.innerText.length; window.__i18n.apply(); window.__i18n.apply(); return [n, document.body.innerText.length]; }")
        ck.check("B18 重复 apply 幂等（文本长度不变）", a[0] == a[1], "相等", a)

        # ── B19 六语 × 四断点：零横向溢出 ──
        if skip_slow:
            ck.skip("B19 六语 × 四断点零横向溢出", "--skip-slow")
        else:
            bad = []
            ctx5 = await new_ctx()
            pg5 = await ctx5.new_page()
            for w in (390, 768, 900, 1440):
                await pg5.set_viewport_size({"width": w, "height": 800})
                await pg5.goto(URL + "#/", wait_until="load")   # 每个断点只加载一次，切语靠 set() 重渲
                for lg in LANGS:
                    await pg5.evaluate("(l) => window.__i18n.set(l, true)", lg)
                    d = await pg5.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    if d > 1:
                        bad.append((w, lg, d))
            ck.check("B19 六语 × 四断点零横向溢出", not bad, "全部 <=1", bad[:4])
            await ctx5.close()

        # ── B20 console / pageerror 双零 ──
        ctx6 = await new_ctx()
        pg6 = await ctx6.new_page()
        msgs = []
        pg6.on("console", lambda m: msgs.append((m.type, m.text[:80])))
        pg6.on("pageerror", lambda e: msgs.append(("pageerror", str(e)[:120])))
        for lg in LANGS:
            for route in ("#/", "#/features", "#/tutorial", "#/m1/m1p1", "#/dev"):
                await pg6.goto(URL + route, wait_until="load")
                await pg6.evaluate("(l) => window.__i18n.set(l, true)", lg)
                await pg6.wait_for_timeout(60)
        ck.check("B20 六语 × 五路由 console/pageerror 双零", not msgs, "0 条", msgs[:4])

        await browser.close()
    ck.check("B21 全流程无未捕获异常", not errors, "0 条", errors[:3])


def main():
    raw = SRC.read_text(encoding="utf-8", newline="")
    ck = L()
    src_checks(ck, raw)
    import asyncio

    slow = "--skip-slow" in sys.argv
    asyncio.run(runtime_checks(ck, slow))
    return ck.report()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
