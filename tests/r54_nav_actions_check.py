#!/usr/bin/env python3
"""R54/R55 常驻导航文字入口间距探针。"""

from __future__ import annotations

import pathlib
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from i18n_pin import pin_browser

SRC = ROOT / "Meow Star Map 官网.html"
SITE = ROOT / "site" / "index.html"
LANGS = ("zh", "en", "fr", "es", "ru", "ar")
WIDTHS = (360, 390, 400, 401, 560, 561, 640, 641, 768, 900, 1024, 1440, 1920)
ROUTES = ("#/", "#/features", "#/resonance", "#/privacy", "#/download", "#/download/start")

PROBE = """() => {
  const links = document.querySelector('#lp-nav .lp-links');
  const routes = document.querySelector('#lp-nav .lp-routes');
  const actions = document.querySelector('#lp-nav .lp-actions');
  const routeLinks = [...document.querySelectorAll('#lp-nav .lp-nav-link')];
  const actionLinks = [
    document.querySelector('#lp-nav a[href="#/identity"]'),
    document.querySelector('#lp-nav #lp-dl-link'),
    document.querySelector('#lp-nav #lp-about-link')
  ].filter(Boolean);
  const items = [...routeLinks, ...actionLinks].filter(Boolean);
  const visible = e => { const s=getComputedStyle(e),r=e.getBoundingClientRect(); return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0; };
  const box = e => { if(!e) return {left:0,right:0,top:0,bottom:0,width:0,height:0}; const r=e.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}; };
  const textBox = e => { const q=document.createRange(); q.selectNodeContents(e); const r=q.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}; };
  const lines = e => { const q=document.createRange(); q.selectNodeContents(e); return q.getClientRects().length; };
  const rows = items.map(e => {
    const s=getComputedStyle(e),r=box(e),t=textBox(e);
    const padStart=parseFloat(s.paddingInlineStart)||0,padEnd=parseFloat(s.paddingInlineEnd)||0;
    return {id:e.id||e.getAttribute('href')||e.dataset.route,group:e.classList.contains('lp-nav-link')?'route':'action',
      text:e.textContent.trim(),shown:visible(e),rect:r,textRect:t,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,
      whiteSpace:s.whiteSpace,flexShrink:s.flexShrink,fontSize:parseFloat(s.fontSize),padStart,padEnd,
      boxExtra:r.width-t.width-padStart-padEnd,lines:lines(e)};
  });
  const shown = rows.filter(x=>x.shown);
  const routeBox=routes?box(routes):null;
  const clipped = x => x.group==='route'&&routeBox
    ? {left:Math.max(x.rect.left,routeBox.left),right:Math.min(x.rect.right,routeBox.right),top:x.rect.top,bottom:x.rect.bottom}
    : x.rect;
  const outerGap=parseFloat(getComputedStyle(links).columnGap)||0;
  const pairs=[];
  for(let i=0;i<shown.length-1;i++) {
    const a=shown[i],b=shown[i+1],cross=a.group!==b.group;
    if(cross&&routeBox&&(a.rect.left<routeBox.left-1||a.rect.right>routeBox.right+1)) continue;
    const gap=document.documentElement.dir==='rtl'?a.textRect.left-b.textRect.right:b.textRect.left-a.textRect.right;
    const expected=outerGap+a.padEnd+b.padStart;
    pairs.push({a:a.id,b:b.id,gap,expected,error:Math.abs(gap-expected),cross});
  }
  const overlaps = [];
  for(let i=0;i<shown.length;i++) for(let j=i+1;j<shown.length;j++) {
    const a=clipped(shown[i]),b=clipped(shown[j]);
    if(a.right-a.left<=1||b.right-b.left<=1) continue;
    if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1) overlaps.push([shown[i].id,shown[j].id]);
  }
  const controls = [...document.querySelectorAll('#lp-nav .lp-gh,#lp-nav .lang-btn,#lp-nav .lp-thdots,#lp-nav .lp-thdots-toggle,#lp-nav .lp-themebtn,#lp-nav .look-btn')].filter(visible);
  const textControlOverlaps = [];
  for(const a of shown) {
    const ar=clipped(a); if(ar.right-ar.left<=1) continue;
    for(const b of controls) {
      const r=b.getBoundingClientRect();
      if(Math.min(ar.right,r.right)-Math.max(ar.left,r.left)>1 && Math.min(ar.bottom,r.bottom)-Math.max(ar.top,r.top)>1) textControlOverlaps.push([a.id,b.className||b.id]);
    }
  }
  const lr=box(links),nr=box(document.querySelector('#lp-nav')),br=box(document.querySelector('#lp-brand'));
  const actionRows=rows.filter(x=>x.group==='action'),routeRows=rows.filter(x=>x.group==='route');
  const outsideActions=actionRows.filter(x=>x.shown&&(x.rect.left<lr.left-1||x.rect.right>lr.right+1||x.rect.left<0||x.rect.right>innerWidth+1)).map(x=>x.id);
  const fonts=shown.map(x=>x.fontSize),pads=shown.flatMap(x=>[x.padStart,x.padEnd]);
  const gaps=pairs.map(x=>x.gap),errors=pairs.map(x=>x.error);
  const spread=v=>v.length?Math.max(...v)-Math.min(...v):0;
  const columnGaps=[links,routes,actions].filter(Boolean).map(e=>parseFloat(getComputedStyle(e).columnGap)||0);
  return {
    vw:innerWidth,dir:document.documentElement.dir,docOver:document.documentElement.scrollWidth-document.documentElement.clientWidth,
    navHeight:nr.height,brandHeight:br.height,linksRect:lr,linksOver:links.scrollWidth-links.clientWidth,
    hasRoutes:!!routes,hasActions:!!actions,routesClient:routes?routes.clientWidth:0,routesOver:routes?routes.scrollWidth-routes.clientWidth:0,
    routesOverflowX:routes?getComputedStyle(routes).overflowX:'',routeBox,routeRows:routeRows.map(x=>({id:x.id,rect:x.rect})),
    actionsRect:actions?box(actions):null,rows,shownCount:shown.length,actionShownCount:actionRows.filter(x=>x.shown).length,
    dlShown:actionLinks[1]?visible(actionLinks[1]):false,fontSizeSpread:spread(fonts),paddingSpread:spread(pads),
    columnGaps,columnGapSpread:spread(columnGaps),boxExtraMax:shown.length?Math.max(...shown.map(x=>Math.abs(x.boxExtra))):0,
    edgePairs:pairs,edgeGapSpread:spread(gaps),edgeGapError:errors.length?Math.max(...errors):0,
    overlaps,textControlOverlaps,outsideActions
  };
}"""


