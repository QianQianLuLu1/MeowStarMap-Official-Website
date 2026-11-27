# AGENTS.md — Meow Star Map 开发者网页

## 全局执行约束（所有任务必读）

本节规定所有任务的执行与验收流程，不得据此放宽单文件离线自包含、零外链、数据/词典保护等既有硬契约。纯文档改动不涉及站点验收项时，须明确写“不适用”及原因，不得静默跳过。

### 一、改动范围

- 最小化改动：只修改与本次需求直接相关的文件，禁止顺手重构或修改无关代码。
- 优先检索 GitHub 等成熟开源实现，避免重复造轮子；采用方案仍须遵守项目硬契约。必须自行实现时，代码量压到最低，优先复用项目内已有样式、模板和脚本。
- CDN/外链资源默认禁止。只有先修订硬契约，并取得用户对具体 URL、锁定版本及离线影响的明确批准，才可引入；计划声明不等于批准。无新增依赖时写“无”。

### 二、先出计划，再动手

动手前先输出 Markdown 实施计划，至少包含：

1. **依赖声明**：新增 CDN（默认“无”；特批时列完整 URL 和锁定版本）、第三方依赖、本地文件引用及定位锚点。
2. **打开方式**：注明直接打开或本地服务器及具体操作。单文件版可直接以 `file://` 打开 `Meow Star Map 官网.html`；需要 HTTP 时在仓库根目录运行 `python -m http.server 8080`，访问 `http://localhost:8080/site/index.html`。
3. **兼容性**：写明目标浏览器/引擎及最低版本。项目整体最低要求为 Safari 15.4（`:has()`）；WebP 单独要求 Safari 14+，但不降低整体下限。Chrome/Edge/Firefox 须记录本次实测版本，未实测不宣称支持；真实 iOS/Safari 未实测时如实注明。响应式直接引用本文「响应式断点」及其审计视口，不重复维护。
4. **表单/交互校验**：只写真实存在的必填项、格式规则和错误提示文案；无表单时写“表单：不适用”，不得编造校验规则。
5. **验收清单**：逐条列出可手动验证的功能点、预期结果和验证环境。

### 三、分步验证

- 每完成一个功能模块，输出该模块的完整可运行代码、集成位置及验证结果，并确认无语法错误；涉及 JS 逻辑时附 console 测试或简单断言，并执行变更 JS 块的 `node --check`。
- “完整可运行代码”以集成后的唯一源文件为准；回复中给出本次模块的完整代码或精确 diff，不重复粘贴整文件及未修改的数据、字体载荷，不另建多份 HTML/站点副本。

### 四、质量检查

- 按本文「环境装配与工具链」执行 `python perf/tools/build_i18n.py --check`、变更 JS 块的 `node --check` 和受影响探针；跳过项显式记 NOT-RUN，交付前补跑，NOT-RUN 不算通过。
- 修改 HTML 时优先进行 W3C HTML 校验，HTML 错误必须为 0。在线 W3C Nu 因原文件体积或超时无法使用时，校验仅剥离 `#tut-data`/`#dev-data` 及字体 base64 的结构副本并明确标注，同时用 html5lib strict 检查原件；结构副本不替代原件，既有 CSS 校验误报须单独说明。
- 新增或修改的外部资源及出站链接逐项检查可访问性、状态码和最终跳转；外部资源默认禁止，`data:` 内联资源豁免，并用既有零外链探针复核。
- 用现有 Playwright 探针核查目标路由与视口的 console error、pageerror、requestfailed，三者均为 0 才算通过。
- 纯文档、配置或不涉及 HTML/JS 的改动，对应站点验收项写“不适用”及原因，不声称已执行。

### 五、禁止事项

- 不得引用不存在的 CDN 地址或本地文件路径；计划引用先核验。
- 不得使用未声明、未获批准的外部依赖；无依赖时明确写“无”。
- 不得跳过兼容性说明，不得不适用项静默留空。
- 不得手改 `#tut-data`、`#dev-data` 或 `I18N-DATA`，不得新增 npm/Make 平行入口。

## 当前基线与仓库边界

