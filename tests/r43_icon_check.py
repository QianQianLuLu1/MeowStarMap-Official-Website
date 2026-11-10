#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R43 专项探针：软件图标层（单点 data: 母图 + 1em 自适应占位 + 两枚内联图标 link）

用法：
    py tests/r43_icon_check.py              全量（源码级 + 六槽位几何 + 溢出矩阵 + 禁 JS）
    py tests/r43_icon_check.py --skip-slow  跳过四断点 × 双主题 × 三态溢出矩阵

协议：file:// 直开，无端口自起。依赖 playwright（与 r37/r38/r39/r41/r42 同一口径，不新增第三方依赖）。

口径要点：
  * 「尺寸·比例·显示位置不变」的可证伪判据 = `.app-ic` 的实测宽高既相等、又等于该元素自身
    计算字号（CSS 写的是 width/height:1em），即占位与改造前的 emoji 字形同源同值。
  * 瓦片宿主（.q-emoji / .gate-emoji）的圆角·底色·描边须逐项与改造前一致：R43 用
    background-image 长写，故简写 background 设定的底色不得被抹掉。
  * 溢出矩阵不重载页面（34MB 原件每次解析约 2s）：改 data-theme / data-look 属性与
    viewport 即可驱动全部 CSS 级联，与 R38 三态菜单实际写入的属性完全同构。
  * 零外链口径（R43 修订）：link 标记只计 href 非 data: 者；同时正向断言图标 link 恰 2 枚。