class Ledger:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, expected="", actual=""):
        self.rows.append((bool(ok), name, expected, actual))

    def report(self):
        for ok, name, expected, actual in self.rows:
            print(f"[{'PASS' if ok else 'FAIL'}] {name}")
            if not ok:
                print(f"        期望: {expected}\n        实测: {actual}")
        passed = sum(ok for ok, *_ in self.rows)
        failed = len(self.rows) - passed
        print(f"\n合计 {len(self.rows)} 项：PASS {passed} / FAIL {failed}")
        return failed


def check_geometry(ledger, d, width, lang, theme="light", suffix=""):
    tag = f"{width}/{lang}/{theme}{suffix}"
    expected_count = 7 if width >= 641 else 6
    ledger.check(f"{tag} 路由与动作分组存在", d["hasRoutes"] and d["hasActions"], "两个分组", (d["hasRoutes"], d["hasActions"]))
    ledger.check(f"{tag} 可见文字入口数量正确", d["shownCount"] == expected_count, str(expected_count), d["shownCount"])
    ledger.check(f"{tag} 页面无横向溢出", d["docOver"] <= 1, "<=1px", d["docOver"])
    ledger.check(f"{tag} 导航与品牌高度稳定", d["navHeight"] == 52 and d["brandHeight"] <= 52, "52px / brand<=52px", (d["navHeight"], d["brandHeight"]))
    ledger.check(f"{tag} 链接区自身不溢出", d["linksOver"] <= 1, "<=1px", d["linksOver"])
    ledger.check(f"{tag} 文字入口字号一致", d["fontSizeSpread"] <= 0.1, "字号差<=0.1px", d["fontSizeSpread"])
    ledger.check(f"{tag} 文字入口 inline padding 一致", d["paddingSpread"] <= 0.1, "padding 差<=0.1px", d["paddingSpread"])
    ledger.check(f"{tag} 三层 gap 一致", d["columnGapSpread"] <= 0.1, "gap 差<=0.1px", d["columnGaps"])
    ledger.check(f"{tag} 按钮盒无额外等宽留白", d["boxExtraMax"] <= 1, "盒宽-文字宽-padding<=1px", d["boxExtraMax"])
    ledger.check(f"{tag} 相邻文字边缘距一致", len(d["edgePairs"]) >= expected_count - 2 and d["edgeGapSpread"] <= 1, "间距差<=1px", (len(d["edgePairs"]), d["edgeGapSpread"]))
    ledger.check(f"{tag} 文字边缘距等于 gap+padding", d["edgeGapError"] <= 1, "误差<=1px", d["edgeGapError"])
    bad_text = [a for a in d["rows"] if a["shown"] and (a["whiteSpace"] != "nowrap" or a["lines"] != 1 or a["scrollWidth"] > a["clientWidth"] + 1)]
    ledger.check(f"{tag} 全部文字单行且不裁切", not bad_text, "nowrap / 1 行 / 不裁切", bad_text)
    ledger.check(f"{tag} 文字入口互不重叠", not d["overlaps"], "无重叠", d["overlaps"])
    ledger.check(f"{tag} 文字入口不遮挡图标控件", not d["textControlOverlaps"], "无重叠", d["textControlOverlaps"])
    ledger.check(f"{tag} 主动作完整位于可视区", not d["outsideActions"], "无越界", d["outsideActions"])
    if width >= 641:
        ledger.check(f"{tag} 三个主动作可见", d["actionShownCount"] == 3 and d["dlShown"], "3 / 下载按钮可见", (d["actionShownCount"], d["dlShown"]))
    else:
        ledger.check(f"{tag} 窄屏沿用下载按钮隐藏规则", d["actionShownCount"] == 2 and not d["dlShown"], "2 / 下载按钮隐藏", (d["actionShownCount"], d["dlShown"]))
    ledger.check(f"{tag} 路由保留独立滚动区", d["routesClient"] > 0 and d["routesOverflowX"] in ("auto", "scroll"), "clientWidth>0 / overflow-x:auto", (d["routesClient"], d["routesOverflowX"]))
    return d


