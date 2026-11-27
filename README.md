# Meow Star Map 官网（MeowStarMap-official-website）

「喵星图（Meow Star Map）」的官方网站：产品介绍 + 全流程使用教程 + 开发者文档，三合一的**单文件静态站点**。喵星图是一款面向《无限暖暖》的桌面媒体管理工具，软件本体见 [QianQianLuLu1/MeowStarMap](https://github.com/QianQianLuLu1/MeowStarMap)。

> **当前基线 R57（20261126）**：在保留单文件自包含交付的同时，提供多文件线上版与六语国际化。
>
> - **单文件版** `Meow Star Map 官网.html`：**25,214,383 B（24.05 MiB）**。48 张教程截图为**无损 WebP**（逐像素等同原 PNG），另内嵌六语词典与 i18next 23.16.8 运行时（MIT）。
> - **多文件版** [`site/`](site/)：落地页 **1,419,718 B（1.35 MiB）**（`index.html` 535,326 + `assets/site.css` 884,392），教程数据、开发者文档、48 张截图按需加载。
> - **六语 i18n**（zh / en / fr / es / ru / ar）：译文唯一编辑入口是 [`locales/`](locales/README.md)，由 `perf/tools/build_i18n.py` 单向注入。
>
> 逐轮变更与验收记录见 [AGENTS.md](AGENTS.md)。

- 本仓库：<https://github.com/QianQianLuLu1/MeowStarMap-Official-Website>（已推送，`main` 与 `origin/main` 一致）
- 线上地址：尚未公开部署地址；本地 HTML 文件即完整站点（`site/` 已按 GitHub Pages 就绪，含 `.nojekyll`）
- 软件仓库：<https://github.com/QianQianLuLu1/MeowStarMap>
- 软件下载：软件仓库 [Releases](https://github.com/QianQianLuLu1/MeowStarMap/releases)，或站内「资源下载」面板（迅雷 / 百度 / 移动云盘）

## 项目是什么

整个站点只有一个源文件 `Meow Star Map 官网.html`（25,214,383 B / 5,750 行 / CRLF），包含全部 HTML / CSS / JS，以及内联的教程与开发者文档数据、六语词典、字体子集、图标与封面图。**无构建工具、无框架、零外部资源请求**——所有资源以 `data:` 内联，离线双击即可完整运行。

`site/` 是同一份站点的**多文件线上版**（由 `perf/tools/build_site.py` 生成）：外壳 1.35 MiB，教程数据、48 张截图、开发者文档拆成独立文件按需加载。它放弃「单文件」形态，换取首屏传输从 24.05 MiB 降到 1.42 MiB（含空闲预取的教程数据）；单文件版仍保留作为离线交付。

站点通过 hash 路由组织五级界面（详见 [AGENTS.md](AGENTS.md)「五级界面架构」与「路由速查」）：

| 入口 | 内容 |
|------|------|
| `#/` | 一级首页：产品介绍、资源下载、关于 |
| `#/features` / `#/resonance` / `#/privacy` / `#/download` / `#/download/start` | 产品介绍二级页与「开始使用」三级页 |
| `#/identity` | 身份选择门（用户 / 开发者分流） |
| `#/tutorial`、`#/mX`、`#/mX/mYpZ`、`#/all` | 用户教程：首页 / 模块 / 详情 / 连续阅读 |
| `#/dev`、`#/dev/...` | 开发者工作台与文档 |

当前基线为 R55：明暗主题 × 三态外观（中性黑白 / 彩色氛围 / 极简全白）× landing 四套配色主题，Bento Grid 布局，全套动效支持 `prefers-reduced-motion` 降级，禁 JS 不破版；R52 起营销侧提供六语，工作区侧提供中英双语。逐轮变更与验收记录见 [AGENTS.md](AGENTS.md)。

## 本地运行

无需安装任何依赖、无需构建：

1. 直接用浏览器打开 `Meow Star Map 官网.html` 即可（`file://` 协议完整可用，这是项目的验收契约之一）。
2. 线上部署请用多文件版 `site/`（落地页 1.35 MiB，教程图片按需加载）：
   `python perf/tools/build_site.py` 重新生成，或直接部署已入库的 `site/`。
3. 如需 HTTP 方式访问单文件版，在本目录任选一种静态服务器即可，例如：

   ```bash
   python -m http.server 8080
   # 单文件版：http://localhost:8080/Meow%20Star%20Map%20官网.html
   # 多文件版：http://localhost:8080/site/index.html
   ```

单文件版约 24 MiB，首次打开的解析耗时属正常现象；多文件版首屏只下载 1.42 MiB。

## 测试（回归探针）

`tests/` 内是常驻回归探针，Python + Playwright 驱动，`file://` 直开、无端口自起。环境要求：Python ≥ 3.8、Node（探针内用 `node --check` 编译校验 JS 块）。装配：

```bash
pip install playwright html5lib
playwright install chromium
```

> 版本锁定口径：根目录 `requirements.txt` 属于父仓库工具链，本工作树未纳入；以上两个包即探针的全部第三方依赖。工具链自带的第三方依赖只有 `perf/requirements.txt`（Pillow，用于无损 WebP 与截图处理）。

运行（在本目录直跑，**不建 venv**，与 AGENTS.md 既有口径一致）：

| 探针 | 覆盖内容 |
|------|---------|
| `python tests/r37_bento_check.py` | Bento Grid 布局 / 配色 / 圆角 / 零外链 / 功能基线比对（`--baseline` 落基线，`--skip-w3c` 跳慢检） |
| `python tests/r38_visual_check.py` | 三态外观 / 菜单 / AA 对比度 / 多路由溢出（`--skip-w3c`、`--skip-browser-fallback`） |
| `python tests/r39_type_check.py` | 苹果式排版阶梯（支持 `--baseline-json` / `--compare-json`） |
| `python tests/r41_cards_detail_check.py` | landing 卡片行尾详情展开（`--skip-slow`） |
| `python tests/r42_migration_check.py` | 二级页内容迁移零丢失 / GitHub 入口 / 断点矩阵（`--skip-slow`） |
| `python tests/r43_icon_check.py` | 软件图标单点内联 / 六槽位几何 / 溢出矩阵（`--skip-slow`） |
| `python tests/r45_theme_scope_check.py` | landing 暗底舞台色彩作用域 / AA / 折叠配色入口（`--skip-slow`） |
| `python tests/r51_i18n_check.py` | 六语 i18n：源码级 / 运行时级 / 六语 × 四断点溢出 |
| `python tests/r54_nav_actions_check.py` | 常驻导航七入口：单行 / 不裁切 / 不重叠 / 文字边缘距 / 路由可滚 |

各探针的完整用法与口径见脚本头部注释；未跑项显式记 NOT-RUN，不当作通过。`tests/i18n_pin.py` 是探针共用的语言钉住辅助模块（把 `__i18nPin` 钉为 zh，保证确定性）。`tests/r37-baseline.json`、`tests/r39-baseline.json` 等基线 JSON 与 `tests/*-shots/` 截图归档是有意纳入版本管理的验收证据，勿删。

> AGENTS.md 中描述的 `npm run setup/doctor/smoke/vreg`、Makefile 入口与 r14–r31 历史探针属于**父仓库工具链**，本工作树不存在这些文件，相应命令在此不可用。

## 性能与构建工具链

`perf/` 收录全部构建与取证脚本（第三方依赖仅 Pillow，见 `perf/requirements.txt`）：

| 脚本 | 用途 |
|---|---|
| `perf/tools/build_i18n.py` | 六语 i18n：`--extract` 抽键表快照 → `--check` 校验 parity / 零外链 / 占位 → `--write` 注入单文件 |
| `perf/tools/build_site.py` | 由单文件生成多文件版 `site/`（数据外置、按需加载、懒加载、预取） |
| `perf/tools/extract_shots.py` | 从 `#tut-data` 提取 48 张 PNG 原图 → `perf/assets/shots` |
| `perf/tools/convert_shots.py` | PNG → WebP lossless（`method=6, exact`）+ 逐像素复核 |
| `perf/tools/build_lossless.py` | 无损 WebP 重建单文件（默认写 `dist/`，`--in-place` 覆盖源文件） |
| `perf/tools/compare_shots.py` | 三份截图逐像素对比（orig / lossless / site） |
| `perf/tools/smoke_site.mjs` | 10 路由功能签名对比（原文件 vs `site/`，`file://`） |
| `perf/tools/interact_site.mjs` | `site/` 真实点击交互 + 390 移动端溢出 |
| `perf/tools/measure_network.mjs` | 传输字节 / FCP / DCL 实测（需本地 HTTP 服务） |
| `perf/tools/shoot_compare.mjs` | 8 个场景截图取证（图片加载完成后） |

重建顺序（先 i18n、后建站，否则 `site/` 会缺词典）：

```bash
pip install -r perf/requirements.txt
python perf/tools/build_i18n.py --check     # 校验译文与锚点
python perf/tools/build_i18n.py --write     # 注入单文件
python perf/tools/build_site.py            # 再生 site/
```

`perf/assets/`、`perf/dist/` 为可重建产物，已 gitignore；`perf/reports/`（构建元数据、网络实测、截图差异、探针日志）入库。

## 技术要点与硬契约

改动本站前请先读 [AGENTS.md](AGENTS.md) 与 [CONTRIBUTING.md](CONTRIBUTING.md)。核心契约：

- **单文件自包含**：不新增外部资源文件与外链资源（`<link>`（非 `data:`）/ `<script src>` / 外链 img / `iframe` / `url(http)` 恒为 0，探针守护）。
- **零外链不变量**：同上；图标 link 恰 2 枚且均 `data:`，`@font-face{` 恰 2 处且均 `data:`（注意裸词 `@font-face` 全文会出现 3 次——第 3 次在 R36 注释文本里，探针按 `@font-face{` 计数）。
- **两条巨型数据行严禁随意触碰**：`#tut-data`（行 L2723，21,358,276 字符）/ `#dev-data`（行 L2724，1,545,974 字符）内嵌教程与开发者文档 JSON，路由内链与数据解耦。R50 只对 `#tut-data` 做图片载荷的等位置换（PNG → 无损 WebP），JSON 结构与其余字符不变；R52 起另新增 `#i18n-*` 词典块（`#i18n-en/fr/es/ru/ar` + `#i18n-tut-en`），由 `build_i18n.py` 维护、勿手改。
- **注释对回滚机制**：各轮改动以 `RNN:BEGIN/END` 注释对组织，可独立回滚；定位一律用 grep 锚点，行号随轮次漂移。
- **中文字体子集**：内嵌 Noto Sans SC 按站点字符子集化，**新增可见中文文案须再子集化**（流程见 AGENTS.md「R36 勘误」）；新增西文/西里尔/阿拉伯文超出 Inter 子集（381 码位）时按字形回落系统字体。
- **主题与偏好存于浏览器 `localStorage`**（`nikki_theme` / `nikki_look` / `nikki_lp_theme` / `nikki_role` / `nikki_lang`），站点不收集、不上传任何用户数据。

## 目录结构

```
Meow Star Map 官网.html   单文件站点（全部 HTML / CSS / JS / 数据 / 六语词典 / 字体 / 图标；48 张截图为无损 WebP）
site/                     多文件线上版（build_site.py 生成：外壳 + 按需加载的数据/图片 + 词典内联）
locales/                  六语译文（唯一编辑入口：ui.{en,fr,es,ru,ar}.json + tutorial.en.json + ui.zh.json 键表快照）
perf/                     性能与构建工具链（build_i18n / build_site / 无损 WebP / 取证脚本）+ reports/
tests/                    常驻回归探针（r37–r54）+ 基线 JSON + 截图归档 + 校验报告
AGENTS.md                 常驻开发者文档：章节索引、逐轮勘误、开发约定、回滚方式
README.md                 本文件
LICENSE                   授权（MIT）
CONTRIBUTING.md           贡献指引（提炼自 AGENTS.md 既有约定）
SECURITY.md               安全问题披露指引
CODE_OF_CONDUCT.md        行为准则
.github/                  Issue / PR 模板
```

## 第三方资产与授权

站点内嵌了以下第三方资产，**各自保留其原许可证**（依据源文件内注释）：

| 资产 | 来源 | 许可证 |
|------|------|--------|
| GSAP 3.13.0（核心 + ScrollTrigger） | GreenSock | [GreenSock Standard License](https://gsap.com/standard-license) |
| i18next 23.16.8（UMD 内嵌） | i18next（unpkg `i18next@23.16.8`） | MIT |
| Inter v4.1 可变字体（base64 内嵌） | rsms/inter | SIL OFL 1.1 |
| Noto Sans SC 可变字体子集（base64 内嵌） | google/fonts（ofl/notosanssc） | SIL OFL 1.1 |
| Feather v4.29.2 图标（内联 SVG） | feathericons.com | MIT |
| 网盘图标图形 | [Arcticons](https://github.com/Donnnno/Arcticons) | CC BY-SA 4.0（本表即署名；图形副本以相同许可提供） |
| QQ / 微信 / 抖音图标字形 | [Simple Icons](https://github.com/simple-icons/simple-icons)（tencentqq / wechat / tiktok，路径经逐字比对核实） | CC0 1.0（图标公有领域；品牌商标归原权利方，使用时须尊重） |
| GitHub 图标 | [Octicons](https://github.com/primer/octicons) mark-github-16 | MIT |

本项目自身代码采用 [MIT](LICENSE) 许可证（版权行 QianQianLuLu1，经项目所有者确认）。第三方资产的许可证不受本项目 LICENSE 覆盖；再分发时请保留 Arcticons 图形的署名与 CC BY-SA 4.0 许可声明。

## 贡献与联系

- 改动前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；安全问题见 [SECURITY.md](SECURITY.md)；协作请遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
- 译文改动请走 [`locales/README.md`](locales/README.md) 的单向流程，不要手改单文件里的 `#i18n-*` 块。
- 问题反馈：按 `.github/` 内 Issue 模板提交；也可经站内「关于」板块的社交入口（QQ 群 / 微信 / 抖音）联系。
- 维护者：[QianQianLuLu1](https://github.com/QianQianLuLu1)（GitHub 主页）；安全问题请走 [SECURITY.md](SECURITY.md) 的私下披露渠道。
