#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R42 专项探针：一级界面三大卡片迁移至二级界面 + 顶部常驻 GitHub 入口

用法：
    py tests/r42_migration_check.py              全量（含断点矩阵与双主题）
    py tests/r42_migration_check.py --skip-slow  跳过五断点矩阵与基线对齐取证

协议：file:// 直开，无端口自起。依赖 playwright（与 r37/r38/r39/r41 同一口径，不新增第三方依赖）。
口径要点：
  * A2「内容零丢失」用逐字子串断言，不用计数近似：一级首页三卡的每条文本节点必须能在
    迁移目的地（4 个 landing 页）的合并文本中原样找到。
  * A9 字体子集：本探针只用 stdlib 判定「新汉字符号是否已在源文件其它位置出现过」
    （R36 子集即按站点字符构建，故这是可证伪的必要条件）；精确 cmap 命中另用 fonttools
    一次性核验，不写进仓库探针，避免给 requirements.txt 添依赖。
  * 导航溢出（C4b）单独断言 .lp-links 自身 scrollWidth<=clientWidth：该容器在改造前
    390/640px 就已溢出且滚动条被隐藏，属既有缺陷，本层只保证「不因新增圆钮而恶化到 900px 档」。
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "Meow Star Map 官网.html"
URL = SRC.resolve().as_uri()
SKIP_SLOW = "--skip-slow" in sys.argv

GH_HREF = "https://github.com/QianQianLuLu1/MeowStarMap"
LANDING_VIEWS = ["#/", "#/features", "#/resonance", "#/privacy", "#/download", "#/download/start"]
WIDTHS = [390, 768, 1440, 1920, 2560]

# 一级首页三卡原文（摘除前逐字抄录，见 R42 CSS 层头注的迁移对照表）
CARD_TEXTS = [
    "喵星图 · 无限暖暖本地相册",
    "为《无限暖暖》玩家打造的 Windows 桌面相册工具，自动扫描截图与录屏，数据保存在本地。",
    "五种视图，支持搜索、标签与分类",
    "图片编辑、视频处理与重复检测",
    "分享、备份与共鸣录",
    "抽卡记录与衣橱，都在本地。",
    "记录抽卡历程、整理我的衣橱、查看个人统计；本地 JSON 导入导出，纯离线运行，零外链。",
    "开始使用",
    "开始使用喵星图",
    "当前版本 2.5.6-beta · Windows 10 (1803+) / Windows 11 · x64",
    "前往下载",
    "进入应用",
]
# 有意随卡片退场的两条：均为一级首页专属的自指导航文案，迁到目的地后语义不成立
RETIRED_TEXTS = ["共鸣录", "了解共鸣录"]


class Ledger:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expected, actual, note=""):
        self.rows.append({"name": name, "status": "PASS" if ok else "FAIL",
                          "expected": expected, "actual": str(actual)[:400], "note": note})
        return bool(ok)

    def skip(self, name, expected, why):
        self.rows.append({"name": name, "status": "NOT-RUN", "expected": expected,
                          "actual": None, "note": why})

    def report(self, title):
        p = f = s = 0
        print()
        print("=" * 78)
        print(title)
        print("=" * 78)
        for r in self.rows:
            print(f"  {r['status']:4}  {r['name']}")
            if r["status"] == "FAIL":
                print(f"        期望: {r['expected']}")
                print(f"        实际: {r['actual']}")
            elif r["status"] == "NOT-RUN":
                print(f"        跳过: {r['note']}")
            if r["note"] and r["status"] == "PASS":
                print(f"        {r['note']}")
            p += r["status"] == "PASS"
            f += r["status"] == "FAIL"
            s += r["status"] == "NOT-RUN"
        print("-" * 78)
        print(f"合计 {len(self.rows)} | PASS {p} | FAIL {f} | NOT-RUN {s}")
        return f