def settle(page, lang, theme="light"):
    page.evaluate("(l) => window.__i18n.set(l, true)", lang)
    page.evaluate("(t) => { if(t==='dark') document.documentElement.setAttribute('data-theme','dark'); else document.documentElement.removeAttribute('data-theme'); }", theme)
    page.evaluate("async () => { await document.fonts.ready; }")
    page.wait_for_timeout(80)


def geometry_checks(ledger, page, width, lang, theme="light"):
    page.set_viewport_size({"width": width, "height": 900})
    if not page.url.endswith("#/"):
        page.goto(URL + "#/", wait_until="load")
    page.evaluate("() => { const r=document.querySelector('#lp-nav .lp-routes'); if(r) r.scrollLeft=0; }")
    settle(page, lang, theme)
    d = page.evaluate(PROBE)
    check_geometry(ledger, d, width, lang, theme)
    if d["hasRoutes"] and d["routesOver"] > 1:
        page.evaluate("() => { const r=document.querySelector('#lp-nav .lp-routes'); r.style.scrollBehavior='auto'; r.scrollLeft=document.documentElement.dir==='rtl'?-r.scrollWidth:r.scrollWidth; }")
        page.wait_for_timeout(50)
        end = page.evaluate(PROBE)
        rb = end["routeBox"]
        last = end["routeRows"][-1]["rect"]
        end_aligned = rb and (abs(last["left"] - rb["left"]) <= 1 if end["dir"] == "rtl" else abs(last["right"] - rb["right"]) <= 1)
        ledger.check(f"{width}/{lang}/{theme} 路由末项可滚至末端", end_aligned, "末项对齐滚动末端", last)
        last_full = rb and last["left"] >= rb["left"] - 1 and last["right"] <= rb["right"] + 1
        cross = [p for p in end["edgePairs"] if p["cross"]]
        if last_full:
            ledger.check(f"{width}/{lang}/{theme} 路由—动作跨界间距一致", bool(cross) and max(p["error"] for p in cross) <= 1, "gap+padding / 误差<=1px", cross)
        page.evaluate("() => { const r=document.querySelector('#lp-nav .lp-routes'); r.style.scrollBehavior='auto'; r.scrollLeft=0; }")
        page.wait_for_timeout(50)
        start = page.evaluate(PROBE)
        rb0 = start["routeBox"]
        first0 = start["routeRows"][0]["rect"]
        start_aligned = rb0 and (abs(first0["right"] - rb0["right"]) <= 1 if start["dir"] == "rtl" else abs(first0["left"] - rb0["left"]) <= 1)
        ledger.check(f"{width}/{lang}/{theme} 路由首项可滚回起点", start_aligned, "首项对齐滚动起点", first0)
    return d


