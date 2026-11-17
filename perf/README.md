# perf — 加载性能与网络速度优化（R50 · 20261116）

本目录是从 `main` 新建的 `性能/极速加载` 分支的性能工作区。结论先行：

| 产物 | 首屏传输 | 相对 main |
|---|---|---|
| `main` 单文件（PNG，34.85 MB） | **34.85 MB** | 100% |
| 单文件版（PNG → **无损 WebP**） | **24.98 MB** | −28.3% |
| 多文件版 `site/`（推荐线上部署） | **1.19 MB**（gzip 684 KB / brotli 644 KB） | **−96.6%** |

*「清晰度不变」按**逐像素相同**兑现*：48 张教程截图以 WebP **lossless** 编码，
解码后与 PNG 的 RGB 逐像素完全一致（48/48 复核通过），不是「肉眼不可辨」的有损近似。

---

## 一、做了什么

### 1. 单文件版：PNG → 无损 WebP

- 48 张 1400×900 教程截图：`23,165,937 B`（22.09 MiB PNG）→ `15,991,294 B`（15.25 MiB WebP lossless）。
- 整文件：`34,547,054 B`（分支基线）→ **`24,980,902 B`（23.82 MiB）**；相对 `main` 的
  `34,851,151 B` 降 **28.3%**。
- 只换图片载荷：`#tut-data` 之外的 head / tail **逐字节不变**；JSON 去掉载荷后结构等价；
  零外链不变量（`<link>` 2 枚 data: / `<script src>` 0 / `<iframe>` 0 / 外链 img 0 /
  `url(http)` 0 / `@font-face` 2 / `<img>` 53 / `<style>` 1）逐项不变。
- 另含 R46（教程数据惰性解析）、R48（截图 `loading="lazy"` + `decoding="async"`）、
  R49（Inter 子集化 352 KB → 119 KB）三项已在分支内的前置优化。

### 2. 多文件版 `site/`：为「网络加载速度」做的架构优化

单文件版无论怎么压，打开时仍要把全部图片和教程数据下载完；`site/` 把这些资产拆开并按需加载：

| 资产 | 体积 | 何时加载 |
|---|---|---|
| `site/index.html`（shell + CSS/JS + 字体 + 图标） | **1,186,206 B（1.13 MiB）** | 首屏，唯一阻塞资源 |
| `site/data/tutorial.js` | 69,450 B | 进入教程路由；空闲时预取 |
| `site/data/dev-docs.js` | 2,088,814 B | 首次进入 `#/dev` |
| `site/assets/shots/*.webp`（48 张） | 15,991,294 B | 每页 1–3 张；`loading="lazy"` |
| `site/assets/about-wx.jpg` | 238,007 B | 打开「关于 → 微信」时（懒加载） |

关键点：

- **落地页不再为 30.9 MB 教程数据付费**；`#/` 首屏只有 1.19 MB（含内联字体），
  比单文件版少 **27.5×**。
- 数据外置为 **classic script**（`window.__TUT__` / `window.__DEV__`），不用 `fetch`/module，
  所以 `file://` 双击仍然完整可用，没有 CORS 问题。
- 路由按需加载 + 加载完成自动重渲；入口 hover 预取；空闲时预取教程数据（搜索与封面依赖它）。
- 截图改为独立 `.webp` 文件，`#/all` 连续阅读也真正惰性加载：打开 `#/all` 只请求视口附近
  3 张图，而不是 48 张。
- 关于板块的微信二维码（317 KB base64 JPEG）外置 + `loading="lazy"`，不再进入首屏。

---

## 二、实测（Chromium 147 headless · 本地 HTTP · 无压缩）

同机、同浏览器、`reducedMotion=reduce`：

