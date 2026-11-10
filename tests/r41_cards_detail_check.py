#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R41 卡片二级详情展开专项探针（landing 主要功能 6 卡 + 产品优势 3 卡）

用法：
    py tests/r41_cards_detail_check.py              全量（含横向溢出与双主题）
    py tests/r41_cards_detail_check.py --skip-slow  跳过横向溢出与二/三级断点矩阵

协议：file:// 直开，无端口自起。依赖 playwright（本机基线 Python 3.12，用 py 启动器）。
口径要点：
  * 面板惰性创建且默认脱离文档，故加载期 document.body.innerText 快照不受影响（对应 r37 F2）。
  * 同行判定用 offsetTop（整数、同行严格相等），天然适配 3/2/1 列断点。
  * 零跳动由「锚点行负 margin 吸收多出的一份 row gap」保证：插入瞬间下方行位移必须为 0。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
FILE = ROOT / "Meow Star Map 官网.html"
URL = FILE.as_uri()
SKIP_SLOW = "--skip-slow" in sys.argv

VIEWPORTS = [("desktop", 1440, 900), ("tablet", 800, 900), ("phone", 390, 780)]
CARDS_JS = "Array.prototype.slice.call(document.querySelectorAll('.lpx-card-grid>.lpx-card,.lpx-adv-grid>.lpx-card'))"


class Log:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, want, got="", note=""):
        self.rows.append(("ok" if ok else "FAIL", name, want, got, note))

    def skip(self, name, want, why):
        self.rows.append(("skip", name, want, why, ""))

    def report(self, title):
        p = f = s = 0
        print()
        print("=" * 78)
        print(title)
        print("=" * 78)
        for st, name, want, got, note in self.rows:
            print(f"  {st:4}  {name}")
            if st == "FAIL":
                print(f"        期望: {want}")
                print(f"        实际: {got}")
            elif st == "skip":
                print(f"        跳过: {want} / {got}")
            if note:
                print(f"        {note}")
            p += st == "ok"
            f += st == "FAIL"
            s += st == "skip"
        print("-" * 78)
        print(f"合计 {p + f + s} | PASS {p} | FAIL {f} | SKIP {s}")
        print()
        return 1 if f else 0


def new_page(browser, w, h, reduced=None, scheme=None):
    ctx = browser.new_context(viewport={"width": w, "height": h})
    if reduced:
        ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion=reduced)
    page = ctx.new_page()
    if scheme:
        page.emulate_media(color_scheme=scheme)
    page.goto(URL, wait_until="load")
    page.wait_for_timeout(150)
    return ctx, page