- 当前基线：**R59**。R56 起 `site/` 的样式表外置为 `assets/site.css`；R57 页脚备案号；R58–R59 的彩色视觉（背景流光 `#r58-flow` + 玻璃卡）只挂 `html[data-look="color"]`，中性/极简保持原样。站点本体为原生 HTML/CSS/JavaScript，无框架、无包管理器入口；Python/Node 仅用于构建、i18n 与验收工具链。
- 仓库根：`MeowStarMap-Official-Website/`。当前 `main` 的已提交 HEAD 与 `origin/main` 同步；工作树可能有未提交文档改动，以 `git status` 为准。
- 单文件源：`Meow Star Map 官网.html`，当前 **25,219,808 B / 5,842 个 CRLF 换行**，内嵌全部 HTML/CSS/JS、教程与开发者数据、六语词典、字体子集、图标和 48 张无损 WebP 截图。
- 多文件线上版：`site/index.html` **534,863 B（522.3 KiB）** + `site/assets/site.css` **890,319 B（869.5 KiB）**，由 `perf/tools/build_site.py` 从单文件源生成；教程/开发者数据与截图按路由加载。
- 教程数据：9 模块、36 页、48 张图；开发者文档：12 板块、12 子分类、104 篇。
- i18n：359 键（MKT 272 / BI 87）；营销侧 zh/en/fr/es/ru/ar，工作区侧 zh/en，开发者文档正文永久不译。
- 本仓库现有 `.md` 共 **10 份**；临时计划、逐轮报告和一次性取证产物不入库。

## 目录、工具链与探针

```text
Meow Star Map 官网.html  单文件站点源
site/                    多文件线上版（build_site.py 生成）
  index.html              应用 shell；CSS 外链 assets/site.css，JS/字体/图标/词典内联
  assets/site.css         全站样式（字体子集与图标仍以 data: 内联在此文件）
  data/tutorial.js        教程数据（截图为相对路径）
  data/dev-docs.js        开发者文档数据
  assets/shots/*.webp     48 张 1400×900 无损 WebP
  assets/about-wx.jpg     微信二维码
  .nojekyll / README.md
locales/                 六语译文唯一编辑入口
  ui.zh.json              键表快照（build_i18n.py --extract 生成，勿手改）
  ui.{en,fr,es,ru,ar}.json 译文
  tutorial.en.json        教程英文包
  README.md              翻译流程与键归属
perf/tools/              构建与取证脚本
  build_i18n.py / build_site.py
  extract_shots.py / convert_shots.py / build_lossless.py / compare_shots.py / common.py
  smoke_site.mjs / interact_site.mjs / measure_network.mjs / shoot_compare.mjs
perf/reports/            构建元数据、网络实测、截图差异、探针日志
tests/                   9 支常驻探针 + 基线 JSON + 截图归档 + 校验报告
AGENTS.md / README.md / CONTRIBUTING.md / SECURITY.md / CODE_OF_CONDUCT.md / LICENSE
.github/                  Issue / PR 模板
```

### 环境装配

| 入口 | 命令 | 说明 |
|---|---|---|
| 探针依赖 | `pip install playwright html5lib` + `playwright install chromium` | 9 支 Python 探针的第三方依赖；本仓库无锁文件 |
| 构建依赖 | `pip install -r perf/requirements.txt` | Python 构建脚本仅依赖 Pillow |
| Python | 3.12 实测基线 | `perf/` 类型注解要求 3.10+；`r51_i18n_check.py` 直跑需 3.13+，3.12 使用 `Path.open(newline="")` 兼容包装 |
| Node | 现代版本 | 用于 `node --check` 与 `.mjs` 取证脚本；无 `package.json`/锁文件 |

探针一律 `python tests/<脚本>.py` 直跑，不建 venv。不得新增 npm scripts、Makefile 或平行工具入口。

### 常用命令

| 任务 | 命令 |
|---|---|
| 校验译文/键表/零外链/build_site 锚点 | `python perf/tools/build_i18n.py --check` |
| 刷新键表快照 | `python perf/tools/build_i18n.py --extract` |
| 注入译文到单文件 | `python perf/tools/build_i18n.py --write` |
| 再生多文件版 | `python perf/tools/build_site.py` |
| 常驻探针 | `python tests/<脚本>.py` |

### 常驻探针