| 场景 | 传输字节 | 请求数 | 截图请求 | FCP | DCL | load |
|---|---|---|---|---|---|---|
| 原始单文件 · 落地页 | 34,547,054（32.95 MiB） | 1 | 0 | 332 ms | 1036 ms | 1047 ms |
| **site · 落地页** | **1,255,656（1.20 MiB）** | 2 | 0 | **112 ms** | **226 ms** | **230 ms** |
| 原始单文件 · 教程正文页 | 34,547,054 | 1 | 0 | 88 ms | 1127 ms | 1161 ms |
| **site · 教程正文页** | **1,277,720（1.22 MiB）** | 3 | 1（22 KB） | 96 ms | **120 ms** | **226 ms** |
| site · `#/all` 连续阅读 | 2,702,346（2.58 MiB） | 5 | 3 / 48 | 92 ms | 121 ms | 385 ms |
| site · `#/dev` | 3,344,470（3.19 MiB） | 3 | 0 | 116 ms | 140 ms | 311 ms |

> 落地页的 1.20 MiB = `index.html` 1.13 MiB + 空闲预取的 `tutorial.js` 68 KB。
> 教程数据预取是为搜索/封面服务的有意取舍；如果只算首屏阻塞资源，就是 1.13 MiB。

带宽换算（仅下载时间，不含 TTFB）：

| 带宽 | main 34.85 MB | 单文件无损版 24.98 MB | site 落地页 1.20 MiB | site 落地页 + gzip 700 KB |
|---|---|---|---|---|
| 10 Mbps | 27.9 s | 20.0 s | **1.00 s** | **0.56 s** |
| 50 Mbps | 5.6 s | 4.0 s | 0.20 s | 0.11 s |
| 100 Mbps | 2.8 s | 2.0 s | 0.10 s | 0.06 s |

压缩后体积（服务端开启 gzip/brotli 即可）：

| 文件 | 原始 | gzip -9 | brotli q11 |
|---|---|---|---|
| `site/index.html` | 1,186,206 | 684,124 | 644,292 |
| `site/data/tutorial.js` | 69,450 | 17,057 | 14,434 |
| `site/data/dev-docs.js` | 2,088,814 | 479,740 | 330,422 |
| 单文件版 | 24,980,902 | 17,554,904 | —（base64 + WebP 熵高，收益有限） |

---

## 三、目录与用法

```
perf/
  README.md               本文件
  requirements.txt        Pillow（工具链唯一依赖）
  .gitignore              assets/ dist/ 不入库
  tools/
    common.py             源文件切分 / 截图枚举 / 体积工具
    extract_shots.py      从 #tut-data 提取 48 张 PNG 原图 → assets/shots
    convert_shots.py      PNG → WebP lossless（method=6, exact）+ 逐像素复核；可选 q95 对照
    build_lossless.py     无损 WebP 重建单文件（默认写 dist/，--in-place 覆盖源文件）
    build_site.py         生成多文件版 site/（数据外置、按需加载、懒加载、预取）
    compare_shots.py      三份截图的逐像素对比（orig / lossless / site）
    smoke_site.mjs        10 路由功能签名对比（原文件 vs site，file://）
    interact_site.mjs     site/ 真实点击交互 + 390 移动端溢出
    measure_network.mjs   传输字节 / FCP / DCL 实测（需本地 HTTP 服务）
    shoot_compare.mjs     8 个场景截图取证（图片加载完成后）
  assets/                 [gitignored] 原图、WebP、截图证据
  dist/                   [gitignored] 无损单文件构建产物
  reports/                [入库] 构建元数据、网络实测、截图差异、探针日志
site/                     多文件版产物（入库）
```

重建：

```bash
pip install -r perf/requirements.txt
python perf/tools/extract_shots.py        # 从单文件提取 48 张 PNG
python perf/tools/convert_shots.py        # 无损 WebP + 48/48 逐像素复核
python perf/tools/build_lossless.py --in-place   # 单文件版（会把源文件换成 25 MB 版）
python perf/tools/build_site.py           # 多文件版 → site/

# 本地预览（HTTP 推荐，gzip/brotli 由服务器负责）
python -m http.server 8080
# 打开 http://localhost:8080/site/index.html
# 离线：直接双击 site/index.html 也可用（字体/图标内联，数据用 classic script）
```

---

## 四、验证