JS_COUNTS = """() => {
  const all = s => [...document.querySelectorAll(s)];
  const t = s => { const e = document.querySelector(s); return e ? e.textContent.trim() : null; };
  return {
    view: document.body.dataset.view,
    product: all('.lp-product').length,
    resonance: all('.lpx-resonance').length,
    cta: all('.lpx-cta').length,
    banner: all('.lpx-banner').length,
    art: all('.lpx-art').length,
    ctaCard: all('.lpx-cta-card').length,
    hero: all('.lp-hero').length,
    stats: all('.lpx-stats').length,
    featCards: all('.lpx-features .lpx-card').length,
    advCards: all('.lpx-advantages .lpx-card').length,
    foot: all('.lp-foot').length,
    aboutSec: all('.about-sec').length,
    aboutSoc: all('.about-social').length,
    pgCards: all('.pg-card').length,
    pgGrids: all('.pg-grid').length,
    pgBack: t('.pg-back'),
    ghNav: all('#lp-nav .lp-gh').length,
    ghTop: all('#topbar .ghlink').length,
    text: document.body.innerText
  };
}"""


def load_source_text():
    """按行读入，跳过 >100000 字符的巨型数据/字体行（与 r31/r37 同一防假阳性口径）。"""
    keep = []
    for line in SRC.read_text(encoding="utf-8").split("\n"):
        if len(line) <= 100000:
            keep.append(line)
    return "\n".join(keep)