def functional_checks(ledger, page):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(URL + "#/", wait_until="load")
    settle(page, "zh")
    page.click('#lp-nav a[href="#/identity"]')
    ledger.check("进入仍进入身份选择页", page.url.endswith("#/identity"), "#/identity", page.url)
    page.goto(URL + "#/", wait_until="load")
    page.click("#lp-dl-link")
    page.wait_for_timeout(700)
    ledger.check("下载按钮仍打开资源下载面板", page.evaluate("() => !document.querySelector('#lp-dl-menu').hidden"), "面板可见", page.evaluate("() => document.querySelector('#lp-dl-menu').hidden"))
    page.keyboard.press("Escape")
    page.evaluate("() => scrollTo(0,0)")
    page.click("#lp-about-link")
    page.wait_for_timeout(500)
    ledger.check("关于按钮仍滚动到关于板块", page.evaluate("() => scrollY>0 && !!document.querySelector('.about-sec')"), "scrollY>0", page.evaluate("() => scrollY"))
    gh = page.evaluate("() => { const a=document.querySelector('#lp-nav .lp-gh'); return {href:a.href,target:a.target,rel:a.rel}; }")
    ledger.check("GitHub 入口属性不变", gh["href"] == "https://github.com/QianQianLuLu1/MeowStarMap" and gh["target"] == "_blank" and gh["rel"] == "noopener noreferrer", "原 href/target/rel", gh)
    page.click("#lp-nav .lang-btn")
    ledger.check("语言菜单仍可打开", page.evaluate("() => window.__i18n.isOpen()"), "open", page.evaluate("() => window.__i18n.isOpen()"))
    page.keyboard.press("Escape")
    ledger.check("语言菜单仍可 Escape 关闭", page.evaluate("() => !window.__i18n.isOpen()"), "closed", page.evaluate("() => window.__i18n.isOpen()"))


def main():
    global URL
    URL = (SITE if "--site" in sys.argv else SRC).resolve().as_uri()
    slow = "--skip-slow" not in sys.argv
    ledger = Ledger()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = pin_browser(browser, "zh").new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)[:120]))
        page.on("console", lambda m: errors.append(m.text[:120]) if m.type == "error" else None)
        page.on("requestfailed", lambda r: errors.append(f"{r.url} {r.failure}"))
        page.goto(URL + "#/", wait_until="load")
        if slow:
            for width in WIDTHS:
                for lang in LANGS:
                    geometry_checks(ledger, page, width, lang)
            for width in (390, 641, 1440):
                for lang in ("zh", "en", "ar"):
                    geometry_checks(ledger, page, width, lang, "dark")
            for route in ROUTES:
                for width in (390, 641, 1440):
                    for lang in ("zh", "fr", "ar"):
                        page.set_viewport_size({"width": width, "height": 900})
                        page.goto(URL + route, wait_until="load")
                        settle(page, lang)
                        d = page.evaluate(PROBE)
                        check_geometry(ledger, d, width, lang, suffix=f"/{route}")
        else:
            for width, lang in ((390, "zh"), (641, "fr"), (1440, "zh")):
                geometry_checks(ledger, page, width, lang)
        functional_checks(ledger, page)
        ledger.check("全程 console/pageerror/requestfailed 零报错", not errors, "0 条", errors[:5])
        browser.close()
    return 1 if ledger.report() else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