| 项 | 结果 |
|---|---|
| 48 张 WebP 解码后与 PNG 逐像素对比 | **48/48 完全一致**（PSNR = ∞） |
| 单文件结构 | head/tail 逐字节相同；JSON 去载荷后结构等价；CRLF 5058 不变 |
| 单文件不变量 | link 2(data:) / script src 0 / iframe 0 / 外链 img 0 / url(http) 0 / @font-face 2 / img 53 / style 1 |
| 22 个 JS 块 | `node --check` 全通过 |
| html5lib strict | **NOT-RUN**：25 MB 文件上 strict 解析在本机 >20 分钟无结果；`--skip-w3c` 跳过。结构等价另由「head/tail 逐字节相同 + JSON 去载荷深比对 + 22 JS 块编译」三项覆盖 |
| 10 路由功能签名（view / title / h1+h2 / links / imgs / textLen / sidebar / broken） | 原文件 vs `site/` **逐项相同**，console / pageerror / requestfailed 全 0（file://） |
| `site/` 交互（真实点击） | 9/9：hero → 身份门 → 用户 → 教程首页（8 封面加载）→ 模块卡 → 详情页（截图懒加载）→ 搜索 → 资源下载面板 → 主题明暗切换（刷新持久化）→ 微信二维码懒加载；`file://` 与 HTTP 均通过 |
| `site/` 移动端 | 7 路由 × 390px：文档级横向溢出 **0px**（`perf/tools/interact_site.mjs`） |
| 截图（8 场景 × 3 产物，1440/390、浅/深） | `orig` vs `lossless`、`orig` vs `site` **16/16 PASS**：10 项逐像素完全相同；6 项为 ≤2/255 的文字抗锯齿 / 合成层抖动（无布局、无文案、无图片区域差异，肉眼不可辨），见 `reports/shots-diff.json` |
| 仓库探针 | r37 32 PASS / 1 FAIL（F2 已知，见下）/ 2 NOT-RUN；r38 27 PASS / 1 FAIL（U5 **在 main 原件上复现**，环境问题）/ 2 NOT-RUN；r39 23/0/1；r41 25/25；r42 39/39；r43 25/0/1；r45（`--skip-slow`）65/65。日志见 `reports/probes/*.txt`。本轮只改了两处探针口径：`r45 A7` 的冻结行长度（tut 30924428 → 21358276）、`r43 A6` 改为按**母图载荷本体**计数（原「全文件仅 1 处 webp data URI」在截图 WebP 化后必然变成 49 处） |
| 已知探针差异 | **r37 F2**：`light\|#/` 与 `light\|#/identity` 的 `sidebarLinks` 47 → 130，是 R46 惰性侧栏的既有差异（同文档 hash 导航残留状态，0/47/130 随探针顺序变化），非 R50 引入；**r38 U5**：`--skip-w3c` 下 scroll 关闭 look-menu 未触发，把 `main` 原件换回后同样 FAIL（`reports/probes/r38-main-baseline.txt`），属 Chrome 147 环境时序问题 |

---

## 五、已知限制 / 未做

1. **单文件版仍是 25 MB**：`file://` 双击打开时，Chrome 要把 21.3 MB 的 base64 数据行解析完
   才执行主脚本。真正把首屏做到 1 MB 的是 `site/`；单文件版保留为「离线单文件」交付形态。
2. **`#/dev` 仍一次加载 2.0 MB 开发文档**：可再拆成「目录 + 按文档加载」，本轮未做。
3. **`site/` 的缓存完全依赖服务器配置**：文件名未带内容哈希；建议对 `/assets/*` 设长缓存，
   `/index.html` 与 `/data/*` 设短缓存并开启 gzip/brotli。
4. 字体仍内联在 `index.html`（647 KB base64）：保证 `file://` 下字体也能加载；如果只做 HTTP
   部署，可以外置成 `.woff2` 再省约 0.5 MB 首屏（需接受 file:// 下回退系统字体）。
5. 没有做 AVIF/JXL 对比：AVIF lossless 的浏览器门槛更高（Safari 16.4+），且本机缺编码器；
   WebP lossless 已满足「零画质损失」且兼容面更宽。

## 六、回滚

- 单文件版：`git checkout main -- "Meow Star Map 官网.html"`。
- 多文件版：删除 `site/` 与 `perf/` 即可（`perf/assets`、`perf/dist` 本就不入库）。
- 测试：`git checkout main -- tests/r45_theme_scope_check.py`。
