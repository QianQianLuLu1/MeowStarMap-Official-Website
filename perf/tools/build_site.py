#!/usr/bin/env python3
"""从「无损 WebP 单文件版」生成多文件站点 site/。

设计目标（网络加载速度）：
  - 落地页只下载 shell（HTML/CSS/JS/字体/图标），不再为约 24.04 MiB 的单文件源付费；
  - 教程截图改为独立 .webp 文件：按页、按需、可缓存，`#/all` 也真正惰性加载；
  - 教程 / 开发文档数据改为 external classic script，按路由加载并自动重渲；
  - 入口 hover 预取 + 空闲预取，切换路由近零等待。

产物：
  site/index.html
  site/assets/site.css        （R56：内联 <style> 拆为独立样式表）
  site/data/tutorial.js
  site/data/dev-docs.js
  site/assets/shots/*.webp
  site/assets/about-wx.jpg
  site/.nojekyll

用法：python perf/tools/build_site.py

定位（勿误解）：本脚本不是构建框架，而是「把 25 MB 单文件转换成多文件站点」的转换器。
除「抽数据」与「拆 CSS」外，其余步骤都是对源文件的字符串锚点替换，每步自带 FAIL 守卫；
它没有增量构建 / 任务图 / 插件体系 / 监听热更新 / CI 流水线，也没有 package.json。
源文件结构一变，这里必须同步改——所以不要手改 site/ 产物，改完脚本重跑即可。
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
SRC = REPO / "Meow Star Map 官网.html"
SITE = REPO / "site"
SHOTS = SITE / "assets" / "shots"
DATA = SITE / "data"
REPORTS = ROOT / "reports"

WEBP_RE = re.compile(r"data:image/webp;base64,([A-Za-z0-9+/=]+)")
JPEG_RE = re.compile(r"data:image/jpeg;base64,([A-Za-z0-9+/=]+)")
IMG_TAG_RE = re.compile(r"<img\b[^>]*>")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lazyify(html: str) -> str:
    def add(m):
        tag = m.group(0)
        extra = ""
        if not re.search(r"\sloading\s*=", tag):
            extra += ' loading="lazy"'
        if not re.search(r"\sdecoding\s*=", tag):
            extra += ' decoding="async"'
        if not extra:
            return tag
        return re.sub(r"\s*/?>$", extra + ">", tag)

    return IMG_TAG_RE.sub(add, html)


def main() -> int:
    if not SRC.exists():
        print(f"缺少 {SRC}")
        return 1
    raw = SRC.read_bytes()
    text = raw.decode("utf-8")

    m_tut = re.search(r'<script id="tut-data" type="application/json">(.*?)</script>', text, re.S)
    m_dev = re.search(r'<script id="dev-data" type="application/json">(.*?)</script>', text, re.S)
    if not m_tut or not m_dev:
        print("FAIL: 未找到数据块（需要先跑 build_lossless.py 的无损 WebP 版）")
        return 1
    tut = json.loads(m_tut.group(1))
    dev_text = m_dev.group(1)
    json.loads(dev_text)  # 校验 dev JSON 可解析

    for d in (SITE, SHOTS, DATA):
        d.mkdir(parents=True, exist_ok=True)
    # 不再批量删除旧截图：文件名由「内容 SHA → owner-NN」决定且稳定，重跑会直接覆盖；
    # 批量 unlink 在受管/沙箱环境下会被 safe-delete 守卫拦截并超时（R52 实测）。
    stale = 0

    by_sha: dict[str, str] = {}
    written = 0

    def transform(html: str, owner: str) -> str:
        nonlocal written
        seq = [0]

        def repl(m):
            nonlocal written
            data = base64.b64decode(m.group(1))
            key = sha(data)
            if key in by_sha:
                return by_sha[key]
            seq[0] += 1
            name = f"{owner}-{seq[0]:02d}.webp"
            (SHOTS / name).write_bytes(data)
            by_sha[key] = f"assets/shots/{name}"
            written += 1
            return by_sha[key]

        return lazyify(WEBP_RE.sub(repl, html))

    def walk(node, owner):
        if isinstance(node, dict):
            if isinstance(node.get("id"), str):
                owner = node["id"]
            for k in list(node.keys()):
                node[k] = walk(node[k], owner)
            return node
        if isinstance(node, list):
            return [walk(v, owner) for v in node]
        if isinstance(node, str):
            return transform(node, owner)
        return node

    walk(tut, "root")
    if written != 48:
        print(f"FAIL: 期望写出 48 张，实际 {written}")
        return 1

    tut_js = json.dumps(tut, ensure_ascii=False, separators=(",", ":"))
    tut_js = tut_js.replace("</script", "<\\/script").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    with open(DATA / "tutorial.js", "w", encoding="utf-8", newline="") as f:
        f.write("window.__TUT__=" + tut_js + ";\n")

    dev_js = dev_text.replace("</script", "<\\/script")
    with open(DATA / "dev-docs.js", "w", encoding="utf-8", newline="") as f:
        f.write("window.__DEV__=" + dev_js + ";\n")

    # ── shell 改造 ──
    shell = text

    # 1) 关于板块的微信二维码（317 KB JPEG）外置 + 惰性加载
    m_qr = JPEG_RE.search(shell)
    if m_qr:
        (SITE / "assets" / "about-wx.jpg").write_bytes(base64.b64decode(m_qr.group(1)))
        shell = shell.replace(
            m_qr.group(0),
            "assets/about-wx.jpg",
            1,
        )
        # 给这张 img 补 loading/decoding（保留原有 alt 等属性）
        shell = re.sub(
            r'<img class="about-wx-img" src="assets/about-wx\.jpg"',
            '<img class="about-wx-img" loading="lazy" decoding="async" src="assets/about-wx.jpg"',
            shell,
            count=1,
        )

    # 2) 数据层：内联 JSON -> external classic script 按需加载
    start = shell.index("var DATA=null, MODS=null, ORDER=[], byId={}, modById={};")
    end = shell.index("var lowCache={};", start)
    new_layer = r"""/* ═══ 多文件版数据层（20261116 性能轮）═══
   教程 / 开发文档数据外置为 classic script，按路由加载；file:// 直开同样可用。
   落地页不请求任何数据文件；教程数据在空闲时预取，hover 入口时也会预取。 */