| 探针 | 覆盖 |
|---|---|
| `tests/r37_bento_check.py` | Bento Grid、配色、圆角、零外链、功能基线 |
| `tests/r38_visual_check.py` | 三态外观、菜单、AA 对比度、多路由溢出 |
| `tests/r39_type_check.py` | 苹果式排版阶梯 |
| `tests/r41_cards_detail_check.py` | landing 卡片行尾详情展开 |
| `tests/r42_migration_check.py` | 二级页内容迁移、GitHub 入口、断点矩阵 |
| `tests/r43_icon_check.py` | 软件图标单点内联、六槽位、溢出矩阵 |
| `tests/r45_theme_scope_check.py` | landing 暗底色彩作用域、AA、折叠配色入口 |
| `tests/r51_i18n_check.py` | 六语 i18n 源码级/运行时级/溢出 |
| `tests/r54_nav_actions_check.py` | 常驻导航七入口布局、间距、路由可达性 |

`tests/i18n_pin.py` 是探针共用的语言钉住辅助模块。基线 JSON 与 `tests/*-shots/` 是有意入库的验收证据，勿删。

## 源码导航与硬契约

定位一律使用 grep 锚点，不依赖绝对行号；grep 巨型数据行时必须截断输出。

| 区域 | 定位锚点 | 说明 |
|---|---|---|
| 头部防闪烁与图标 | `THEME:BEGIN` / `R43-ICON:BEGIN` | 主题首帧脚本 + 两枚 `data:` 图标 link |
| 全量 CSS | `<style>` / `</style>` | 基础样式与 R18–R55 活动增量层 |
| 一级导航 | `LP-NAV:BEGIN` | `.lp-brand` + `.lp-routes` + `.lp-actions` + GitHub 圆钮 |
| 教程/开发者数据 | `#tut-data` / `#dev-data` | 两条巨型 JSON 数据行，严禁手改 |
| 六语词典 | `I18N-DATA:BEGIN` | 由 `build_i18n.py --write` 生成，勿手改 |
| i18n 运行时 | `I18N:BEGIN` | i18next 23.16.8 UMD + `window.__i18n` + `T/TN` |
| 动画运行时 | `MOTION:BEGIN` | GSAP 3.13.0 核心 + ScrollTrigger |
| 主脚本 | `R46:BEGIN` / `function render()` | 惰性教程解析、hash 路由、视图渲染 |
| 交互增强 | `ENHANCE:BEGIN` / `THEME-UI:BEGIN` / `ABOUT-UI:BEGIN` | 交互精修、主题、关于板块 |
| 下载与按钮动效 | `R21-UI:BEGIN` | 下载面板状态机 + 按压回弹/涟漪 |
| 导航玻璃 | `R26-SVG:BEGIN` / `R26-UI:BEGIN` | 折射滤镜 + 滚动 tone |
| 面板动效 | `R28-UI:BEGIN` / `R29-UI:BEGIN` | FLIP/残影 + 液态玻璃 |
| 卡片视效 | `R31C-UI:BEGIN` / `R31A-UI:BEGIN` / `R31B-UI:BEGIN` | 门卡环、3D 倾斜、Fluid Morph |
| 外观与配色 | `R36-UI:BEGIN` / `R37-UI:BEGIN` / `R38-UI:BEGIN` / `R45-UI:BEGIN` | 配色主题、比例圆角、三态外观、折叠入口 |
| 二级页与详情 | `R40-VIEW:BEGIN` / `R40-UI:BEGIN` / `R41-UI:BEGIN` | 二级页模板、导航高亮、卡片详情 |
| 首页节奏与导航 | `R53-HOME-RHYTHM:BEGIN` / `R54:BEGIN` / `R55:BEGIN` | 首页排版、导航分组、七入口间距 |

硬契约：

- **单文件源零外部资源**：非 `data:` 的 `<link>`、`<script src>`、外链 img、`iframe`、`url(http)`、`@import` 恒为 0；图标 link 恰 2 枚且均 `data:`，`@font-face{` 恰 2 处且均 `data:`。
- **两条巨型数据行严禁手改**：`#tut-data` 当前 21,358,276 字符，`#dev-data` 当前 1,545,974 字符。
- **六语词典块勿手改**：译文改 `locales/*.json`，走 `build_i18n.py --extract/check/write` 单向流程。
- **跨轮次选择器串不改名**：R21 `SEL`、R31A `TILT` 宿主串、GSAP 入场/clearProps 串等。
- **HTML 注释内禁止连续双连字符**。
- **新增可见中文必须重建 Noto Sans SC 子集**；当前工作树不含可复现的子集化脚本，不得引用 `.zcode/r36-font/`。需要新增字符时先在仓库外准备 fonttools/brotli 工具链并完成覆盖验证。
- **Inter 子集当前 381 码位**；超出范围的西文、西里尔、阿拉伯文按字形回落系统字体。
- **不得新增 npm/Make 平行入口**；不得把历史父仓库工具链写成本仓库可用命令。

