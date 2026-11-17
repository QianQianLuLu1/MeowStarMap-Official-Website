#!/usr/bin/env python3
"""R52 i18n 资源管线（stdlib only）。

三件事：
  --extract  从单文件 HTML 的 T()/TN()/data-i18n* 里抽出「键 → 中文默认值」，写 locales/ui.zh.json
  --check    parity / 空值 / 非法字符 / 教程包占位 / 零外链不变量 / build_site 锚点（只读）
  --write    把 locales/ui.<lang>.json 与 locales/tutorial.en.json 注入 HTML 的 #i18n-* 数据块

为什么中文默认值留在源码里：t(key,'中文') 的第二个参数就是 zh 兜底，zh 分支短路不查表，
所以改造前后中文输出逐字节同文；ui.zh.json 只是「抽取出来的键表快照」，由 --check 保证不漂移。

用法：
    python perf/tools/build_i18n.py --extract
    python perf/tools/build_i18n.py --check
    python perf/tools/build_i18n.py --write
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HTML = ROOT / "Meow Star Map 官网.html"
LOCALES = ROOT / "locales"
LANGS = ["en", "fr", "es", "ru", "ar"]
BI_PREFIX = ("doc.", "gate.", "top.", "tut.", "dev.", "search.", "notice.")

# T('key','中文') / TN('key', 表达式 ,'中文')
RE_T = re.compile(r"(?<![\w.$])T\('([A-Za-z0-9_.]+)','([^']*)'")
RE_TN = re.compile(r"(?<![\w.$])TN\('([A-Za-z0-9_.]+)',[^,]*,'([^']*)'")
# 引擎内部的 t('key','中文')（语言菜单 / 通告）
RE_ENGINE = re.compile(r"(?<![\w.$])t\('((?:lang|notice)\.[A-Za-z0-9_.]+)','([^']*)'")
# 静态节点：data-i18n="key|中文" 等
RE_ATTR = re.compile(r'data-i18n(?:-aria|-title|-ph)?="([A-Za-z0-9_.]+)\|([^"]*)"')


def read_html() -> str:
    with open(HTML, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write_html(s: str) -> None:
    with open(HTML, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def scan_keys(s: str) -> dict:
    """返回 {key: zh_default}；重复键默认值冲突直接报错（防同名不同义）。"""
    out = {}
    conflict = []
    for rx in (RE_T, RE_TN, RE_ENGINE, RE_ATTR):
        for m in rx.finditer(s):
            k, v = m.group(1), m.group(2)
            if k in out and out[k] != v:
                conflict.append((k, out[k], v))
            out.setdefault(k, v)
    for k, v in scan_dynamic(s).items():
        if k in out and out[k] != v:
            conflict.append((k, out[k], v))
        out.setdefault(k, v)
    return out, conflict



def scan_dynamic(s: str) -> dict:
    """动态键：R41 卡片详情（dt.<id>.bN / dt.<id>.link）、R36 配色名（palette.<id>）、
    R38 外观名（look.<id>.n / .d）。这些键在代码里是拼接出来的，静态正则抓不到，
    但译文同样要交付，故从源结构里解析出「键 → 中文默认值」。"""
    out = {}
    i = s.find("  var DATA={")
    if i > 0:
        j = s.find("\r\n  };", i)
        for line in s[i:j].split("\r\n"):
            t = line.strip()
            if ":{b:[" not in t:
                continue
            k = t.split(":", 1)[0].strip("'")
            b0 = t.index("b:[", t.index(":", 1)) + 3
            b1 = t.index("],href:'", b0)
            body = t[b0:b1].strip()
            items = [x.strip().strip("'") for x in body.split("','")] if body else []
            for n, it in enumerate(items, 1):
                out["dt.%s.b%d" % (k, n)] = it
            l0 = t.index("',link:'", b1) + 8
            out["dt.%s.link" % k] = t[l0:t.index("'}", l0)]
    for line in s.split("\n"):
        t = line.strip()
        if "zk:'palette." in t:
            kid = t.split("zk:'palette.", 1)[1].split("'", 1)[0]
            z = t.split("zname:'", 1)[1].split("'", 1)[0]
            out["palette." + kid] = z
        if "lk:'theme." in t:
            tid = t.split("lk:'theme.", 1)[1].split("'", 1)[0]
            out["theme." + tid] = t.split("lz:'", 1)[1].split("'", 1)[0]
            out["theme." + tid + "Next"] = t.split("nz:'", 1)[1].split("'", 1)[0]
        if "nk:'look." in t:
            parts = t.split("nk:'look.", 1)[1]
            lid = parts.split(".", 1)[0]
            nz = t.split("nz:'", 1)[1].split("'", 1)[0]
            dz = t.split("dz:'", 1)[1].split("'", 1)[0]
            out["look.%s.n" % lid] = nz
            out["look.%s.d" % lid] = dz
    return out


def is_bi(key: str) -> bool:
    return any(key.startswith(p) for p in BI_PREFIX)


def load_locale(lang: str) -> dict:
    p = LOCALES / ("ui.%s.json" % lang)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def data_block_span(s: str, block_id: str):
    open_tag = '<script id="%s" type="application/json">' % block_id
    i = s.find(open_tag)
    if i < 0:
        return None, None, None
    body_start = i + len(open_tag)
    body_end = s.find("</script>", body_start)
    return i, body_start, body_end


def cmd_extract() -> int:
    s = read_html()
    keys, conflict = scan_keys(s)
    if conflict:
        print("FAIL 键冲突（同名不同中文默认值）：")
        for k, a, b in conflict[:20]:
            print("  %s: %r vs %r" % (k, a, b))
        return 1
    LOCALES.mkdir(exist_ok=True)
    with open(LOCALES / "ui.zh.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(keys, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    bi = sum(1 for k in keys if is_bi(k))
    print("extracted %d keys (MKT %d / BI %d) -> locales/ui.zh.json" % (len(keys), len(keys) - bi, bi))
    return 0


def cmd_check() -> int:
    s = read_html()
    keys, conflict = scan_keys(s)
    fail = []
    if conflict:
        fail.append("键冲突 %d 处" % len(conflict))
    zh = load_locale("zh") if (LOCALES / "ui.zh.json").exists() else keys
    if set(zh) != set(keys):
        missing = set(keys) - set(zh)
        extra = set(zh) - set(keys)
        fail.append("ui.zh.json 与源码不一致（缺 %d / 多 %d），先跑 --extract" % (len(missing), len(extra)))

    mkt = {k for k in keys if not is_bi(k)}
    bi = {k for k in keys if is_bi(k)}

    for lang in LANGS:
        pack = load_locale(lang)
        if not pack:
            fail.append("ui.%s.json 缺失或为空" % lang)
            continue
        got = set(pack)
        miss = mkt - got
        extra = got - mkt - (bi if lang == "en" else set())
        if miss:
            fail.append("ui.%s.json 缺 MKT 键 %d 个，如 %s" % (lang, len(miss), sorted(miss)[:3]))
        if extra:
            fail.append("ui.%s.json 有多余键 %d 个，如 %s" % (lang, len(extra), sorted(extra)[:3]))
        if lang != "en":
            semi = bi & got
            if semi:
                fail.append("ui.%s.json 出现 BI 键 %d 个（工作区侧只做中英）" % (lang, len(semi)))
        for k, v in pack.items():
            if not isinstance(v, str) or not v.strip():
                fail.append("ui.%s.json %s 为空值" % (lang, k))
            elif "</script" in v or "\u2028" in v or "\u2029" in v or "\x00" in v:
                fail.append("ui.%s.json %s 含非法字符（</script / U+2028/2029 / NUL）" % (lang, k))
            elif "undefined" in v:
                fail.append("ui.%s.json %s 含 undefined" % (lang, k))

    # 教程包占位与图片数量
    tp = LOCALES / "tutorial.en.json"
    if not tp.exists():
        fail.append("tutorial.en.json 缺失")
    else:
        with open(tp, "r", encoding="utf-8") as f:
            tut = json.load(f)
        src = read_html()
        m = re.search(r'<script id="tut-data" type="application/json">(.*?)</script>', src, re.S)
        base = json.loads(m.group(1)) if m else {}
        base_pages = {p["id"]: p for p in base.get("pages", [])}
        base_mods = {x["id"]: x for x in base.get("modules", [])}
        total = 0
        for pid, p in (tut.get("pages") or {}).items():
            want = len(re.findall(r"<img\b", base_pages.get(pid, {}).get("html", "")))
            got = len(re.findall(r"\{\{img\d+\}\}", p.get("html", "")))
            if want != got:
                fail.append("tutorial.en.json %s 图片占位 %d ≠ 原文 %d" % (pid, got, want))
            total += got
        for mid, mm in (tut.get("mods") or {}).items():
            want = len(re.findall(r"<img\b", base_mods.get(mid, {}).get("overview", "")))
            got = len(re.findall(r"\{\{img\d+\}\}", mm.get("overview", "") or ""))
            if want != got:
                fail.append("tutorial.en.json mods.%s 图片占位 %d ≠ 原文 %d" % (mid, got, want))
            total += got
        if total != 48:
            fail.append("tutorial.en.json 图片占位总数 %d ≠ 48" % total)
        if len(tut.get("pages") or {}) != len(base_pages):
            fail.append("tutorial.en.json 页数 %d ≠ 原 %d" % (len(tut.get("pages") or {}), len(base_pages)))

    # 零外链与字体不变量
    if s.count("@font-face{") != 2:
        fail.append("@font-face{ 计数 %d ≠ 2" % s.count("@font-face{"))
    if len(re.findall(r'<link\b(?![^>]*href="data:)', s)):
        fail.append("存在非 data: 的 <link>")
    if "<script src" in s:
        fail.append("存在 <script src")
    if "url(http" in s:
        fail.append("存在 url(http)")

    # build_site.py 锚点
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
    for a in anchors:
        if a not in s:
            fail.append("build_site 锚点缺失：%s" % a[:50])

    # 数据行未被触碰
    # 口径与 r45 A7 一致：整行长度（含 script 标签前后缀），不是 JSON 载荷长度
    sizes = {}
    for name, marker in (("tut", 'id="tut-data"'), ("dev", 'id="dev-data"')):
        hit = [ln for ln in s.split("\n") if marker in ln and len(ln) > 100000]
        sizes[name] = len(hit[0].rstrip("\r")) if hit else -1

    print("keys=%d (MKT %d / BI %d) packs=%s data=%s" % (len(keys), len(mkt), len(bi), LANGS, sizes))
    if sizes != {"tut": 21358276, "dev": 1545974}:
        print("WARN 数据行长度与 R50 基线不同（若本轮确实动过数据行请更新本口径）：%s" % sizes)
    if fail:
        print("FAIL %d 项：" % len(fail))
        for x in fail:
            print("  -", x)
        return 1
    print("OK 全部检查通过")
    return 0


def cmd_write() -> int:
    s = read_html()
    before = hashlib.sha256(
        (re.search(r'<script id="tut-data" type="application/json">(.*?)</script>', s, re.S).group(1) +
         re.search(r'<script id="dev-data" type="application/json">(.*?)</script>', s, re.S).group(1)).encode("utf-8")
    ).hexdigest()
    n = 0
    for lang in LANGS:
        pack = load_locale(lang)
        if not pack:
            print("FAIL ui.%s.json 为空，先写译文" % lang)
            return 1
        i, a, b = data_block_span(s, "i18n-%s" % lang)
        if i is None:
            print("FAIL 找不到 #i18n-%s 数据块" % lang)
            return 1
        payload = json.dumps(pack, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload = payload.replace("</script", "<\\/script").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        s = s[:a] + payload + s[b:]
        n += 1
    tp = LOCALES / "tutorial.en.json"
    if not tp.exists():
        print("FAIL tutorial.en.json 缺失")
        return 1
    with open(tp, "r", encoding="utf-8") as f:
        tut = json.load(f)
    payload = json.dumps(tut, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload = payload.replace("</script", "<\\/script").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    i, a, b = data_block_span(s, "i18n-tut-en")
    if i is None:
        print("FAIL 找不到 #i18n-tut-en 数据块")
        return 1
    s = s[:a] + payload + s[b:]
    after = hashlib.sha256(
        (re.search(r'<script id="tut-data" type="application/json">(.*?)</script>', s, re.S).group(1) +
         re.search(r'<script id="dev-data" type="application/json">(.*?)</script>', s, re.S).group(1)).encode("utf-8")
    ).hexdigest()
    if before != after:
        print("FAIL 数据行被改动了，拒绝写盘")
        return 1
    write_html(s)
    print("wrote %d UI packs + tutorial.en (bytes=%d)" % (n, len(s.encode("utf-8"))))
    return 0


def main(argv) -> int:
    cmd = argv[1] if len(argv) > 1 else "--check"
    if cmd == "--extract":
        return cmd_extract()
    if cmd == "--check":
        return cmd_check()
    if cmd == "--write":
        return cmd_write()
    print("用法：build_i18n.py [--extract|--check|--write]")
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv))