def run():
    L = Log()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            # ---------- A 结构挂载 ----------
            ctx, page = new_page(browser, 1440, 900)
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

            n = page.evaluate(f"{CARDS_JS}.length")
            L.check("A1 两网格共 9 张卡片被识别", n == 9, "9", n)

            tg = page.evaluate("document.querySelectorAll('.lpx-card-toggle').length")
            L.check("A2 9 张卡各挂一个覆盖层触发按钮", tg == 9, "9", tg)

            pos = page.evaluate(
                "getComputedStyle(document.querySelector('.lpx-card-toggle')).position"
            )
            L.check("A3 覆盖层 position 未被 R21 的 .r21-b 打回静态流", pos == "absolute",
                    "absolute", pos,
                    "R21 会给所有 button 挂 .r21-b{position:relative}，需靠 0,3,0 特异度压过")

            geo = page.evaluate("""() => {
              const c = document.querySelector('.lpx-card-grid>.lpx-card');
              const b = c.querySelector('.lpx-card-toggle');
              const cr = c.getBoundingClientRect(), br = b.getBoundingClientRect();
              return {dx: Math.round(br.left - cr.left), dy: Math.round(br.top - cr.top),
                      dw: Math.round(cr.right - br.right), dh: Math.round(cr.bottom - br.bottom)};
            }""")
            ok_geo = all(abs(v - 1) <= 1 for v in geo.values())
            L.check("A4 覆盖层贴合卡片 padding box（四边各内缩 1px 边框）", ok_geo,
                    "四边均约 1px", geo)

            lab = page.evaluate("""() => {
              const b = document.querySelector('.lpx-card-toggle');
              const id = b.getAttribute('aria-labelledby');
              const h = id ? document.getElementById(id) : null;
              return {id: id, text: h ? h.textContent.trim() : null,
                      exp: b.getAttribute('aria-expanded'),
                      ctl: b.getAttribute('aria-controls')};
            }""")
            L.check("A5 覆盖层可访问名取自卡片标题且初始为折叠态",
                    bool(lab["text"]) and lab["exp"] == "false" and lab["ctl"] == "r41-det",
                    "文本非空 / expanded=false / controls=r41-det", lab)

            # ---------- B 零跳动 ----------
            jump = page.evaluate("""() => {
              const cs = Array.prototype.slice.call(document.querySelectorAll('.lpx-card-grid>.lpx-card'));
              const probe = cs[3];                       // 第二行首张（3 列断点）
              const before = probe.offsetTop;
              cs[0].querySelector('.lpx-card-toggle').click();
              const after = probe.offsetTop;             // 同一 tick，面板高度仍为 0
              return {before: before, after: after, delta: after - before};
            }""")
            L.check("B1 插入详情行瞬间下方行位移为 0（负 margin 吸收多出的 row gap）",
                    jump["delta"] == 0, "位移 0", jump,
                    "若不做锚点行补偿，此处会固定多出 18px")

            page.wait_for_timeout(600)
            grew = page.evaluate("""() => {
              const p = document.getElementById('r41-det');
              return p ? Math.round(p.getBoundingClientRect().height) : -1;
            }""")
            L.check("B2 面板展开后高度大于 0", grew > 40, ">40px", f"{grew}px")

            panel_n = page.evaluate("document.querySelectorAll('.lpx-detpanel').length")
            open_n = page.evaluate("document.querySelectorAll('.lpx-card.is-open').length")
            L.check("B3 同时仅一个面板、一张卡为展开态", panel_n == 1 and open_n == 1,
                    "1 / 1", f"{panel_n} / {open_n}")

            # ---------- C 锚点行 ----------
            def anchor_at(w, h, idx):
                c2, p2 = new_page(browser, w, h)
                try:
                    p2.evaluate(f"""{CARDS_JS}[{idx}].querySelector('.lpx-card-toggle').click()""")
                    p2.wait_for_timeout(500)
                    return p2.evaluate("""() => {
                      const p = document.getElementById('r41-det');
                      if (!p) return null;
                      const cs = Array.prototype.slice.call(
                        document.querySelectorAll('.lpx-card-grid>.lpx-card'));
                      return {prev: cs.indexOf(p.previousElementSibling),
                              title: p.previousElementSibling
                                ? p.previousElementSibling.querySelector('h3').textContent.trim() : null,
                              w: Math.round(p.getBoundingClientRect().width),
                              gw: Math.round(p.parentNode.getBoundingClientRect().width)};
                    }""")
                finally:
                    c2.close()

            a3 = anchor_at(1440, 900, 1)
            L.check("C1 三列断点：点第 2 张 → 面板挂在第 3 张之后",
                    a3 and a3["prev"] == 2, "索引 2", a3)
            L.check("C2 三列断点：面板占满整行", a3 and a3["w"] == a3["gw"],
                    "面板宽 == 网格宽", a3)

            if not SKIP_SLOW:
                a2 = anchor_at(800, 900, 1)
                L.check("C3 两列断点（≤960）：点第 2 张 → 面板挂在第 2 张之后",
                        a2 and a2["prev"] == 1, "索引 1", a2)
                a1 = anchor_at(390, 780, 1)
                L.check("C4 单列断点（≤640）：面板挂在该卡自身之后",
                        a1 and a1["prev"] == 1, "索引 1", a1)

            ctx.close()

            # ---------- D 切换与收起 ----------
            ctx, page = new_page(browser, 1440, 900)
            page.evaluate(f"{CARDS_JS}[0].querySelector('.lpx-card-toggle').click()")
            page.wait_for_timeout(500)
            sw = page.evaluate("""() => {
              const cs = Array.prototype.slice.call(document.querySelectorAll('.lpx-card-grid>.lpx-card'));
              const p = document.getElementById('r41-det');
              const homeBefore = p.previousElementSibling;
              cs[1].querySelector('.lpx-card-toggle').click();   // 同行切换
              const homeAfter = document.getElementById('r41-det').previousElementSibling;
              return {sameHome: homeBefore === homeAfter,
                      open: document.querySelectorAll('.lpx-card.is-open').length,
                      panels: document.querySelectorAll('.lpx-detpanel').length,
                      text: document.querySelector('.lpx-det-list').textContent.slice(0, 12)};
            }""")
            page.wait_for_timeout(500)
            L.check("D1 同行切换：面板不搬家、内容就地替换",
                    sw["sameHome"] and sw["panels"] == 1 and sw["open"] == 1,
                    "同锚点 / 1 面板 / 1 展开", sw)

            sw2 = page.evaluate("""() => {
              const cs = Array.prototype.slice.call(document.querySelectorAll('.lpx-card-grid>.lpx-card'));
              cs[4].querySelector('.lpx-card-toggle').click();   // 跨行切换
              return true;
            }""")
            page.wait_for_timeout(900)
            st2 = page.evaluate("""() => {
              const p = document.getElementById('r41-det');
              const cs = Array.prototype.slice.call(document.querySelectorAll('.lpx-card-grid>.lpx-card'));
              return {panels: document.querySelectorAll('.lpx-detpanel').length,
                      open: document.querySelectorAll('.lpx-card.is-open').length,
                      prev: p ? cs.indexOf(p.previousElementSibling) : -1,
                      top: p ? document.querySelector('.lpx-det-list').textContent.slice(0, 12) : ''};
            }""")
            L.check("D2 跨行切换：先收后移，最终仍仅一个面板且挂到新锚点行",
                    st2["panels"] == 1 and st2["open"] == 1 and st2["prev"] == 5,
                    "1 面板 / 1 展开 / 锚点索引 5", st2)

            page.evaluate("document.querySelector('.lpx-det-close').click()")
            page.wait_for_timeout(700)
            cl = page.evaluate("""() => {
              const cs = Array.prototype.slice.call(
                document.querySelectorAll('.lpx-card-grid>.lpx-card,.lpx-adv-grid>.lpx-card'));
              return {panels: document.querySelectorAll('.lpx-detpanel').length,
                      open: document.querySelectorAll('.lpx-card.is-open').length,
                      mb: cs.filter(c => c.style.marginBottom !== '').length,
                      exp: document.querySelector('.lpx-card-toggle').getAttribute('aria-expanded')};
            }""")
            L.check("D3 收起后无状态残留（无面板 / 无展开态 / 无 margin 残留 / aria 复位）",
                    cl["panels"] == 0 and cl["open"] == 0 and cl["mb"] == 0 and cl["exp"] == "false",
                    "0 / 0 / 0 / false", cl)

            # ---------- E 键盘与焦点 ----------
            page.evaluate(f"{CARDS_JS}[0].querySelector('.lpx-card-toggle').focus()")
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
            k1 = page.evaluate("""() => ({
              panels: document.querySelectorAll('.lpx-detpanel').length,
              exp: document.querySelector('.lpx-card-toggle').getAttribute('aria-expanded')
            })""")
            L.check("E1 键盘 Enter 可展开", k1["panels"] == 1 and k1["exp"] == "true",
                    "1 面板 / true", k1)

            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            k2 = page.evaluate("""() => ({
              panels: document.querySelectorAll('.lpx-detpanel').length,
              focus: document.activeElement && document.activeElement.className || '',
              ring: document.activeElement
                ? getComputedStyle(document.activeElement).outlineWidth : ''
            })""")
            L.check("E2 Escape 关闭且焦点归还该卡触发按钮",
                    k2["panels"] == 0 and "lpx-card-toggle" in k2["focus"],
                    "0 面板 / 焦点在 toggle", k2)

            ring = page.evaluate("""() => {
              const b = document.querySelector('.lpx-card-toggle');
              b.focus();
              const s = getComputedStyle(b);
              return {w: s.outlineWidth, style: s.outlineStyle, color: s.outlineColor};
            }""")
            L.check("E3 触发按钮具备可见焦点环（继承既有 --focus-ring 口径）",
                    ring["w"] != "0px" and ring["style"] != "none",
                    "outline 非 0 且 style 非 none", ring,
                    "本层不写任何焦点样式，依赖 L33 + L1017 的 button:focus-visible")

            # ---------- F 链接与文案 ----------
            nav = page.evaluate("""() => {
              const cs = Array.prototype.slice.call(
                document.querySelectorAll('.lpx-card-grid>.lpx-card,.lpx-adv-grid>.lpx-card'));
              let hit = null;
              cs.forEach(c => { if (c.querySelector('h3').textContent.trim() === '本地优先') hit = c; });
              if (!hit) return null;
              hit.querySelector('.lpx-card-toggle').click();
              const a = hit.querySelector('.lpx-more');
              return {href: a ? a.getAttribute('href') : null,
                      z: a ? getComputedStyle(a).zIndex : null};
            }""")
            page.wait_for_timeout(400)
            L.check("F1 「本地优先」卡内既有链接抬到覆盖层之上且 href 未变",
                    nav and nav["href"] == "#/privacy" and nav["z"] == "2",
                    "href=#/privacy 且 z-index=2", nav)

            copy = page.evaluate("""() => {
              const out = [];
              const cs = Array.prototype.slice.call(
                document.querySelectorAll('.lpx-card-grid>.lpx-card,.lpx-adv-grid>.lpx-card'));
              cs.forEach(c => {
                out.push(c.querySelector('h3').textContent.trim());
              });
              return out;
            }""")
            want = ["智能扫描", "多视图图库", "专业图片编辑", "智能整理", "重复检测", "分享与备份",
                    "本地优先", "同步由你决定", "为玩家而设"]
            L.check("F2 9 张卡标题原样未改（模板零改动）", copy == want, want, copy)

            det = page.evaluate("""() => {
              const r = window.__r41;
              const keys = ['智能扫描','多视图图库','专业图片编辑','智能整理','重复检测',
                            '分享与备份','本地优先','同步由你决定','为玩家而设'];
              return keys.map(k => {
                r.close();
                const okOpen = r.open(k);
                const p = document.getElementById('r41-det');
                return {k: k, ok: okOpen,
                        n: p ? p.querySelectorAll('.lpx-det-list li').length : 0,
                        href: p && p.querySelector('.lpx-det-link')
                          ? p.querySelector('.lpx-det-link').getAttribute('href') : null};
              });
            }""")
            bad = [d for d in det if not d["ok"] or d["n"] < 2 or not d["href"]]
            L.check("F3 9 张卡均有 ≥2 条要点与一个了解更多链接", not bad,
                    "全部 ok 且要点≥2", bad if bad else "全部通过")

            L.check("F4 控制台零报错 / 零未捕获异常", not errs, "0 条", errs[:3])
            ctx.close()

            # ---------- G 减少动效 ----------
            ctx, page = new_page(browser, 1440, 900, reduced="reduce")
            rm = page.evaluate("""() => {
              const cs = Array.prototype.slice.call(document.querySelectorAll('.lpx-card-grid>.lpx-card'));
              cs[0].querySelector('.lpx-card-toggle').click();
              const p = document.getElementById('r41-det');
              if (!p) return {dur: -1, h: -1};
              const st = getComputedStyle(p);
              return {dur: parseFloat(st.transitionDuration) || 0,
                      prop: st.transitionProperty,
                      h: Math.round(p.getBoundingClientRect().height)};
            }""")
            # 本层已显式 transition:none，但全站总闸会把时长压到 .01ms（计算值表现为 1e-05s），
            # 故按「时长 < 10ms」判定，而非要求字符串为 0s
            L.check("G1 减少动效偏好下过渡被关闭且面板立即可见",
                    rm["dur"] < 0.01 and rm["h"] > 40,
                    "transition 时长 <10ms 且 高度 >40px", rm)
            page.evaluate("document.querySelector('.lpx-det-close').click()")
            page.wait_for_timeout(120)
            rm2 = page.evaluate("document.querySelectorAll('.lpx-detpanel').length")
            L.check("G2 减少动效偏好下收起立即完成（不留待清理面板）", rm2 == 0, "0", rm2)
            ctx.close()

            # ---------- H 横向溢出 ----------
            if SKIP_SLOW:
                L.skip("H1 展开态全断点双主题零横向溢出", "0 处", "--skip-slow 已跳过")
            else:
                bad = []
                for name, w, h in VIEWPORTS:
                    for scheme in ("light", "dark"):
                        c3, p3 = new_page(browser, w, h, scheme=scheme)
                        try:
                            p3.evaluate(f"{CARDS_JS}[1].querySelector('.lpx-card-toggle').click()")
                            p3.wait_for_timeout(500)
                            ov = p3.evaluate(
                                "document.documentElement.scrollWidth - document.documentElement.clientWidth")
                            if ov > 0:
                                bad.append(f"{name}/{scheme}: +{ov}px")
                        finally:
                            c3.close()
                L.check("H1 展开态全断点双主题零横向溢出", not bad, "0 处", bad)
        finally:
            browser.close()

    return L.report("R41 卡片二级详情展开专项探针")


if __name__ == "__main__":
    sys.exit(run())