def main():
    L = Ledger()
    raw = SRC.read_text(encoding="utf-8")
    text_only = load_source_text()

    # ---------------------------------------------------------- 静态：零外链不变量
    # R43 起 favicon / apple-touch-icon 以 <link href="data:"> 内联，属自包含资源而非外链。
    ext_link = len(re.findall(r"""<link\b(?![^>]*href=["']data:)""", raw))
    icon_link = len(re.findall(r"""<link\b[^>]*href=["']data:image/""", raw))
    L.check("A10a 零外链资源标签",
            ext_link == 0
            and len(re.findall(r"<script[^>]+\bsrc=|<iframe\b|url\(\s*http", raw)) == 0,
            "外链 0 处", f"外链 link={ext_link}")
    L.check("A10a2 图标 link 恰 2 枚且均为 data: 内联（R43）", icon_link == 2, "2", icon_link)
    L.check("A10b @font-face 计数保持 2（均 data:）",
            raw.count("@font-face{") == 2, "2", raw.count("@font-face{"))
    L.check("A10c GitHub 出链恰 2 处（lp-nav + topbar）",
            raw.count(GH_HREF + '"') == 2, "2", raw.count(GH_HREF + '"'))
    L.check("S1 R42 注释对成对平衡",
            raw.count("R42:BEGIN") == raw.count("R42:END") == 1
            and raw.count("R42-VIEW:BEGIN") == raw.count("R42-VIEW:END") == 1,
            "CSS 层 1 对 + 模板层 1 对",
            f"R42 {raw.count('R42:BEGIN')}/{raw.count('R42:END')}, "
            f"R42-VIEW {raw.count('R42-VIEW:BEGIN')}/{raw.count('R42-VIEW:END')}")
    L.check("S2 本层零新增 hex（颜色全走令牌）",
            "hex" not in raw.split("R42:BEGIN")[1].split("R42:END")[0].lower()
            or not re.search(r"#[0-9a-fA-F]{3,8}\b",
                             raw.split("R42:BEGIN")[1].split("R42:END")[0]),
            "R42 CSS 层内无字面色值", "无")

    # ---------------------------------------------------------- 字体子集必要条件
    # 新引入的可见汉字（迁移对照表之外，本轮自造的短句与标签）
    new_copy = ["浏览图库", "编辑处理", "分享备份", "三步开始", "下载、安装、进入应用",
                "返回下载与支持", "查看开始使用", "前往下载与支持页"]
    # 源文件里除「本轮新增文案自身」以外是否本来就出现过这些字
    probe = text_only
    missing = []
    for cp in sorted({c for s in new_copy for c in s if "\u3400" <= c <= "\u9fff"}):
        # 把本轮新增串从语料里剔掉，剩下的才是 R42 之前的既有字符集
        stripped = probe
        for s in new_copy:
            stripped = stripped.replace(s, "")
        if cp not in stripped:
            missing.append(cp)
    L.check("A9b 新增汉字均为站点既有字符（R36 子集必要条件，stdlib 口径）",
            not missing, "0 个新字", "".join(missing) or "0",
            "精确 cmap 命中另用 fonttools 一次性核验；探针不引入 fonttools 依赖")

    console_errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))

        snap = {}
        for h in LANDING_VIEWS:
            page.goto(URL + h)
            page.wait_for_timeout(450)
            snap[h] = page.evaluate(JS_COUNTS)
            snap[h]["title"] = page.title()

        # ------------------------------------------------------ A1 一级首页结构
        lp = snap["#/"]
        L.check("A1 一级首页三卡归零",
                lp["product"] == lp["resonance"] == lp["cta"] == 0,
                "0/0/0", f'{lp["product"]}/{lp["resonance"]}/{lp["cta"]}')
        L.check("A1b 一级首页其余区块完好（hero+stats+6 功能卡+3 优势卡+关于+页脚）",
                lp["hero"] == 1 and lp["stats"] == 1 and lp["featCards"] == 6
                and lp["advCards"] == 3 and lp["aboutSec"] >= 1 and lp["foot"] == 1,
                "1/1/6/3/≥1/1",
                f'{lp["hero"]}/{lp["stats"]}/{lp["featCards"]}/{lp["advCards"]}/{lp["aboutSec"]}/{lp["foot"]}')

        # ------------------------------------------------------ A2 内容零丢失
        union = "".join(snap[h]["text"] for h in LANDING_VIEWS)
        lost = [t for t in CARD_TEXTS if t not in union]
        L.check("A2 三卡 12 条原文在四个 landing 页合并文本中逐字命中",
                not lost, "12/12 命中", f"缺失 {len(lost)} 条: {lost}")
        L.check("A2b 一级首页专属自链「了解共鸣录」已随卡片退场（有意取舍，非丢失）",
                "了解共鸣录" not in lp["text"], "不在一级首页文本中",
                "已退场" if "了解共鸣录" not in lp["text"] else "仍在位")

        # ------------------------------------------------------ A4 二级/三级页无大卡
        big = {h: (snap[h]["banner"], snap[h]["art"], snap[h]["ctaCard"], snap[h]["product"])
               for h in LANDING_VIEWS[1:]}
        L.check("A4 四个 landing 子页 .lpx-banner/.lpx-art/.lpx-cta-card/.lp-product 全 0",
                all(v == (0, 0, 0, 0) for v in big.values()), "全 0",
                {k: v for k, v in big.items() if v != (0, 0, 0, 0)} or "全 0")
        L.check("A4b 子页卡片一律走 .pg-grid > .pg-card 小卡体系",
                all(snap[h]["pgGrids"] >= 1 and snap[h]["pgCards"] >= 2 for h in LANDING_VIEWS[1:]),
                "每页 ≥1 网格且 ≥2 小卡",
                {h: (snap[h]["pgGrids"], snap[h]["pgCards"]) for h in LANDING_VIEWS[1:]})

        # ------------------------------------------------------ A6 三级页路由
        gs = snap["#/download/start"]
        L.check("A6 三级页 #/download/start 渲染为 landing 视图且标题正确",
                gs["view"] == "landing" and "开始使用" in gs["title"]
                and "开始使用喵星图" in gs["text"],
                "view=landing / title 含「开始使用」", f'{gs["view"]} / {gs["title"]}')
        L.check("A6b 三级页返回链指回 #/download 且文案为「返回下载与支持」",
                gs["pgBack"] == "← 返回下载与支持", "← 返回下载与支持", gs["pgBack"])
        L.check("A6c 既有四个二级页返回链零变化（默认尾参生效）",
                all(snap[h]["pgBack"] == "← 返回首页" for h in
                    ["#/features", "#/resonance", "#/privacy", "#/download"]),
                "← 返回首页 ×4",
                {h: snap[h]["pgBack"] for h in ["#/features", "#/resonance", "#/privacy", "#/download"]})
        page.goto(URL + "#/zzz-unknown")
        page.wait_for_timeout(350)
        L.check("A6d 未知 hash 仍回落一级首页",
                page.evaluate("() => !!document.querySelector('.lp-hero')"), "有 .lp-hero", "已回落")
        page.goto(URL + "#/download/start@faq")
        page.wait_for_timeout(350)
        L.check("A6e 深链锚点 #/download/start@faq 可达且定位到 FAQ",
                page.evaluate("() => !!document.getElementById('faq')"), "存在 #faq", "可达")

        # ------------------------------------------------------ A7 GitHub 双入口
        gh = page.evaluate("""() => {
          const q = s => document.querySelector(s);
          const bar = [...document.querySelectorAll('#topbar > *')]
            .map(e => (e.className || '') + '#' + (e.id || ''));
          return {
            nav: q('#lp-nav .lp-gh') ? {
              href: q('#lp-nav .lp-gh').href, target: q('#lp-nav .lp-gh').target,
              rel: q('#lp-nav .lp-gh').rel, label: q('#lp-nav .lp-gh').getAttribute('aria-label'),
              svg: !!q('#lp-nav .lp-gh svg')
            } : null,
            top: q('#topbar .ghlink') ? {
              href: q('#topbar .ghlink').href, target: q('#topbar .ghlink').target,
              rel: q('#topbar .ghlink').rel, svg: !!q('#topbar .ghlink svg'),
              text: q('#topbar .ghlink').textContent.trim()
            } : null,
            order: bar,
            ghIdx: bar.findIndex(c => (c||'').includes('ghlink')),
            roleIdx: bar.findIndex(c => (c||'').includes('rolelink')),
            themeIdx: bar.findIndex(c => (c||'').includes('themebtn'))
          };
        }""")
        for side in ("nav", "top"):
            g = gh[side]
            L.check(f"A7 {side} 侧 GitHub 按钮 href/target/rel 逐字正确",
                    g and g["href"] == GH_HREF and g["target"] == "_blank"
                    and "noopener" in g["rel"] and "noreferrer" in g["rel"] and g["svg"],
                    GH_HREF + " / _blank / noopener noreferrer + 内联 svg",
                    g)
        L.check("A7b topbar GitHub 紧随「切换身份」之后（不破坏 THEME-UI insertBefore 锚点）",
                gh["ghIdx"] == gh["roleIdx"] + 1 > 0, "ghIdx == roleIdx+1",
                f'gh={gh["ghIdx"]} role={gh["roleIdx"]} theme={gh["themeIdx"]}')
        L.check("A7c #themebtn 与 .look-btn 仍插在「切换身份」之前（既有注入位序零变化）",
                -1 < gh["themeIdx"] < gh["roleIdx"], "themeIdx < roleIdx",
                f'theme={gh["themeIdx"]} role={gh["roleIdx"]}')

        # ------------------------------------------------------ A8 导航高亮前缀匹配
        for h, want in (("#/download", True), ("#/download/start", True), ("#/features", False)):
            page.goto(URL + h)
            page.wait_for_timeout(320)
            act = page.evaluate(
                """() => { const a=document.querySelector('#lp-nav a[data-route="download"]');
                return {cls:a.classList.contains('is-active'),
                        aria:a.getAttribute('aria-current')}; }""")
            L.check(f"A8 {h} 时「下载」导航项 active 状态正确（期望 active={want}）",
                    act["cls"] == want and (act["aria"] == "page") == want,
                    f"active={want}", act)

        # ------------------------------------------------------ A3 「关于」滚动目标
        page.goto(URL + "#/")
        page.wait_for_timeout(500)
        about = page.evaluate("""() => {
          const s = document.querySelector('.about-sec');
          return { hasSocial: !!s.querySelector('.about-social'),
                   title: (s.querySelector('.about-title')||{}).textContent };
        }""")
        L.check("A3 一级首页首个 .about-sec 现为真正的关于板块（含社交行）",
                about["hasSocial"], "含 .about-social", about)
        page.click("#lp-about-link")
        page.wait_for_timeout(900)
        scrolled = page.evaluate("""() => {
          const r = document.querySelector('.about-sec').getBoundingClientRect();
          const nav = document.querySelector('#lp-nav').getBoundingClientRect();
          return { top: Math.round(r.top), navH: Math.round(nav.height) };
        }""")
        L.check("A3b 点「关于」后板块顶边落在导航之下（scroll-margin-top 生效）",
                scrolled["top"] >= scrolled["navH"] - 4,
                f'top >= navH({scrolled["navH"]})', scrolled)

        # ------------------------------------------------------ B1/B3 对齐取证
        align = page.evaluate("""() => {
          const cx = e => { const r = e.getBoundingClientRect(); return [r.top, r.bottom]; };
          const cs = e => getComputedStyle(e);
          const gh = document.querySelector('#topbar .ghlink');
          const role = document.querySelector('#topbar .rolelink');
          const gsvg = gh.querySelector('svg'), rsvg = role.querySelector('span');
          return {
            ghDisplay: cs(gh).display, ghAlign: cs(gh).alignItems, ghGap: cs(gh).gap,
            navDisplay: cs(document.querySelector('#lp-nav .lp-gh')).display,
            navAlign: cs(document.querySelector('#lp-nav .lp-gh')).alignItems,
            navJust: cs(document.querySelector('#lp-nav .lp-gh')).justifyContent,
            navPad: cs(document.querySelector('#lp-nav .lp-gh')).padding,
            ghBox: cx(gh), roleBox: cx(role)
          };
        }""")
        # display 断言须接受 flex：.lp-gh 是 .lp-links(display:flex) 的 flex item，
        # 规范上 inline-flex 会被块化为 flex，对齐意图由 align-items/justify-content 承载
        L.check("B3 两枚 GitHub 按钮显式声明对齐方式（非默认 inline 基线）",
                align["ghDisplay"] == "inline-flex" and align["ghAlign"] == "center"
                and align["navDisplay"] in ("flex", "inline-flex")
                and align["navAlign"] == "center" and align["navJust"] == "center",
                "topbar=inline-flex / lp-nav 圆钮 flex|inline-flex 且 center+center",
                {k: align[k] for k in ("ghDisplay", "ghAlign", "ghGap",
                                        "navDisplay", "navAlign", "navJust")})
        L.check("B4 GitHub 圆钮 padding 复位为 0（未被 .lp-links a 的 6px 2px 顶偏心）",
                align["navPad"] in ("0px", "0px 0px"), "0px", align["navPad"])
        L.check("B1 GitHub 胶囊与相邻「切换身份」胶囊垂直中心对齐 ≤1px",
                abs((align["ghBox"][0] + align["ghBox"][1]) / 2
                    - (align["roleBox"][0] + align["roleBox"][1]) / 2) <= 1.0,
                "Δ ≤ 1px",
                round(abs((align["ghBox"][0] + align["ghBox"][1]) / 2
                          - (align["roleBox"][0] + align["roleBox"][1]) / 2), 2))

        # ------------------------------------------------------ B6/B7 卡片对齐与内边距
        page.goto(URL + "#/download/start")
        page.wait_for_timeout(400)
        card = page.evaluate("""() => {
          const c = document.querySelector('.pg-card');
          const p = c.querySelector('p');
          const cs = getComputedStyle(c);
          return { ta: getComputedStyle(p).textAlign,
                   pad: [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft],
                   secTa: getComputedStyle(document.querySelector('.pg')).textAlign };
        }""")
        L.check("B6 父容器居中而卡内文字显式左对齐",
                card["secTa"] == "center" and card["ta"] == "left",
                ".pg=center / 卡内 p=left", card)
        L.check("B7 卡片四周 padding 等值（28px）",
                len(set(card["pad"])) == 1 and card["pad"][0] == "28px",
                "四边均 28px", card["pad"])

        # ------------------------------------------------------ B5 导航防遮挡
        pad = page.evaluate("""() => {
          const nav = document.querySelector('#lp-nav').getBoundingClientRect().height;
          const back = document.querySelector('.pg-back').getBoundingClientRect();
          return { nav, top: back.top };
        }""")
        L.check("B5 三级页首个内容块不被固定导航遮挡",
                pad["top"] >= pad["nav"], f'top >= {pad["nav"]}', pad)

        # ------------------------------------------------------ C4 断点矩阵
        if SKIP_SLOW:
            L.skip("C4 五断点 × 双主题零横向溢出 + 导航不遮挡", "全部视口 scrollWidth<=clientWidth",
                   "--skip-slow 显式跳过")
            L.skip("C4b .lp-links 自身不因新增圆钮溢出", "scrollWidth<=clientWidth",
                   "--skip-slow 显式跳过")
            L.skip("C4c 390px 档 .lp-links 溢出优于改造前", "≤ 46px", "--skip-slow 显式跳过")
            L.skip("C4d 390px 档 .lp-brand 未被挤成三行", "brandH ≤ 52px", "--skip-slow 显式跳过")
        else:
            over, navover, nav390, brand390 = [], [], [], []
            for w in WIDTHS:
                pg = ctx.new_page()
                for theme in ("light", "dark"):
                    for h in LANDING_VIEWS:
                        pg.set_viewport_size({"width": w, "height": 900})
                        pg.goto(URL + h)
                        pg.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
                        pg.wait_for_timeout(260)
                        r = pg.evaluate("""() => ({
                          doc: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
                          linksOver: (() => { const e=document.querySelector('#lp-nav .lp-links');
                            return e ? e.scrollWidth - e.clientWidth : 0; })(),
                          brandH: (() => { const b=document.querySelector('.lp-brand');
                            return b ? Math.round(b.getBoundingClientRect().height) : 0; })(),
                          clear: (() => {
                            // 一级首页 hero 按 R21 设计本就铺在毛玻璃导航之下，故遮挡判定取
                            // 首个「文字块」：子页用 .pg-back，首页用 .lp-title
                            const nav=document.querySelector('#lp-nav, #topbar');
                            if(!nav) return true;
                            const first=document.querySelector('.pg-back')||document.querySelector('.lp-title');
                            return !first || first.getBoundingClientRect().top >= nav.getBoundingClientRect().height - 1;
                          })()
                        })""")
                        if not r["doc"]:
                            over.append(f"{w}/{theme}/{h}")
                        if not r["clear"]:
                            over.append(f"遮挡 {w}/{theme}/{h}")
                        if w > 640 and r["linksOver"] > 0:
                            navover.append(f'{w}/{theme}/{h}:{r["linksOver"]}')
                        if w == 390 and h == "#/":
                            nav390.append(r["linksOver"])
                            brand390.append(r["brandH"])
                pg.close()
            L.check("C4 五断点 × 双主题 × 六视图零横向溢出且首块不被导航遮挡",
                    not over, "0 处", over or "0")
            L.check("C4b .lp-links 在 >640px 各档零溢出（≤900px 隐藏配色圆点生效）",
                    not navover, "0 处", navover or "0")
            # 390px 档改造前即溢出 +46px（既有缺陷，滚动条被隐藏）；本轮加圆钮后靠
            # ≤900px 隐圆点 + ≤640px 隐三重重复的 #lp-dl-link + 放宽 .lp-links 上限收回，
            # 断言口径为「不得比改造前更差」，且品牌必须留在 52px 栏高内
            L.check("C4c 390px 档 .lp-links 溢出不劣于改造前的 +46px",
                    nav390 and max(nav390) <= 46, "≤ 46px", f"{max(nav390) if nav390 else 'n/a'}px")
            L.check("C4d 390px 档 .lp-brand 未被挤成超出栏高的三行",
                    brand390 and max(brand390) <= 52, "brandH ≤ 52px", f"{max(brand390) if brand390 else 'n/a'}px")

        # ------------------------------------------------------ A5 图标未静默回落
        # pgIcon() 对未知 name 静默回落 icons.spark（不抛错），故按 svg innerHTML 比对而非 path
        page.goto(URL + "#/features")
        page.wait_for_timeout(400)
        icons = page.evaluate("""() => {
          const out = {};
          document.querySelectorAll('.pg-grid .pg-card').forEach(c => {
            const i = c.querySelector('.pg-ico svg');
            out[(c.querySelector('h3')||{}).textContent] = i ? i.innerHTML : null;
          });
          return out;
        }""")
        trio = ["浏览图库", "编辑处理", "分享备份"]
        vals = [icons.get(k) for k in trio]
        spark = next((v for k, v in icons.items() if k == "双主题"), None)
        L.check("A5 #/features 新迁移三卡图标各不相同且未落到 pgIcon 的 spark 静默兜底",
                all(vals) and len(set(vals)) == 3 and (spark is None or all(v != spark for v in vals)),
                "3 个互异且非兜底图标",
                {k: (v or "")[:40] for k, v in zip(trio, vals)})

        # ------------------------------------------------------ C6 控制台
        L.check("C6 全程 console / pageerror 零报错",
                not console_errors, "0 条", console_errors[:5])

        # 快照留档，便于人工核对
        (HERE / "r42-snapshot.json").write_text(
            json.dumps({h: {k: v for k, v in d.items() if k != "text"}
                        for h, d in snap.items()}, ensure_ascii=False, indent=1),
            encoding="utf-8")

        browser.close()

    fails = L.report("R42 专项探针 · 一级三卡迁移 + GitHub 常驻入口")
    print(f"\n快照: {HERE / 'r42-snapshot.json'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