"""
import base64
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

try:  # Windows 控制台默认 GBK，中文报告需强制 UTF-8（与 r37/r38/r39 同口径）
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "Meow Star Map 官网.html"
URL = SRC.resolve().as_uri()
SKIP_SLOW = "--skip-slow" in sys.argv

GLYPH = "\U0001F4F7"
# 六处槽位：(标签, 视图 hash, 命中选择器, 运行时可达性说明)。
# 侧栏 DEV_SB / 快捷卡 devHome() / dev-actions renderDev() 三支均在开发者工作台视图渲染，
# 且 DEV_SB 需 DEV 数据解析成功（非用户教程视图），故三处一律走 #/dev。
# .dev-actions 那一处位于 renderDev 的 `if(!DEV)` 兜底分支内：本构建 dev-data 恒在位，
# 该分支运行时不可达，故只做源码级断言（见 A12），运行时项记 NOT-RUN 而非静默通过。
SLOTS = [
    ("一级导航 .lp-brand-mark", "#/", "#lp-nav .lp-brand-mark.app-ic", None),
    ("顶栏 Logo .lg-emoji", "#/tutorial", "#topbar .logo .lg-emoji.app-ic", None),
    ("侧栏 .sb-all 内嵌", "#/dev", "#sidebar .sb-all .app-ic", None),
    ("快捷卡 .q-emoji 瓦片内", "#/dev", ".quick .q-emoji .app-ic", None),
    ("开发者工作台 .alllink 内嵌", "#/dev", ".dev-actions .alllink .app-ic",
     "renderDev 的 !DEV 兜底分支，本构建 dev-data 在位故不渲染；由 A12 源码级覆盖"),
    ("身份门 .gate-emoji 瓦片内", "#/identity", ".gate .gate-emoji .app-ic", None),
]
# 六处槽位在源码中的最终形态（逐字，用于 A12 精确计数）
SLOT_MARKUP = [
    '<span class="lp-brand-mark app-ic" aria-hidden="true"></span>',
    '<span class="lg-emoji app-ic" aria-hidden="true"></span>',
    '<a class="sb-all" href="#/tutorial"><span class="app-ic" aria-hidden="true"></span>用户使用教程</a>',
    '<span class="q-emoji"><span class="app-ic" aria-hidden="true"></span></span>',
    '<a class="alllink" href="#/tutorial"><span class="app-ic" aria-hidden="true"></span> 查看用户使用教程</a>',
    '<div class="gate-emoji"><span class="app-ic" aria-hidden="true"></span></div>',
]
WIDTHS = [390, 768, 1440, 1920]
VIEWS_MATRIX = ["#/", "#/identity", "#/tutorial", "#/dev"]


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
            elif r["note"]:
                print(f"        {r['note']}")
            p += r["status"] == "PASS"
            f += r["status"] == "FAIL"
            s += r["status"] == "NOT-RUN"
        print("-" * 78)
        print(f"合计 {len(self.rows)} | PASS {p} | FAIL {f} | NOT-RUN {s}")
        return f


def source_checks(L):
    raw = SRC.read_text(encoding="utf-8", errors="replace")

    L.check("A1 旧软件图标字形 📷 已全部替换", raw.count(GLYPH) == 0,
            "0 处", f"{raw.count(GLYPH)} 处")
    L.check("A2 全文件 <link> 恰 2 枚（favicon + apple-touch-icon）",
            len(re.findall(r"<link\b", raw)) == 2, "2", len(re.findall(r"<link\b", raw)))
    ext = re.findall(r"""<link\b(?![^>]*href=["']data:)""", raw)
    L.check("A3 零外链不变量：无任何 href 非 data: 的 link", not ext, "0 处", f"{len(ext)} 处")
    n_icon = len(re.findall(r'<link rel="icon"[^>]*href="data:image/png;base64,', raw))
    n_touch = len(re.findall(r'<link rel="apple-touch-icon"[^>]*href="data:image/png;base64,', raw))
    L.check("A4 两枚图标 link 均声明 data:image 且 rel 正确",
            n_icon == 1 and n_touch == 1, "icon 1 + apple-touch-icon 1",
            f"icon={n_icon} apple-touch-icon={n_touch}")

    # 载荷可解码 + 魔数正确（防复制截断 / 编码错配）
    payloads = re.findall(r"""href="data:image/(png|webp);base64,([^"]+)""", raw)
    magics, bad = [], []
    for kind, b64 in payloads:
        try:
            blob = base64.b64decode(b64)
        except Exception as e:  # noqa: BLE001
            bad.append(f"{kind}:{e}")
            continue
        want = b"\x89PNG" if kind == "png" else b"RIFF"
        (magics if blob[:4] == want else bad).append(f"{kind}:{len(blob)}B")
    m = re.search(r'--app-icon:url\("data:image/webp;base64,([^"]+)"\)', raw)
    if m:
        blob = base64.b64decode(m.group(1))
        (magics if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP" else bad).append(
            f"app-icon(webp):{len(blob)}B")
    L.check("A5 三段 base64 载荷解码成功且魔数正确", not bad and len(magics) == 3,
            "png + png + webp 均通过", f"通过 {magics} 失败 {bad}")

    L.check("A6 母图 base64 全文仅内联一次（单点消费，无重复载荷）",
            raw.count("data:image/webp;base64,") == 1, "1", raw.count("data:image/webp;base64,"))
    L.check("A7 R43 注释对成对平衡（CSS 层 + head link 对）",
            raw.count("R43:BEGIN") == raw.count("R43:END") == 1
            and raw.count("R43-ICON:BEGIN") == raw.count("R43-ICON:END") == 1,
            "各 1", f"{raw.count('R43:BEGIN')}/{raw.count('R43:END')}, "
                    f"{raw.count('R43-ICON:BEGIN')}/{raw.count('R43-ICON:END')}")
    offenders = [c[:60] for c in re.findall(r"<!--(.*?)-->", raw, re.S) if "--" in c]
    L.check("A8 HTML 注释内无连续双连字符（W3C；R43-ICON 注释须避开 --app-icon 写法）",
            not offenders, "0 处", f"{len(offenders)} 处", " | ".join(offenders[:2]))
    miss = [m for m in SLOT_MARKUP if raw.count(m) != 1]
    L.check("A9 六处槽位标记逐字在位且各一处（含 !DEV 兜底分支那处）",
            not miss, "六条各命中 1 次", f"{len(miss)} 条缺失", "; ".join(x[:60] for x in miss))
    L.check("A12 旧字形未被局部漏换：📷 计数 0 且 app-ic 消费点 >= 6",
            raw.count(GLYPH) == 0 and raw.count("app-ic") >= 9,
            "0 字形 / >=9 引用", f"{raw.count(GLYPH)} / {raw.count('app-ic')}")

    lines = raw.split("\n")
    tut = [l for l in lines if l.lstrip().startswith('<script id="tut-data"')]
    dev = [l for l in lines if 'id="dev-data"' in l]
    L.check("A10 两条巨型数据行仍在位且未被触碰",
            len(tut) == 1 and len(dev) == 1 and len(tut[0]) > 1_000_000 and len(dev[0]) > 100_000,
            "各 1 行，tut>1MB / dev>100KB",
            f"tut={len(tut[0]) if tut else 0} dev={len(dev[0]) if dev else 0}")
    n_font = len(re.findall(r"@font-face\s*\{", raw))
    n_other = len(re.findall(r"<script[^>]*\bsrc\s*=|<iframe|url\(\s*['\"]?https?:", raw))
    L.check("A11 零外链旁证：@font-face 仍 2 处、无 script src / iframe / url(http",
            n_font == 2 and n_other == 0,
            "font-face=2 其余 0", f"font-face={n_font} other={n_other}")
    return raw


JS_SLOT = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  const parent = el.parentElement;
  const pcs = parent ? getComputedStyle(parent) : null;
  return {
    w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10,
    fs: parseFloat(cs.fontSize),
    bg: cs.backgroundImage.slice(0, 24), bgLen: cs.backgroundImage.length,
    size: cs.backgroundSize, repeat: cs.backgroundRepeat, radius: cs.borderTopLeftRadius,
    pRadius: pcs ? pcs.borderTopLeftRadius : null,
    pBg: pcs ? pcs.backgroundColor : null, pBorder: pcs ? pcs.borderTopWidth : null,
    display: cs.display, visible: r.width > 0 && r.height > 0 && cs.display !== 'none',
  };
}"""

JS_OVERFLOW = """() => {
  const de = document.documentElement;
  return {over: de.scrollWidth - de.clientWidth, brandH: (() => {
    const b = document.querySelector('.lp-brand');
    return b ? Math.round(b.getBoundingClientRect().height) : 0;
  })()};
}"""


def main():
    L = Ledger()
    source_checks(L)

    console_errors, failed_reqs = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.on("requestfailed", lambda r: failed_reqs.append(r.url[:80]))

        # ---------------------------------------------------- B1 六槽位几何与占位
        for label, view, sel, unreachable in SLOTS:
            if unreachable:
                L.skip(f"B1 {label} 渲染且占位 = 1em", "宽=高=fontSize", unreachable)
                continue
            page.goto(URL + view)
            page.wait_for_timeout(500)
            d = page.evaluate(JS_SLOT, sel)
            if d is None:
                L.check(f"B1 {label}", False, "元素存在", "未命中选择器 " + sel)
                continue
            square = abs(d["w"] - d["h"]) < 0.6
            one_em = abs(d["w"] - d["fs"]) < 0.6
            L.check(f"B1 {label} 渲染且占位 = 1em",
                    d["visible"] and square and one_em and d["bg"].startswith("url("),
                    "宽=高=fontSize 且 background-image 非 none",
                    f"{d['w']}×{d['h']} fs={d['fs']} bg={d['bg']} size={d['size']}")

        # ---------------------------------------------------- B2 瓦片宿主样式未被覆盖
        page.goto(URL + "#/identity")
        page.wait_for_timeout(500)
        tile = page.evaluate(JS_SLOT, ".gate .gate-emoji .app-ic")
        L.check("B2 身份门瓦片圆角/底色/描边保留（background-image 长写不吞简写）",
                tile and tile["pRadius"] not in (None, "0px")
                and tile["pBg"] not in (None, "rgba(0, 0, 0, 0)"),
                "瓦片仍有圆角与底色",
                f"pRadius={tile['pRadius'] if tile else None} pBg={tile['pBg'] if tile else None} "
                f"pBorder={tile['pBorder'] if tile else None}")
        page.goto(URL + "#/dev")
        page.wait_for_timeout(500)
        q = page.evaluate(JS_SLOT, ".quick .q-emoji .app-ic")
        L.check("B2b 快捷卡瓦片圆角/底色保留",
                q and q["pRadius"] not in (None, "0px") and q["pBg"] not in (None, "rgba(0, 0, 0, 0)"),
                "瓦片仍有圆角与底色",
                f"pRadius={q['pRadius'] if q else None} pBg={q['pBg'] if q else None}")

        # ---------------------------------------------------- B3 母图可解码（WebP 支持面）
        decoded = page.evaluate("""() => new Promise(res => {
          const u = getComputedStyle(document.documentElement).getPropertyValue('--app-icon').trim();
          const href = u.replace(/^url\\(["']?/, '').replace(/["']?\\)$/, '');
          const im = new Image();
          im.onload = () => res({ok: true, w: im.naturalWidth, h: im.naturalHeight});
          im.onerror = () => res({ok: false, w: 0, h: 0});
          im.src = href;
        })""")
        L.check("B3 --app-icon 母图在真实浏览器中解码成功",
                decoded["ok"] and decoded["w"] == 256 and decoded["h"] == 256,
                "naturalWidth/Height = 256", f"{decoded}")

        # ---------------------------------------------------- B4 favicon 被文档采纳
        hrefs = page.evaluate("""() => [...document.querySelectorAll('link[rel]')]
            .filter(l => /icon/i.test(l.rel))
            .map(l => ({rel: l.rel, ok: l.href.startsWith('data:image/'), len: l.href.length}))""")
        L.check("B4 两枚图标 link 的 DOM href 均为 data: 内联",
                len(hrefs) == 2 and all(h["ok"] for h in hrefs),
                "2 枚且 data:", f"{hrefs}")

        # ---------------------------------------------------- B5 溢出矩阵（无重载驱动）
        if SKIP_SLOW:
            L.skip("B5 四断点 × 双主题 × 三态零横向溢出", "over <= 0", "--skip-slow")
        else:
            bad = []
            for view in VIEWS_MATRIX:
                page.goto(URL + view)
                page.wait_for_timeout(420)
                for w in WIDTHS:
                    page.set_viewport_size({"width": w, "height": 860})
                    for theme in ("light", "dark"):
                        for look in ("neutral", "color", "plain"):
                            page.evaluate(
                                """([t,l]) => {
                                  const de = document.documentElement;
                                  if (t === 'dark') de.setAttribute('data-theme','dark');
                                  else de.removeAttribute('data-theme');
                                  de.setAttribute('data-look', l);
                                }""",
                                [theme, look])
                            page.wait_for_timeout(70)
                            r = page.evaluate(JS_OVERFLOW)
                            if r["over"] > 0:
                                bad.append(f"{view}@{w}/{theme}/{look}=+{r['over']}")
                            if w == 390 and view == "#/" and r["brandH"] > 52:
                                bad.append(f"390 landing .lp-brand 高 {r['brandH']}>52")
                    page.set_viewport_size({"width": 1440, "height": 900})
            L.check("B5 四断点 × 双主题 × 三态零横向溢出（含 390 landing 品牌高度）",
                    not bad, "全部 over<=0 且 brandH<=52", f"{len(bad)} 处", "; ".join(bad[:4]))

        # ---------------------------------------------------- B6 plain 态灰度
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(URL + "#/")
        page.wait_for_timeout(420)
        gray = page.evaluate("""() => {
          document.documentElement.setAttribute('data-look','plain');
          const e = document.querySelector('#lp-nav .lp-brand-mark.app-ic');
          return e ? getComputedStyle(e).filter : null;
        }""")
        L.check("B6 data-look=plain 时图标灰度化（与社交图标同口径）",
                gray is not None and "grayscale" in gray, "filter 含 grayscale", f"{gray}")
        page.evaluate("() => document.documentElement.setAttribute('data-look','neutral')")

        # ---------------------------------------------------- B7 零请求失败 / 零报错
        L.check("B7 控制台零报错 + 零请求失败（无资源缺失/引用错误）",
                not console_errors and not failed_reqs, "0 / 0",
                f"console={console_errors[:2]} reqfail={failed_reqs[:2]}")
        ctx.close()

        # ---------------------------------------------------- B8 禁 JS 下静态图标仍在
        nctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                   java_script_enabled=False)
        npage = nctx.new_page()
        npage.goto(URL + "#/")
        npage.wait_for_timeout(700)
        static_ok = npage.evaluate("""() => {
          const out = {};
          for (const sel of ['#lp-nav .lp-brand-mark.app-ic', '#topbar .lg-emoji.app-ic']) {
            const e = document.querySelector(sel);
            const cs = e && getComputedStyle(e);
            out[sel] = {
              styled: !!(cs && cs.backgroundImage.startsWith('url(')),
              // 禁 JS 时 body[data-view] 停在静态初值 home，#lp-nav 整条导航按视图隐藏，
              // 属既有路由行为而非图标缺失，故可见性只就顶栏（home 视图显示）判定。
              box: e ? Math.round(e.getBoundingClientRect().width) : -1,
            };
          }
          return out;
        }""")
        nav = static_ok['#lp-nav .lp-brand-mark.app-ic']
        top = static_ok['#topbar .lg-emoji.app-ic']
        L.check("B8 禁用 JS 时两处静态图标样式仍生效（CSS 层路径，不破 R8b）",
                nav["styled"] and top["styled"] and top["box"] > 0,
                "两处 background-image 均为 url()，顶栏可见",
                f"nav={nav} top={top}")
        nctx.close()
        browser.close()

    return L.report("R43 软件图标层专项探针")


if __name__ == "__main__":
    sys.exit(main())