var DATA=null, MODS=null, ORDER=[], byId={}, modById={}, DEV=null;
var _tutState=0, _devState=0;
function needsTut(){var h=(location.hash||'#/').slice(1).split('@')[0];return h==='/all'||h==='/tutorial'||/^\/m\d+(\/|$)/.test(h);}
function needsDev(){var h=(location.hash||'#/').slice(1).split('@')[0];return h==='/dev'||h.indexOf('/dev/')===0;}
function loadScriptOnce(src,onOk,onErr){
  var s=document.createElement('script');
  s.src=src; s.async=true;
  s.onload=onOk; s.onerror=onErr;
  document.head.appendChild(s);
}
function ensureTut(){
  if(DATA) return true;
  if(_tutState===1) return false;
  _tutState=1;
  loadScriptOnce('data/tutorial.js',function(){
    DATA=window.__TUT__||null;
    if(!DATA){_tutState=0;return;}
    MODS=DATA.modules;
    MODS.forEach(function(m){modById[m.id]=m;});
    MODS.forEach(function(m){m.pages.forEach(function(pid){ORDER.push({m:m,pid:pid,p:DATA.pages.find(function(x){return x.id===pid;})});});});
    ORDER.forEach(function(o){byId[o.pid]=o;});
    USER_SB=null; sbFamily=''; _tutState=2;
    var sbx=document.getElementById('searchbox');
    if(sbx&&sbx.value.trim()){try{sbx.dispatchEvent(new Event('input'));}catch(e){}}
    if(needsTut()) render();
  },function(){_tutState=0;});
  return false;
}
function ensureDev(){
  if(DEV) return true;
  if(_devState===1) return false;
  _devState=1;
  loadScriptOnce('data/dev-docs.js',function(){
    DEV=window.__DEV__||null;
    if(!DEV){_devState=0;return;}
    buildDevIndexes();
    DEV_SB=buildDevSb(); _devState=2;
    if(needsDev()) render();
  },function(){_devState=0;});
  return false;
}
"""
    shell = shell[:start] + new_layer + shell[end:]

    # 3) buildUserSb：数据未就绪时返回空串（由 render 的占位兜底）
    old_user = "  if(USER_SB!==null) return USER_SB;\r\n  ensureTut();"
    if old_user not in shell:
        old_user = "  if(USER_SB!==null) return USER_SB;\n  ensureTut();"
    if old_user not in shell:
        print("FAIL: buildUserSb 守卫未匹配")
        return 1
    shell = shell.replace(old_user, old_user.split("ensureTut")[0] + "if(!DATA) return '';", 1)

    # 4) DEV_SB：加载期 IIFE -> 惰性函数
    s = shell.index("var DEV_SB=(function(){")
    e = shell.index("var sbFamily='';", s)
    block = shell[s:e]
    inner = block[len("var DEV_SB=(function(){\r\n"): block.rindex("})();")]
    inner = inner.replace("if(!DEV)return '';", "", 1).rstrip()
    if inner.endswith("return h;"):
        inner = inner[: -len("return h;")].rstrip()
    new_dev_sb = (
        "/* 多文件版：开发者侧栏惰性构建（DEV 数据按需加载） */\r\n"
        "var DEV_SB=null;\r\n"
        "function buildDevSb(){\r\n"
        "  if(DEV_SB!==null) return DEV_SB;\r\n"
        "  if(!DEV) return '';\r\n"
        + inner
        + "\r\n  DEV_SB=h; return h;\r\n}\r\n"
    )
    shell = shell[:s] + new_dev_sb + shell[e:]

    # 5) 开发者索引：加载期 if(DEV) -> buildDevIndexes()
    s = shell.index("var devCatById={}, devGrpById={}, devDocById={};")
    e = shell.index("function devFlatDocs(", s)
    block = shell[s:e]
    if "if(DEV){" not in block:
        print("FAIL: 开发者索引块结构未匹配")
        return 1
    inner = block[block.index("if(DEV){") + len("if(DEV){"): block.rindex("}")]
    inner = inner.rstrip()
    new_idx = (
        "var devCatById={}, devGrpById={}, devDocById={};\r\n"
        "function buildDevIndexes(){\r\n"
        "  if(!DEV) return;\r\n"
        + inner
        + "\r\n}\r\n"
    )
    shell = shell[:s] + new_idx + shell[e:]

    # 6) render：数据未就绪时占位 + 提前返回
    old_guard = "  if(h==='/all'||h==='/tutorial'||/^\\/m\\d+(\\/|$)/.test(h)) ensureTut();"
    if old_guard not in shell:
        print("FAIL: render 守卫未匹配")
        return 1
    new_guard = (
        "  /* 多文件版：教程 / 开发文档按需加载；未就绪先渲染占位，数据到达后自动重渲 */\r\n"
        "  if((h==='/all'||h==='/tutorial'||/^\\/m\\d+(\\/|$)/.test(h)) && !ensureTut()){ renderPending('教程数据加载中…'); return; }\r\n"
        "  if((h==='/dev'||h.indexOf('/dev/')===0) && !ensureDev()){ renderPending('开发者文档加载中…'); return; }"
    )
    shell = shell.replace(old_guard, new_guard, 1)

    # 7) 搜索：数据未就绪时先触发加载（载入后若输入框仍有内容会自动重放）
    old_search = "  ensureTut();  /* R46：搜索读 MODS/ORDER，首次输入时才解析数据 */"
    if old_search not in shell:
        print("FAIL: 搜索守卫未匹配")
        return 1
    shell = shell.replace(
        old_search,
        "  if(!DATA){ ensureTut(); return; }  /* 多文件版：搜索依赖教程数据，首次输入触发加载 */",
        1,
    )

    # 8) 封面：接受外置图片路径（原来是 data:image/ 仅内嵌）
    old_cover = r'/<img\b[^>]*\bsrc="(data:image\/[^"]+)"/i'
    new_cover = r'/<img\b[^>]*\bsrc="(data:image\/[^"]+|assets\/shots\/[^"]+)"/i'
    if old_cover not in shell:
        print("FAIL: firstCoverSrc 正则未匹配")
        return 1
    shell = shell.replace(old_cover, new_cover, 1)

    # 9) 占位渲染 + 预取，插在启动 render() 之前
    idx = shell.rindex("render();")
    extra = (
        "/* ── 多文件版：加载占位 + 入口预取 ── */\r\n"
        "function renderPending(msg){\r\n"
        "  document.body.dataset.view='loading';\r\n"
        "  app.innerHTML='<div class=\"wrap\"><div class=\"empty-ill\"><b>'+esc(msg)+'</b>'\r\n"
        "    +'<span>数据在首次进入对应模块时按需加载，之后由浏览器缓存。</span></div></div>';\r\n"
        "}\r\n"
        "function prefetchTut(){ if(!DATA && _tutState===0) ensureTut(); }\r\n"
        "requestAnimationFrame(function(){ if(!needsTut()) return; ensureTut(); });\r\n"
        "if('requestIdleCallback' in window){ requestIdleCallback(prefetchTut,{timeout:3000}); }\r\n"
        "else { setTimeout(prefetchTut,1800); }\r\n"
        "document.addEventListener('mouseover',function(e){\r\n"
        "  var t=e.target;\r\n"
        "  var a=t&&t.closest?t.closest('a[href=\"#/tutorial\"],a[href=\"#/all\"],a[href=\"#/dev\"],a[href^=\"#/dev/\"],a[href^=\"#/m\"]'):null;\r\n"
        "  if(!a)return;\r\n"
        "  var href=a.getAttribute('href')||'';\r\n"
        "  if(href==='#/dev'||href.indexOf('#/dev/')===0) ensureDev(); else ensureTut();\r\n"
        "},true);\r\n\r\n"
    )
    shell = shell[:idx] + extra + shell[idx:]

    # 10) 去掉两个内联数据块
    shell = shell.replace(m_tut.group(0), "")
    shell = shell.replace(m_dev.group(0), "")
    shell = shell.replace("<!--DEV-DATA:BEGIN-->", "").replace("<!--DEV-DATA:END-->", "")

    # 11) 拆 CSS：内联 <style> 整块 -> assets/site.css + <link rel="stylesheet">
    #     CSS 占 index.html 的 62%（883,647 / 1,418,846 B）。拆出后 HTML 只剩约 535 KB，
    #     HTML 解析更快、样式表可被浏览器独立缓存；字体与图标仍内联在 CSS（data:），
    #     所以部署依旧零外部域名依赖。CSS 里的 url(#id) 是对当前文档的片段引用，
    #     迁入外部样式表后按规范仍解析到同一文档（Chrome/Firefox 实测一致）。
    m_css = re.search(r"<style\b[^>]*>(.*?)</style>", shell, re.S)
    if not m_css:
        print("FAIL: 未找到内联 <style> 块，无法拆分 CSS")
        return 1
    css_text = m_css.group(1)
    (SITE / "assets" / "site.css").write_bytes(css_text.encode("utf-8"))
    shell = shell.replace(m_css.group(0), '<link rel="stylesheet" href="assets/site.css">', 1)

    (SITE / "index.html").write_bytes(shell.encode("utf-8"))
    (SITE / ".nojekyll").write_bytes(b"")

    # ── 自检 ──
    problems = []
    if 'id="tut-data"' in shell or 'id="dev-data"' in shell:
        problems.append("index.html 仍含内联数据块")
    if "<style" in shell:
        problems.append("index.html 仍含内联 <style> 块")
    if 'href="assets/site.css"' not in shell:
        problems.append("index.html 未引用 assets/site.css")
    css_size = (SITE / "assets" / "site.css").stat().st_size
    if css_size < 100000:
        problems.append(f"assets/site.css 体积异常：{css_size} B")
    if "@font-face" not in css_text:
        problems.append("assets/site.css 缺失 @font-face（字体被误删）")
    if 'url("data:font/woff2' not in css_text and "url(data:font/woff2" not in css_text:
        problems.append("assets/site.css 缺失内联 woff2 字体")
    big_inline = [m for m in WEBP_RE.finditer(shell) if len(m.group(1)) > 10000]
    if big_inline:
        problems.append(f"index.html 仍有 {len(big_inline)} 张截图内联（>10KB）")
    if "renderPending" not in shell or "ensureTut" not in shell or "ensureDev" not in shell:
        problems.append("数据层改造点缺失")
    if shell.count("buildDevIndexes") < 2 or shell.count("buildDevSb") < 2:
        problems.append("开发者惰性改造点缺失")
    for p in sorted(SHOTS.glob("*.webp")):
        pass
    if len(list(SHOTS.glob("*.webp"))) != 48:
        problems.append("截图文件数不是 48")
    for ref in set(re.findall(r"assets/shots/[^\"')]+\.webp", shell + tut_js)):
        if not (SITE / ref).exists():
            problems.append("缺文件 " + ref)
            break
    # 外部数据脚本 node --check
    for js in (DATA / "tutorial.js", DATA / "dev-docs.js"):
        r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"node --check 失败：{js.name} {r.stderr[:200]}")

    sizes = {
        "index.html": (SITE / "index.html").stat().st_size,
        "assets/site.css": css_size,
        "data/tutorial.js": (DATA / "tutorial.js").stat().st_size,
        "data/dev-docs.js": (DATA / "dev-docs.js").stat().st_size,
        "assets/shots/*.webp": sum(p.stat().st_size for p in SHOTS.glob("*.webp")),
        "assets/about-wx.jpg": (SITE / "assets" / "about-wx.jpg").stat().st_size,
    }
    print(json.dumps(sizes, ensure_ascii=False, indent=2))
    print(f"截图 {len(list(SHOTS.glob('*.webp')))} 张，落地页首载 = index.html "
          f"{sizes['index.html']:,} B + assets/site.css {css_size:,} B = "
          f"{sizes['index.html'] + css_size:,} B ({(sizes['index.html'] + css_size) / 1048576:.2f} MiB)")
    for p in problems:
        print("FAIL", p)

    meta = {
        "built_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source": {"file": SRC.name, "bytes": len(raw)},
        "sizes": sizes,
        "shots": len(list(SHOTS.glob("*.webp"))),
        "problems": problems,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "site-build.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if problems:
        return 1
    print(f"产物: {SITE}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