## 当前路由与界面架构

| Hash | data-view | 内容 |
|---|---|---|
| `#/` | `landing` | 一级首页：产品介绍、资源下载、关于；未知 hash 也回落至此 |
| `#/features` | `landing` | 功能总览 |
| `#/resonance` | `landing` | 共鸣录 |
| `#/privacy` | `landing` | 隐私与本地数据 |
| `#/download` | `landing` | 下载与支持 |
| `#/download/start` | `landing` | 开始使用；支持 `#/download/start@faq` |
| `#/identity` | `identity` | 用户/开发者身份选择门 |
| `#/tutorial` | `home` | 教程首页 |
| `#/all` | `all` | 连续阅读 |
| `#/mX` | `module` | 教程模块页 |
| `#/mX/mYpZ` | `page` | 教程详情页 |
| `#/dev` | `dev` | 开发者工作台 |
| `#/dev/<cat>` | `dev` | 开发者板块 |
| `#/dev/<cat>/<group>` | `dev` | 开发者子分类 |
| `#/dev/<cat>/<group>/<doc>` | `dev` | 开发者文档详情 |

语言切换使用 `?lang=` 或 `localStorage.nikki_lang`，不新增路由。`html[lang]` / `html[data-lang]` 驱动文案与字体栈，`html[dir="rtl"]` 驱动阿拉伯语镜像层。

## 关键开发约定

### 软件图标

- 母图在 `:root{--app-icon:url("data:image/webp;base64,…")}`，全文件仅一份。
- 六处通过 `<span class="app-ic">` 消费，`width/height:1em` 自适应槽位字号。
- 换图时替换 favicon PNG 64²、apple-touch-icon PNG 180²、母图 WebP 256² 三段 base64；六处标记无需改动。
- 不得新增 `assets/` 真实图标文件、`og:image` 或外部图标链接。

### 主题与偏好

- `nikki_theme`：`light/dark/auto`；`light` 态不设 `data-theme`，dark 态设 `html[data-theme="dark"]`。
- `nikki_look`：`neutral/color/plain`，落点 `html[data-look]`。
- `nikki_lp_theme`：`slim/spectrum/energy/deep`，落点 `.lp-root.lp-theme-*`。
- `nikki_role`：`user/dev`。
- `nikki_lang`：`zh/en/fr/es/ru/ar`；判定链为 `__i18nPin > ?lang= > localStorage.nikki_lang > navigator.languages > zh`。
- `__i18nPin` 仅供探针确定性钉住语言。

### landing 色彩与布局作用域

- `energy/deep` 会把 landing 底刷成暗底。新板块文字与表面必须走 `.lp-root` 已翻转的 `--tx/--mut/--bd/--card` 或 landing 墨口 token。
- 不得在 `.lp-root` 上翻 `--card/--ac/--ac-soft`；`#lp-nav` 与 `#look-menu` 在 `.lp-root` 之外，需要各自单点覆写。
- `plain` 态下 `.lp-theme-*` 类仍挂在 `.lp-root`，暗底适配规则必须排除 `plain`。
- R53 首页节奏只作用于 `body[data-view="landing"] #app .lp-root:has(.lpx-stats)`；二级页走 `.pg-*`，不命中该作用域。

### 常驻导航与下载

- `#lp-nav` = `.lp-brand` + `.lp-links`（`.lp-routes` 四条产品路由 + `.lp-actions` 三个主动作）+ `.lp-gh`。
- 三个主动作不得加 `.lp-nav-link`，避免被 `syncNav()` 当作路由项。
- 网盘行在 `lpView()` 与 `pgDownloadView()` 两处重复；更换链接/提取码必须同步修改两处。

## 响应式断点

| 断点 | 用途 |
|---|---|
| `≤1100px` | 开发者文档单列、TOC 隐藏 |
| `≤960px` | 侧栏收起、封面网格 2 列；R53 平板 2 列 |
| `≤900px` | landing 配色色点隐藏；769–900px 使用折叠圆钮 |
| `≤768px` | landing hero 收紧；该档无 landing 配色入口 |
| `≤767px` | R37 单列档复位 `grid-column:auto` |
| `≤720px`（高度） | 矮视口首屏与留白压缩 |
| `≤640px` | 隐藏重复下载按钮；R53 卡片单列；R54/R55 主动作按内容宽度 |
| `≤600px` | 封面网格单列 |
| `≤560px` | 顶栏紧凑、骨架单列、导航字号 12.5px |
| `≤480px` | 窄屏补充压缩 |
| `≤400px` | 导航 gap 4px、品牌 basis 104px |
| `≥641px` | 主动作布局基线 |
| `≥961px` | R53 大屏区块宽与导航留白 |
| `≥1440px` | R37 四列 Bento |
| `≥1920px` | 超宽屏补充 |
| `prefers-reduced-motion` | 全局禁用动画 |
| `prefers-reduced-transparency` | 玻璃层降级 |
| `pointer:coarse` / `hover:hover` | 触屏与精确指针分支 |

审计视口：390 / 768 / 1440 / 1920 / 2560px；R51/R54 另覆盖 360 / 640 / 641 / 850px 等宽度。

## 注释对与安全回滚

- 活动 CSS/JS 层尽量按 `RNN:BEGIN/END` 注释对组织，可独立回滚。
- 非纯追加项必须保留逐字还原说明：R37 两处底色令牌、R43 六处图标、R44 下载卡单行替换、R54 `LP-NAV` 两个包裹 `div`。
- R47–R50 为载荷型改动，无独立注释对；当前截图已是无损 WebP。
- 当前工作树没有正式整文件快照目录；`.i18n-tmp/` 是被忽略的一次性工作区，不作为回滚依据。
- 禁止使用“删除 `site/` 与 `perf/`”作为回滚方案；`perf/` 当前包含 i18n 与建站工具链。

## 验证状态与已知限制

- `python perf/tools/build_i18n.py --check` 当前通过：359 键，MKT 272 / BI 87。
- 归档结果：R54 导航矩阵单文件与 `site/` 各 2580 PASS；r37 F2 与 r39 T13 仍有已知失败/差异，不得概括为“全部通过”。
- 4 个 `.mjs` 写死 `C:/Users/henji/.../playwright`，不可直接移植；本次只记录限制，不修代码。
- `extract_shots.py` / `convert_shots.py` / `build_lossless.py` 是历史 PNG→WebP 基线工具，不能直接处理当前 WebP 源。
- 当前机器 Python 3.12；r51 的 `Path.read_text(newline=...)` 需 3.13+，3.12 下用等价的 `Path.open(newline="")` 包装执行。
- `≤768px` 无 landing 配色入口；极窄屏产品路由在 `.lp-routes` 内横滑。

## 文档清单与维护口径

| 文件 | 定位 | 维护口径 |
|---|---|---|
| `AGENTS.md` | 当前约束、源码导航、路由、断点、回滚、验证状态 | 架构或契约变化时同步当前状态，不追加逐轮报告 |
| `README.md` | 项目入口、运行、测试、构建、体积、授权 | 数值实测，命令与当前工具链一致 |
| `CONTRIBUTING.md` | 贡献流程 | 与 AGENTS.md 当前约定同步 |
| `SECURITY.md` | 安全披露 | 资源模型或部署边界变化时同步 |
| `CODE_OF_CONDUCT.md` | 行为准则 | 极少变动 |
| `locales/README.md` | i18n 编辑流程 | 键表/语种范围变化时同步 |
| `site/README.md` | 多文件版部署 | 重建后同步体积与产物 |
| `.github/ISSUE_TEMPLATE/*.md`、`.github/PULL_REQUEST_TEMPLATE.md` | GitHub 协作模板 | 探针、契约或维护口径变化时同步 |

新增文档门槛：临时计划、轮次报告、一次性取证脚本产物不入库；需要留证的结论写入当前文档或 `perf/reports/`。
