# AGENTS.md — Meow Star Map 开发者网页

## 项目结构概述

单文件静态教程站点，无构建工具、无框架依赖（指站点本体；构建与测试工具链见下文「环境装配与工具链」章节）。

**本工作树的真实目录（20261126 实测）**：

```
Meow Star Map 官网.html ← 唯一源文件（5,742 行 / 25,213,498 B / CRLF；R55 基线），含全部 HTML / CSS / JS / 教程与开发者数据 / 六语词典 / 字体子集 / 图标
site/                     ← 多文件线上版（perf/tools/build_site.py 生成，已入库）
  index.html                单页应用 shell：JS / 六语词典内联，样式表外链（535,186 B；R56 起 CSS 拆出）
  assets/site.css           全站样式（883,647 B；字体子集与图标仍以 data: 内联在此文件）
  data/tutorial.js          window.__TUT__  教程数据（截图改为相对路径）
  data/dev-docs.js          window.__DEV__  开发者文档
  assets/shots/*.webp       48 张 1400×900 无损 WebP 截图（15,991,294 B）
  assets/about-wx.jpg       关于板块微信二维码（238,007 B）
  .nojekyll / README.md
locales/                  ← 六语译文唯一编辑入口
  ui.zh.json                 键表快照（由 build_i18n.py --extract 生成，勿手改）
  ui.{en,fr,es,ru,ar}.json  译文（zh 走源码内联默认值，不入字典）
  tutorial.en.json          教程英文包（9 模块 / 36 页 / 48 个 {{imgN}} 占位）
  README.md                 编辑流程与键归属口径
perf/                     ← 构建与取证工具链（第三方依赖仅 Pillow，见 perf/requirements.txt）
  tools/                     build_i18n.py / build_site.py / extract_shots.py / convert_shots.py /
                             build_lossless.py / compare_shots.py / common.py + 5 个 .mjs 取证脚本
  reports/                   构建元数据、网络实测、截图差异、探针日志（入库）
  assets/ dist/              [gitignored] 可重建中间产物
tests/                    ← 常驻回归探针（9 支）+ 基线 JSON + 截图归档 + 校验报告
  r37_bento_check.py          Bento Grid / 配色 / 圆角 / 零外链 / 功能基线比对
  r38_visual_check.py         三态外观 / 菜单 / AA 对比度 / 多路由溢出
  r39_type_check.py           苹果式排版阶梯
  r41_cards_detail_check.py   landing 卡片行尾详情展开
  r42_migration_check.py      二级页内容迁移零丢失 / GitHub 入口 / 断点矩阵
  r43_icon_check.py           软件图标单点内联 / 六槽位几何 / 溢出矩阵
  r45_theme_scope_check.py    landing 暗底舞台色彩作用域 / AA / 折叠配色入口
  r51_i18n_check.py           六语 i18n（源码级 + 运行时级 + 六语 × 四断点溢出）
  r54_nav_actions_check.py    常驻导航七入口布局（单行 / 不裁切 / 不重叠 / 文字边缘距 / 路由可滚）
  i18n_pin.py                 探针共用的语言钉住辅助模块
AGENTS.md / README.md / CONTRIBUTING.md / SECURITY.md / CODE_OF_CONDUCT.md / LICENSE
.github/                  ← Issue / PR 模板
```

**已不存在于本工作树的旧工具链（历史口径，勿再引用）**：`package.json`（npm scripts `setup/doctor/smoke/vreg`）、`Makefile`、根 `requirements.txt`、`tests/` 下的 r14–r31 探针与 `gui-audit.js` / `insert-*.mjs` / `env_check.py` / `smoke.mjs`、`backups/`、`gui-test-screenshots/`、`archive-r15/` 等归档目录。这些属于父仓库工具链或早期历史产物；本工作树的一律口径以本节与「环境装配与工具链」为准。

## 「构建器」的定位（防误解·20261126）

**站点本体没有构建**：`Meow Star Map 官网.html` 是可双击运行的单文件站点，无打包、无框架、无运行时依赖；`site/` 只是它的网页优化形态。

`perf/tools/`（11 个脚本 / 约 1,800 行）容易被读成「自研构建引擎」，实际是：

- **来源**：2026-11-16 提交 `d9b0ccb`（R50）一次性落地 10 个，2026-11-17 `e7242ae`（R51）补 `build_i18n.py`。不来自任何框架，也不是逐轮长出的通用基础设施。
- **性质**：以单文件为唯一源的**一次性转换器**。`build_site.py`（约 400 行）的 11 步里，除「抽数据」与「拆 CSS」外，全是对源文件做字符串锚点替换（数据外置、`DEV_SB` 惰性化、render/搜索守卫改写、封面正则、占位与预取注入……），每步自带 `FAIL: xxx 未匹配` 守卫——源文件结构一变就必须同步改脚本。它**没有**增量构建、任务图、插件体系、监听热更新、CI 流水线，也没有 `package.json` / lock 文件。
- **依赖**：Python 仅标准库 + Pillow（`perf/requirements.txt`）；Node 仅用于 Playwright 取证脚本与 `node --check`，零 npm 依赖。
- **存在理由**：交付形态要求「离线双击的 25 MB 单文件」，线上又需要多文件版；不维护两份源，就只能写转换器。所以这层是**单文件形态的补偿层，不是架构选择**——若站点本身按多文件组织，大半脚本不需要存在。
- **维护口径**：改内容只改 `Meow Star Map 官网.html`，再重跑脚本；**不要手改 `site/` 产物**（下次重建覆盖）。改生成逻辑就改脚本，然后 `python perf/tools/build_site.py` 复现。`perf/reports/*.json` 只是产物元数据，不是构建缓存。

## 环境装配与工具链（20261126 实况）

### 一次性装配

| 入口 | 命令 | 说明 |
|------|------|------|
| 探针依赖 | `pip install playwright html5lib` + `playwright install chromium` | `tests/` 下 9 支探针的全部第三方依赖；本工作树**无锁文件**，版本以安装环境为准 |
| 构建工具链依赖 | `pip install -r perf/requirements.txt` | 仅 Pillow（无损 WebP 与截图处理） |
| Node | 任意现代版本 | 仅用于 `node --check` 校验 JS 块与 `perf/tools/*.mjs` 取证脚本；**零第三方 npm 依赖**，无 `package-lock.json` |

> 探针一律 `python tests/<脚本>.py` 直跑，**不建 venv**（未激活的 venv 会打断全部既有入口）。
> 历轮实测基线：Python 3.12。

### 声明来源（单一、可复制）

| 事项 | 唯一来源 |
|------|---------|
| 站点本体结构与硬契约 | `Meow Star Map 官网.html` 的注释对 + 本文件「关键开发约定」 |
| 探针第三方依赖 | 本节「一次性装配」（本工作树无 `requirements.txt` 锁文件） |
| 构建工具链第三方依赖 | `perf/requirements.txt`（Pillow） |
| i18n 键表与译文 | `locales/ui.zh.json`（键表快照）+ `locales/ui.{en,fr,es,ru,ar}.json` |
| 教程英文包 | `locales/tutorial.en.json` |

### 常用命令

| 任务 | 命令 |
|------|------|
| 校验译文 / 键表 / 零外链 / build_site 锚点 | `python perf/tools/build_i18n.py --check` |
| 刷新键表快照 | `python perf/tools/build_i18n.py --extract` |
| 注入译文到单文件 | `python perf/tools/build_i18n.py --write` |
| 再生多文件版 `site/` | `python perf/tools/build_site.py` |
| 无损 WebP 重建单文件 | `python perf/tools/extract_shots.py` → `convert_shots.py` → `build_lossless.py --in-place` |
| 路由功能签名对比（原文件 vs `site/`） | `node perf/tools/smoke_site.mjs` |
| 站点真实点击 + 390 移动端溢出 | `node perf/tools/interact_site.mjs` |
| 网络传输 / FCP / DCL 实测 | `node perf/tools/measure_network.mjs`（需本地 HTTP 服务） |
| 8 场景截图取证 | `node perf/tools/shoot_compare.mjs` |
| 逐轮专项探针 | `python tests/<脚本>.py`（`file://` 直开、无端口自起；**不为其新增 npm scripts / make targets，避免平行工具**） |

### 探针清单（9 支，常驻）

| 探针 | 覆盖 |
|------|------|
| `tests/r37_bento_check.py` | Bento Grid 布局 / 配色 / 圆角 / 零外链 / 功能基线比对（`--baseline` 落基线、`--skip-w3c` 跳慢检） |
| `tests/r38_visual_check.py` | 三态外观 / 菜单 / AA 对比度 / 多路由溢出（`--skip-w3c`、`--skip-browser-fallback`） |
| `tests/r39_type_check.py` | 苹果式排版阶梯（`--baseline-json` / `--compare-json`） |
| `tests/r41_cards_detail_check.py` | landing 卡片行尾详情展开（`--skip-slow`） |
| `tests/r42_migration_check.py` | 二级页内容迁移零丢失 / GitHub 入口 / 断点矩阵（`--skip-slow`） |
| `tests/r43_icon_check.py` | 软件图标单点内联 / 六槽位几何 / 溢出矩阵（`--skip-slow`） |
| `tests/r45_theme_scope_check.py` | landing 暗底舞台色彩作用域 / AA / 折叠配色入口（`--skip-slow`） |
| `tests/r51_i18n_check.py` | 六语 i18n：源码级 / 运行时级 / 六语 × 四断点溢出 |
| `tests/r54_nav_actions_check.py` | 常驻导航七入口布局：单行 / 不裁切 / 不重叠 / 文字边缘距 / 路由可滚 |

各探针的完整用法与口径见脚本头部注释；未跑项显式记 NOT-RUN，不当作通过。`tests/i18n_pin.py` 是探针共用的语言钉住辅助模块（把 `__i18nPin` 钉为 zh，保证确定性）。基线 JSON（`tests/r37-baseline.json`、`tests/r39-baseline.json` 等）与 `tests/*-shots/` 截图归档是有意入库的验收证据，勿删。

## HTML 文件章节结构索引

`Meow Star Map 官网.html`（**5,742 行 / 25,213,498 B / CRLF**）的完整章节地图，标注注释标记与行号范围，便于快速定位编辑目标。（**当前基线 = R55**；下方「总览」与「CSS 样式分区」表已于 20261126 刷新为 R55 锚点口径；CSS 分区表与「可回滚注释对标记汇总」一律以 grep 锚点（`R55:BEGIN` 等）为准；行号随轮次漂移；**grep 巨型数据行务必 `cut -c` 截断输出**）

> **R32–R35 勘误（20261025）**：当前文件 = R31 基线 + **R32** GitHub 同步层（`R32:BEGIN/END`，关于板块社交图标配色对齐 MeowStarMap README）+ **R33** 品牌更名轮（20261024，全文件 209 处软件名替换为 Meow Star Map/喵星图 系，数据块 SHA 冻结基线失效；localStorage 键 `nikki_*`、NikkiPhotos_* 目录、`gongeo.us-nikki-tracker`、《无限暖暖》、"Nikki" 角色引用有意保留）+ **R34** 一级界面 Apple 发布会风格层（`R34:BEGIN/END`：Inter v4.1 base64 内嵌 @font-face＝全站唯一 1 处、`--lp-font` 重定义（仅 .lp-* 消费）、九组 `--color-*` 语义 token、`.text-gradient` @supports 纯色兜底、`.lp-hero::before` 超大背景字、四可选主题类 `.lp-theme-slim/-spectrum/-energy/-deep`（模板默认挂 slim）；仅作用 `body[data-view="landing"]`/`.lp-*`/`.lp-root .about-*`；回滚＝删注释对 + 还原 lpView() 两处 class）+ **R35** 全站 Apple 视觉延伸层（20261025，`</style>` 前 R34:END 之后：body 字体栈升级 Inter+Noto Sans SC/思源黑体+苹方/雅黑系统兜底（级联覆写 P1 的 MiSans body 栈，中文不内嵌 Web 字体）、新增 `--r-card:24px` 覆写 `.ms-card/.mod-card/.pagecard/.quick`（不动全局 --r-md）、`.gate h1`/`.hero h1` clamp() 流式字号 + 字距收紧、`.gate-sub`/`.hero-sub` 300 细体、≤960px 紧凑口径微升至 25/26px、print 回落 30px；**零 JS/模板/色彩/动画改动**，暗色零新增规则；回滚＝删 R35 注释对，或整文件还原 `Meow Star Map 官网.backup-r35-20261025.html` 快照）。探针待办：r31_links_check 口径显式更新（Inter data: 巨型行经 >100000 字符剥离逻辑天然不计）、父仓库 `npm run vreg`、r25/r26/r29/r31 探针回归（R35 未触碰按钮/面板几何与色值）。本工作树无父仓库工具链，R35 校验以本机 html5lib strict 解析（0 错误）+ 零外链计数核查 + IAB 六视图截图/控制台遍历替代。

> **R36 勘误（20261025）**：当前文件 = R35 基线 + **R36** Apple 收尾层 + 中文字体内嵌（R36 CSS 层插于 R35:END 与 </style> 之间 L1607–1638；lpThemeCls() 助手 + lpView() 模板单行改写 L1996–2004；R36-UI 脚本块插于 R31B-UI:END 之后 </body> 之前 L3319–3353）：
① Noto Sans SC 可变字体（google/fonts 仓库 ofl/notosanssc，下载日 2026-10-25，源 SHA256 a3041811…，SIL OFL 1.1）按站点字符子集化（1507 字符→1500 字形，366,732B，wght 100..900 覆盖 300/400/500/700）base64 内嵌（**新巨型行 L1621，489,122 字符**，子集 SHA256 2e2083d7…；**@font-face 全站 1→2 处、均 data:，零外链不变量保持**）；中文渲染走思源黑体，缺字由栈内系统字体逐字兜底；**新增中文文案须再子集化**（步骤：node .zcode/r36-font/extract-chars.js 汇集站点字符+新文案 → pyftsubset --text-file --flavor=woff2 → base64 替换 L1621，工具链 fonttools==4.67.0+brotli）。② landing 配色主题色点 .lp-thdots/.lp-thdot（#lp-nav .lp-links 内 4 枚，色值全走 R34 --color-* token）：点击写 .lp-root 的 lp-theme-* 类 + localStorage.nikki_lp_theme（**新键，不触碰 nikki_theme/nikki_role**）+ aria-pressed；lpThemeCls() 随渲染恢复，非法值回落 slim；**≤560px 隐藏色点行**（实测 390/375px 会挤压既有 nav 链接成竖排换行，移动端维持 R35 基线）。③ 暗色核验修复：slim/spectrum 主题浅底墨色（eyebrow/sub/foot，R34 存量）在暗色下不可读 → 暗色换 --color-slim-3（作用域 .lp-root.lp-theme-slim/-spectrum，energy/deep 自带暗色墨色不受影响）。④ .sb-modlink .chev / .kb-chip / .about-pop-item .ab-go 11px→12px。**零业务逻辑/路由/数据结构改动、零新增动画、本层零 hex**。回滚 = 删 R36 CSS 注释对 + 删 R36-UI 脚本块 + 还原 lpView() 两处（助手+模板行）；整文件快照 Meow Star Map 官网.backup-r36-20261025.html。验证：html5lib strict 0 错、17 JS 块编译 0 错、<link>/<script src>/外链 img 全 0、@font-face=2（data:）、本层 0 hex、六视图控制台遍历 0 报错、截图对比 .zcode/r36-shots/。探针待办：r31_links_check 口径须再更新（@font-face 计数 1→2，两条均经 >100000 字符剥离逻辑天然不计）、父仓库 npm run vreg 与 r25/r26/r29/r31 探针回归（R36 未触碰按钮/面板几何与既有色值）。
> **R37 勘误（20261026）**：当前文件 = R36 基线 + **R37** Apple 风格 Bento Grid 便当布局层（CSS 层插于 R36:END 与 `</style>` 之间 **L1639–1723**；`</style>` L1724；`<body>` L1726；**R37-UI** 脚本块插于 R36-UI:END 之后 `</body>` 之前 **L3459–3514**；`</body>` L3515；文件尾 L3516，**总 3516 行**）。作用域仅两个卡片容器（教程首页 `.cover-grid`、开发者工作台 `.mod-grid`）+ 其骨架镜像 `.skel-grid` + 全站页面/卡片底色令牌；**landing（R34/R36）、门页 `.gate-role`、正文/列表/侧栏零改动，且本轮零改类名**，故 R21 涟漪 `SEL`、R31A TILT 宿主串、GSAP 入场/clearProps 串全部原样生效。
① **两处就地令牌改写（非纯追加，回滚须还原原文）**：L20 `--bg:#f4f6fa;` → `--bg:#F5F5F7;`；L842 `--bg:#0f1420;--bd:#2a3244;--tx:#e8ecf4;--mut:#9aa6bd;--card:#161c2a;` → `--bg:#1D1D1F;--bd:#3a3a3c;--tx:#e8ecf4;--mut:#9aa6bd;--card:#000000;`。浅色 `--card:#fff` 本已合规不动。写**字面 hex 而非 `var(--color-neutral-2)`**：后者属 R34 注释对，回滚 R34 会让 L20 变成无效自定义属性、`html` 失去背景色，不建跨轮次依赖。
② **面板让位（本轮成立的前提）**：`--bg` 全站仅 L22 一处消费，而 L75 `.wrap{background:var(--card)}` 铺满阅读区 —— 浅色下灰底被白面板完全盖住（换 `--bg` 等于没换），深色下 `--card`→#000 后面板与卡片同为 #000、**1:1 不可辨**；且本机 `prefers-reduced-transparency` 恒激活，L520/L957 会把 `.wrap-home/.wrap-dev` 强行刷回 `var(--card)`，该失效是必然不是分支。故 R37 用**两条并列规则**把 home/dev 面板底色让位给 `--bg`，特异度分别对齐 L520 `(0,2,1)` 与 L957 `(0,3,2)`，靠源码顺序获胜、零 `important`。
③ **Hero 跨 2列×2行 = 全文件首批 `grid-column/grid-row`**（此前 `grid-column/grid-row/grid-auto-rows/span` 实测 **0 处**）。选主卡用 CSS `:first-child`，**不改 `buildHomeGrid()`/`devHome()` 模板**：`cards.forEach`（L1739）与 `DEV.cats.map`（L1840）保持源序，首卡恰是权重最高的真实入口卡（教程 m1 快速上手且 `firstCoverSrc('m1')` 取到真 `data:image` 封面 / 工作台「项目总览与上手」），零编造内容、零 DOM 语义重排。**曾否决** `data-bento` 属性与 `.bento-hero` 新类：需改 L1743/L1842 他人轮次行、非首位 Hero 会撑隐式轨道、需 `order`/`dense` 补偿、且破坏骨架同构。
④ **单列档必须解跨列**：实测 1 列网格内 `grid-column:span 2` 会撑出 `2px 1112px` 隐式轨道、卡片被压成 2px 宽，故 `@media (max-width:767px)` 复位 `grid-column:auto` 并改用 `aspect-ratio:1/1` 封面 + `min-height` 保持「Hero 仍是最大卡」。同理 `grid-column:span 2` 的计算值落在 **`grid-column-start`**（`-end` 仍是 `auto`），断言须取 start。
⑤ **逐卡比例圆角**：R37-UI 用单个 `ResizeObserver` + `requestAnimationFrame` 批量，对 `.cover-grid>*,.mod-grid>*` 写内联 `--r-bento`，式 `r = clamp(16px, 0.07 × min(宽,高), 34px)`，CSS 侧 `var(--r-bento, var(--r37-r))`（兜底 `--r37-r:26px`）。**取 7% 而非规范字面 18% 的原因**：实测卡短边 213–748px，18% 会给出 15–135px、748px 高的 Hero 近胶囊，故按已确认的工程修正保留「大卡大角、小卡小角」的意图；`border-radius` 属纯绘制属性、不参与盒尺寸，写入不触发观察器自激。**为何不用纯 CSS**：`border-radius:18%` 的横/纵半径分别按宽/高解析（748×870 得 135×157px 椭圆），容器查询需 `container-type:size` 而尺寸包含会把「内容驱动行高」的这两张网格压成 0 高。作用域严格只限两网格，故 **R28/R31B 残影壳的 `border-radius` 静态快照永远不会掺入该变量**（宿主为 `#lp-dl-menu`/`.about-pop`/`.about-wx-dialog`）。脱离文档的节点在 `bind()` 里按 `isConnected` 显式 `ro.unobserve()` 释放。
⑥ **间距与扁平**：`--r37-gap:16px` 收敛 `.cover-grid/.mod-grid/.skel-grid/.quick-grid/.pagecards`（同时压掉 L693 的 28px 与 L708 的 32px 两档随意值），`--r37-block:24px` 给 `.sec-tip` 作区块级留白；两网格卡去 L973–976 双层渐变描边与静置投影、仅留 1px `--bd` 发丝边（dev 视图另有 L975/L976 的 `body[data-view]` 级渐变描边，需并列同特异度规则才能压掉），hover 层级反馈走既有三通道（`translateY` + 强调色边框 + R31 conic 环），**本轮零新增动画**。
⑦ **渐变文字去重**：规范 4.1「每页至多一处、仅页面级 Hero 大标题」——landing 的 `.lp-title` 合规保留；L979/L980 的 `.dev-stats .stat b` 指标数字是第二处，去渐变须**同时**清 `background-image` + `background-clip:border-box` + `-webkit-text-fill-color:currentColor`，否则 `color:transparent` 会让数字隐形；回落色复用既有 `--dvc-deep`（暗色 `--dvc`）。新增 4 列档：`@media (min-width:1440px){.cover-grid,.skel-grid{grid-template-columns:repeat(4,1fr)}}`，Hero 占墙比由 66% 收到 49%，9 卡 = 4+8 = 12 格恰铺 3 行零空洞。
⑧ **封面填充缺陷顺带修（Hero 放大后由隐性变显性）**：L300 `.img-shell img{width:100%;height:auto}` 与 L143 `.ms-cover img{width:100%;height:100%;object-fit:cover}` **特异度相同 `(0,1,1)`、L300 源码在后故胜出**，`height` 实际取 `auto` → 1400×900 原图按比例只画到 357px 高，封面盒其余部分露出 `#eceff4` 灰底。改造前小卡只露约 29px（几乎无人察觉），Hero 跨 2×2 后封面盒涨到 523px 高、**露出 166px 灰带**，视觉上等同破版。修法＝R37 层加一行 `.cover-grid .ms-cover img{height:100%}`（特异度 `(0,2,1)` 压回），作用域仅限封面，**正文配图仍须保持自然高度不裁切**（`.page-body .img-shell` 路径零改动）。
**零新增依赖 / 零外链不变量保持**：`<link>`/`<script src>`/`<iframe>`/`@import`/`url(http)` 全 0，`@font-face{` 仍为 2（均 `data:`），两个巨型数据行未被触碰；**本轮不向 DOM 新增任何可见中文文案**，故不触发 R36 的 Noto 子集化流水线。暗色配套：`.ms-cover-ph`（L880 藏青 `#1a2233` 兜底）与 `.dev-stats .stat`、`.skel-v2 .skel-body` 改随中性 `--card`/`--bd`。
**回滚** = 删 R37 CSS 注释对 + 删 R37-UI 注释对 + 还原上述 L20/L842 两处令牌原文（无其它不可追加项）。
**已知限制**：① 标准单段圆弧 ≠ Apple 连续圆角（曲率连续），且系数已由 18% 工程修正为 7%+34px 上限；② 卡面与页面底色差仅 **1.09:1（浅）/ 1.25:1（深）**，任何单一描边色都无法同时与两侧达 WCAG 1.4.11 的 3:1（两表面需相距 ≥9:1）；改造前既有发丝边 `--bd`↔#fff 亦仅 1.13:1，**本轮不引入新失效**，卡片身份另由封面/标题内容与 `:focus-visible` 的 2px `--ac` 外框（约 4.8:1）承载；③ `.mod-grid` 在 ≥1920 为 4 列 × 15 格，尾部留 1 个空单元格（非内部空洞，符合「宁缺毋滥」）；④ `.gate-role`/`.about-sec`/非 home-dev 的 `.wrap`/`#searchdrop`/`#totop` 的静置投影**不在本轮收敛范围**（属玻璃层，去掉会连带破坏 R26/R29/R31 既有验收）；⑤ R31 倾斜在 748×870 的 Hero 上按 `maxDeg:10` 边缘位移可达约 65px，如需收口请用公开钩子 `window.__r31.cfg.tilt.maxDeg` 在 R37-UI 内覆写，**不要手改 R31A-UI 块**。
**验证（本工作树实测）**：新增 `tests/r37_bento_check.py`（Playwright + html5lib，`file://` 协议、无端口）34 项 = **33 PASS / 0 FAIL / 1 NOT-RUN**（唯一 NOT-RUN：`prefers-reduced-transparency` 双态切换 —— 当前 playwright 版 `emulate_media` 无该形参；本机恒为 reduce，故实跑即该机真实态，非跳过验证）。html5lib 解析当前文件 **0 错误**，与 `Meow Star Map 官网.backup-r36-20261025.html` 快照逐位等值（各约 88s）。改造前后**七视图 × 双主题**功能快照（卡片计数、全部链接 href、标题/文案、`img src`/`alt`、侧栏/面包屑/翻页/相关 chips、正文字数）**逐位一致**，控制台零报错。**探针走「先写可复现用例并确认失败」闭环**：改动前基线运行 = 18 PASS / 9 FAIL（R37 视觉项全部失败，含配色、圆角、间距、Hero 跨列、单列解跨列、手机档主导、渐变文字去重），改动后逐项转绿；过程中该闭环另捕获两处真实缺陷并各自修复后补了常驻断言 —— ① dev 视图 L975/L976 的 `body[data-view]` 级渐变描边压过扁平化（V2 报 10 处）；② **封面未填满**（L300 `height:auto` 压过 L143 `height:100%`，Hero 露 166px 灰带，新增 V6 断言常驻防回归）。视觉实测截图归档 `tests/r37-shots/`（1440/1920/768/390 × 浅/深）。
**探针待办（父仓库）**：`npm run vreg` / `npm run smoke` / `npm run audit:full` / `r15/r19/r20/r24–r31` 探针在本工作树**均不可用**（无 `package.json`/`Makefile`/`requirements.txt`/`tests/` 历史脚本，工具链在父仓库），r37 断言为自包含基线比对；r31 系列探针需复核 `--bg`/`--card` 换值后对色值断言的影响（r20/r29 的 `#8ecbff`/`#0b2e4f` 断言未受本轮触碰）。

> **R38 勘误（20261027）**：当前文件 = R37 基线 + **R38 全站 Apple 收官 + 三态外观层**（R38 CSS L1731–2027、`</style>` L2028、`<body>` L2030；R38-UI L3820–3973；文件尾 L3975，总 3975 行）。本轮只动视觉偏好层，不改 `render()`/路由/数据块/模板 `lpView()`/既有类名；新增 localStorage 键 `nikki_look`（`neutral`/`color`/`plain`，默认 `neutral`），不触碰 `nikki_theme`/`nikki_role`/`nikki_lp_theme`。  
> **① 状态与优先级（非纯追加两处）**：`<html>` L2 增 `data-look="neutral"`；head THEME 脚本首帧读取 `nikki_look` 并写 `html[data-look]`（异常回落 neutral）。优先级 `data-theme`（明暗）> `data-look`（色彩处理）> `lp-theme-*`（仅 landing）；neutral/color 保留 landing 四主题，plain 压过 energy/deep 并隐藏配色圆点。  
> **② R38-UI（L3820–3973）**：纯图标触发器（无文字节点，`aria-label`/`title`）分别注入 `#topbar`（主题按钮后）、`#lp-nav .lp-links`（主题按钮后）、identity 固定右上 fallback；单一 `#look-menu`（默认 hidden + `display:none!important`）三项「中性黑白/彩色氛围/极简全白」，支持点击/Escape/外点/滚动/resize/hashchange 关闭与焦点归还；选择写 `html[data-look]` + `nikki_look`。菜单文案全部在 R36 Noto 子集内（避开缺字舞/浸/斓），无需重做字体；触发器无文本，`body.innerText` 不增长，R37 F2 保持。  
> **③ 视觉**：新增 `--font-en/--font-sans/--type-*/--lh-*/--tracking-*/--sp-section/--r-panel(28px)/--r-panel-sm(22px)` 与反色/动作色语义 token；`--lp-font` 指向同一 `--font-sans`。neutral：教程 `.hero` 白卡 28px + TUTORIAL 背景字、`.dev-hero` 黑卡 28px + DEVELOPER 背景字、门卡平面 22px、`.wrap` 28px、pagecard/quick 24px、step 16px、目录/相关阅读/翻页 22px、按钮恢复胶囊；color 仅门控恢复原彩色 ambient/hero/玻璃/stats；plain 去色、去水印/渐变标题/圆点/氛围层/R31 环/聚光、内容面纯 card/黑、单色控件、社交图标灰度。R37 锁定的 `--bg/--card`、两网格、`.sec-tip` margin 与四类卡半径未动。  
> **④ AA 与渐变**：不改全局 `--mut`；灰底辅助字改用 `--color-slim-1`（暗 slim-3），软蓝底强调字改 `--ac-deep`；landing slim 亮面改 energy-3→stage-2→portrait-2→hello-3（对 #F5F5F7 最低 3.48:1），暗面 slim 改 stage 四色（对 #1D1D1F ≥3）；energy 蓝端点改 energy-4；deep eyebrow/footer 改纯白；`.lp-dl-btn` R29 色值 token 化，computed 不变。  
> **⑤ 回滚**：删除 `/* R38:BEGIN … R38:END */` 与 `<!-- R38-UI:BEGIN … R38-UI:END -->`；还原 `<html>` 的 data-look 与 head THEME 脚本两处；或整文件还原 `Meow Star Map 官网.backup-r38-20261027.html`。其余全为追加。  
> **⑥ 验证（本工作树）**：新增 `tests/r38_visual_check.py`（Playwright + html5lib，file://）**30 PASS / 0 FAIL / 0 NOT-RUN**（含三态/菜单/锚点/AA/七路由六视口双主题溢出/reduced-motion/reduced-transparency/no-JS/字体移除/clip 兜底/console）；`tests/r37_bento_check.py` 全量 **33 PASS / 0 FAIL / 1 NOT-RUN**；html5lib strict 0；Firefox/WebKit 关键路径冒烟无报错；截图 `tests/r38-shots/before|after`（62 张 after）。  
> **已知限制**：在线 W3C Nu 原件 34MB 直传受体积/超时限制；剥离巨型数据/字体行的结构副本为 **0 HTML 错误 + 5 条 CSS 校验器对 R31 既有 `@property`/`conic-gradient`/`var()` 的误报 + 2 条 info**（非 R38 新增，浏览器实测有效），项目主口径 html5lib strict 原件 0 错误；真实 iOS/Safari 硬件未跑（WebKit Windows 代理）；历史 318 处 hex 按确认口径保留，R38 新规则 hex 仅在 token；父仓库 r20/r25 若仍断言双按钮 16px 圆角需同步更新胶囊口径（颜色 computed 未变）；`prefers-reduced-transparency` 双态仍受 playwright 形参限制；360px 顶栏搜索较窄但无溢出。

> **R39–R41 补登（本工作树 20261101 追记；三层此前完全未入本文件，行号见各层 `grep -n "RNN:BEGIN"`）**：
> **R39** 苹果式排版整改层（`/* R39:BEGIN … R39:END */`，纯 CSS，零 JS/DOM/文案/数据/依赖）：`@media screen` 内定义 `--type-eyebrow/-body/-h1/-h2/-h3/-hero/-dev/-gate/-display`、`--lh-body/-lh-heading`、`--space-title-top/-bottom`、`--space-para`、`--measure-prose:40em` 全站排印阶梯；A 标题层级 / B 眉题复用（crumbs、badges、dev-badge、lp-eyebrow）/ C 副文与 lead 去左条与缩进 / D 正文节奏与首子元素复位 / E 40em 行宽（`@supports selector(p:has(img))` 渐进门控）+ 左对齐配图 / F ≤767px 留白最小值。测试 `tests/r39_type_check.py`（24 项）。
> **R40** 产品介绍页增强层（`/* R40:BEGIN … R40:END */` CSS + `/* R40-VIEW:BEGIN … R40-VIEW:END */` 模板层 + `<!-- R40-UI:BEGIN … R40-UI:END -->` 脚本块）：新增 `pgIcon(name)`（14 枚内联 SVG，**未知 name 静默回落 `icons.spark`，打错不报错**）、`lpFooterView()`、`pgShell(kicker,title,lead,content,nextTitle,nextText,actions[,backHref][,backText])` 与 `pgFeaturesView()`/`pgResonanceView()`/`pgPrivacyView()`/`pgDownloadView()` 四个 landing 二级页（`#/features` `#/resonance` `#/privacy` `#/download`，`render()` L2935 判定 + `lpTitles` 分发）；小卡体系 `.pg-grid`（默认 3 列）/`.two`/`.five`/`.pg-card`/`.pg-ico`/`.pg-link`/`.pg-badge`/`.pg-sec`/`.pg-tip`/`.pg-next`/`.pg-back`；landing 侧 `.lpx-section`/`.lpx-card`/`.lpx-banner`/`.lpx-art`/`.lpx-cta-*`/`.lpx-stat*`。`#lp-nav .lp-links` 加 `max-width:min(76vw,760px);overflow-x:auto` + 滚动条隐藏。
> **R41** 卡片二级详情展开层（`/* R41:BEGIN … R41:END */` + `<!-- R41-UI:BEGIN … R41-UI:END -->`）：landing 主要功能 6 卡 + 产品优势 3 卡，点卡片 → 在**所点卡片所在行的末尾**插入 `grid-column:1/-1` 整行详情面板，`max-height` 从 0 撑开、全局互斥；作用域严格收口为 `.lpx-card-grid>.lpx-card`/`.lpx-adv-grid>.lpx-card`，不触碰 `.pg-card`。覆盖层按钮 `.lpx-card-toggle` 用三级选择器压过 R21 引擎自动挂载的 `.r21-b{position:relative}`；详情文案逐字搬运自既有二级页，面板惰性创建且默认脱离文档，故加载期 `body.innerText` 快照不变（R37 F2 兼容）。测试 `tests/r41_cards_detail_check.py`（25 项）。

> **R42 勘误（20261101）**：当前文件 = R41 基线 + **R42 一级界面三大卡片迁移至二级界面 + 顶部常驻 GitHub 入口**（CSS 层 `/* ═══ R42:BEGIN … R42:END ═══ */` 插于 R41:END 与 `</style>` 之间；模板层 `/* R42-VIEW:BEGIN … R42-VIEW:END */` 为 `pgGettingStartedView()`；**非纯追加**，另改 `lpView()` / `pgShell()` / `pgFeaturesView()` / `pgResonanceView()` / `pgDownloadView()` / `render()` 三处 / R40-UI `syncNav()` / `LP-NAV` 与 `#topbar` 两处静态 markup）。整文件快照 `Meow Star Map 官网.backup-r42-20261101.html`。
> **① 一级首页三卡摘除**：`lpView()` 删除 `section.lp-product`、`section.lpx-resonance`（`.lpx-banner` + `.lpx-art`）、`section.lpx-cta`（`.lpx-cta-card`），区块 9 → 6（hero / stats / features 6 卡 / advantages 3 卡 / 关于 / 页脚）。**历史 CSS 有意不删**（保 R34/R40 注释对的独立回滚能力），失效选择器在 R42 头注逐条登记：`.lp-product*`、`.lpx-cta-card`、`.lpx-banner`/`.lpx-art`（两处用法已全部撤除）。
> **② 内容归并（零改写、逐字搬运）**：产品介绍卡 → `#/features`（title/lead 换成卡内两句，卡内三要点变 §1 三张 `.pg-card`，被让位的原 title/lead 降为 §1 的 h2/tip）；共鸣录卡 → `#/resonance`（主句作 §1 h2、描述句作 pgShell lead，页尾残留的 `.lpx-banner` 大卡拆成 `h2 + pg-tip + pg-link` 三行，二级页最后一张大卡清零）；开始使用卡 → **新三级页 `#/download/start`**（kicker/title/lead 三串 + 前往下载/进入应用两按钮原样迁入，并把 `#/download` 的「常见问题」三卡整体搬来，属净去重）。探针 A2 以 12 条原文逐字子串断言证零丢失；唯一有意退场项为一级首页专属自链「了解共鸣录」（迁至目的地后语义不成立，A2b 记录）。
> **③ 三级页路由**：`render()` L2935 条件加 `||h==='/download/start'`、`lpTitles` 加一键、分发链在 `landingPage==='download'` **之前**插一支（`landingPage` 取 `h.slice(1)` 即 `download/start`，与 `/dev/` 前缀分支和 `^/m\d+` 正则均在 if-else 链后段，无冲突）；未知 hash 回落一级首页的默认值不变。`pgShell()` 追加两个**可选尾参** `backHref`/`backText`（默认 `'#/'` / `'← 返回首页'`，默认值须自带箭头，因模板已不再硬编码 `← `），既有四个调用点零改动。深链 `#/download/start@faq` 免费可用（L2931–2932 先剥 `@`，L3063 `getElementById` 视图无关）。
> **④ syncNav 前缀匹配**：R40-UI 原为 `h==='#/'+route` 严格相等，`#/download/start` 会让四个 `.lp-nav-link` 全部失活 → 改为 `h==='#/'+r||h.indexOf('#/'+r+'/')===0` 并先 `split('@')[0]` 剥锚点。
> **⑤ GitHub 常驻入口（两导航各一枚，互斥显示故需双挂）**：`#lp-nav .lp-gh`（32×32 圆钮，几何镜像 `.lp-themebtn`）与 `#topbar .ghlink`（`.alllink` 胶囊 + 图标 + `GitHub` 文本），`href` 逐字 `https://github.com/QianQianLuLu1/MeowStarMap`（实测 200）+ `target="_blank"` + `rel="noopener noreferrer"`。图标**复用站内既有 Octicons mark-github 路径**（ABOUT-UI `SECTION_HTML` 的 `ab-ic-gh`），零新增图形资源；但**不带 `ab-ic-gh` 类** —— L1521–1522 把它写死成 `#111827`/`#e8ecf4`，会压过导航 `data-lg-tone` 的 tone 自适应，故改 `fill="currentColor"` 且本层不写 `color`，让 `.lp-links a` 的 `--mut/--tx` 与他轮主题规则自然级联。`#topbar` 侧**必须作「切换身份」之后的末子元素**：THEME-UI L3435 以 `topbar.querySelector('.rolelink')` 为 `insertBefore` 锚点，且不可给 GitHub 加 `.rolelink` 类（会吃 L215 `body[data-view="dev"] .rolelink{margin-left:auto}`）。
> **⑥ 窄屏导航溢出（本轮唯一实测恶化项，已收回）**：`.lp-links` 为 `gap:26px` flex，圆钮净增约 40px。三段追加式缓解 —— `≤900px` 隐藏 `.lp-thdots`（沿用 R36 原 `≤560px` 既有口径）、`≤640px` 隐藏 `#lp-dl-link`（与同栏 `a[data-route="download"]` 及 hero「资源下载」三重重复，仅 `display:none`，markup 与 R21-UI 绑定原样保留）、`≤640px` 放宽 `.lp-links{max-width:min(66vw,calc(100vw - 133px))}`。实测 390px 溢出 **+46（改造前）→ +86（未缓解）→ +43（最终）**，反优于基线；768/900/1440 档零溢出。`133px` 上限不可省：裸 `66vw` 在 360px 会把 `.lp-brand` 挤成三行（43 → 65px，超出 52px 固定栏高即破版）。
> **⑦ 顺带修正的既有错位**：`#lp-about-link` 处理器用 `document.querySelector('.about-sec')` 定位滚动目标，改造前命中的是 `.lp-product` 借用的样式壳而非真关于板块；三卡摘除后自然命中正确目标（A3/A3b 断言锁定，`scroll-margin-top:64px` 保证不被导航压住）。
> **⑧ 零新增依赖 / 零外链不变量保持 / 字体免重做**：`<link>`/`<script src>`/外链 img/`iframe`/`url(http)` 恒 0，`@font-face{` 恒 2（均 `data:`）；R42 CSS 层**零 hex**，颜色全走既有令牌；零新增动画。新增中文文案全部逐字取自站内既有句子，fonttools 解码 L1628 Noto 子集（1460 码位）遍历八视图 `body.innerText` → **缺字 0，R36 子集无需重做**（该精确核验为一次性脚本，未写入仓库探针以免给 `requirements.txt` 添 fonttools 依赖；探针内改用 stdlib 可判的「新汉字须为源文件既有字符」必要条件，A9b）。
> **⑨ 验证**：新增 `tests/r42_migration_check.py`（Playwright + `file://` 自起、无端口）**38 项 = 38 PASS / 0 FAIL / 0 NOT-RUN**；回归 `r37_bento_check` 33 PASS / 0 FAIL / 1 NOT-RUN、`r38_visual_check` 30/30、`r39_type_check` 24/24、`r41_cards_detail_check` 25/25；html5lib strict 原件 0 错误（r37 S1）。截图 `tests/r42-shots/`（390/360/1440）。**`r37-baseline.json` 已随本轮推进**：F2 曾报 12 处差异，独立复核确认差异字段集合为 `{bodyTextLen}` 单一轴（卡片计数/全部链接 href/标题/img src+alt/侧栏/面包屑/翻页 计数零变化），即纯文案迁移的应有形态；旧基线留存为 `tests/r37-baseline.pre-r42.json`，差异签认记录 `tests/r42-r37-f2-diff.txt`。
> **已知限制**：① 390px 档「关于」按钮仍在 `.lp-links` 横滚区外（该容器改造前即溢出且滚动条被隐藏，属既有缺陷，本轮只保证不因新增圆钮而恶化）；② 360px 档溢出 +73 vs 改造前 +63，受「品牌不得超出 52px 栏高」硬约束无法再收，且 360 不在项目 390/768/1440/1920/2560 审计集内；③ lp-nav 的 GitHub 是 `<a>`，不在 R21 涟漪 `SEL` 内故无按压回弹（扩面须改他轮块，按最小化改动不做）；④ 父仓库 `r31_links_check.py` 冻结的 outbound 清单需追加本轮新增的仓库根 URL，属预期变更（本工作树无该脚本）；⑤ `#/features` §1 三张要点卡与下方 §2/§3/§4 存在语义重叠，为「内容完整迁移」优先于「零重复」的有意取舍。

> **R43 勘误（20261101）**：当前文件 = R42 基线 + **R43 软件图标层**（`<head>` 内 `<!-- R43-ICON:BEGIN … R43-ICON:END -->` 两枚 data: 图标 link + `</style>` 前 `/* ═══════ R43:BEGIN … R43:END ═══════ */` CSS 层 + **六处图标字形就地替换**）。本轮把站点对外呈现的「软件图标」从 📷 emoji 统一换为用户提供的喵星角色方图（4912×4912 原图，WebP 256² 母图 base64 6,664 字符 / PNG 64² favicon 6,280 / PNG 180² apple-touch-icon 29,660，合计 +42.6KB ≈ 全文 +0.12%）。
> **① 六处槽位（改造前 📷 全量，改后计数 6→0）**：`#lp-nav` `.lp-brand-mark`（L2387，1em=17px）、`#topbar` `.lg-emoji`（L2402，20px）、侧栏 `.sb-all` 链接内嵌（L2534，14.5px）、快捷卡 `.q-emoji`（L2610，瓦片内 20~23px）、开发者工作台 `.dev-actions .alllink`（L2719，13.5~14px）、身份门 `.gate-emoji`（L3026，瓦片内 36px）。**不属于软件图标故一律不动**：`.gr-emoji` 人形/工具两枚（身份角色）、`.ms-emoji` 模块瓦片、`pgIcon()` 十四枚内联 SVG、`.lp-tile` 网盘 Arcticons、`.ab-ic-*` 社交 SVG、GitHub Octicon、Feather 按钮图标、微信二维码。
> **② 单点内联 + `1em` 自适应**：母图 base64 全文只出现 1 次（`:root{--app-icon:url("data:image/webp;base64,…")}`），六处共用 `<span class="app-ic">`，其 `width/height:1em` 自动等于所在槽位原字形字号，故**图标的可见尺寸·比例·左上角位置与改造前一致**，无需逐处写死像素（两处品牌位的容器盒因 emoji 推进盒含字体侧边距而收缩约 6px，见「已知限制 ⑤」）。曾否决 `<svg><use href="#app-icon">`（需六处插入 + Safari≤13 `xlink:href` 兜底）与 JS 常量注入（禁 JS 下静态导航/顶栏图标消失，破 R8b 口径）。`background-image` 用长写而非 `background` 简写，故 `.q-emoji`/`.gate-emoji` 的瓦片圆角·底色·描边（L387/L390/L1841/L1861）原样保留；`html[data-look="plain"] .app-ic{filter:grayscale(1)}` 沿用 L1971 社交图标同口径。
> **③ 零外链口径修订（本轮唯一契约变更，须经探针确认）**：改造前全文件 `<link>` 计数恒 0（站点从来没有 favicon），故「标记级 `<link` == 0」是「零外部资源」的**代理指标**而非目的。R43 起四探针统一改为**「无 `http(s)` 外部资源，`data:` 内联豁免」**——`tests/r37_bento_check.py` S5 的 link 计数改负向前瞻 `<link\b(?![^>]*href=["']data:)`，并新增 S5c「图标 link 恰 2 枚且均 data:」；`tests/r38_visual_check.py` S4 的 `"<link>"` 键改 `"<link http(s)>"` 同前瞻；`tests/r39_type_check.py` S0 增加 `icon_link_count == 2` 正向断言；`tests/r42_migration_check.py` A10a 拆为「外链 link 0」+ 新增 A10a2。任何 `http(s)` 外链仍判 FAIL，闸门语义不降。base64 字母表不含 `>` 与引号，负向前瞻不会被载荷截断。
> **④ 非纯追加项**：六处 📷 为就地替换（其中 L2534/L2610/L2719/L3026 在 JS 模板字符串内，只碰图标片段，不触碰所在行的 R21 涟漪 `SEL` / R31A TILT 宿主串 / GSAP 入场串，S7 契约完好）。回滚 = 删两处注释对 + **逐字还原六处 📷** + 还原四探针断言 + 还原 `tests/r37-baseline.json`。
> **⑤ 验证**：`tests/r43_icon_check.py`（Playwright + `file://` 自起、无端口）——六槽位 `.app-ic` 实测宽=高>0、计算 `background-image` 非 `none`、母图 `new Image()` 解码成功（防 WebP 支持面）、六视图 × 1440/768/390/360 × 浅深 × neutral/color/plain 三态零横向溢出、`requestfailed` 恒 0、console 零报错、禁 JS 下导航与顶栏静态图标仍在位、HTTP 服务态零 `favicon.ico` 404。回归 `r37_bento_check`（F2 差异轴须**仅** `bodyTextLen`，旧基线留存 `tests/r37-baseline.pre-r43.json` + 差异签认 `tests/r43-r37-f2-diff.txt` 后 `--baseline` 重落）、`r38_visual_check`、`r39_type_check`、`r41_cards_detail_check`、`r42_migration_check`（C4d 390px `.lp-brand` ≤ 52px）。
> **已知限制**：① **iOS Safari 忽略 `data:` 的 `apple-touch-icon`**，「添加到主屏幕」取不到本图标（Chrome/Edge/Android 走 `rel="icon"` 正常）；真正的 iOS 桌面图标需落地 `assets/` 真实文件，属单文件契约的另行修订，不在本轮；② 无 `og:image`（社交抓取读不了 data:，且加外链 img 会破 A10a）；③ 拍立得相框细节在 14.5~17px 档偏小，母图取 256² 已留 @3× 余量，如仍不可辨可另出「主体放大」同比例变体替换 `--app-icon`（favicon 保持原图）；④ 旧图标是 emoji 字形，**磁盘无旧图标文件需删除**，三份 `backup-r40/r41/r42` 快照有意不改（旧 📷 天然留存于其中，回滚即用）；⑤ **两处品牌位的相邻文字左移约 6px（实测，有意取舍）**：`.lp-brand` 盒 142.2×27.2 → 136×24、`#topbar .logo` 盒 165×32 → 157.5×26.4。原因是 emoji 的**推进盒**（23.2×27.2 / 27.5×32）含字体侧边距与行盒撑高，其可见墨迹宽约 1em，本层按 `1em` 取尺寸故容器收缩；**图标左上角 x 逐位不变**（250→250、24→24、390 档 20→20、66→66），`#lp-nav`(52px) 与 `#topbar`(62px) 均定高，收缩不外溢。未把盒宽钉成 23.2px：那是**单一 emoji 字体在单一系统上的度量巧合**，钉死反而制造跨平台位移。四断点 × 双主题 × 三态文档级零横向溢出（B5）、390 档 `.lp-brand` 高 43px ≤ 52px（与改造前逐位相同）。
> **探针待办（父仓库）**：`tests/r31_links_check.py` 的「零外链资源不变量」同样把 `<link>` 直算为 0，本轮两枚 `data:` 图标 link 会使其误报，须同步改为本轮口径（`<link\b(?![^>]*href=["']data:)` 计 0 + 正向断言图标 link 恰 2 枚）；该脚本不在本工作树，故未随本轮修改。`smoke.mjs` 若以 SHA 冻结数据块，本轮未触碰两条巨行，无需重建基线。

> **R44 勘误（20261101）**：当前文件 = R43 基线 + **R44 `#/download` 右卡内容替换为一级界面「资源下载」面板**（**非纯追加、零注释对**：`pgDownloadView()` 内原 L2965 单行就地替换为 11 行，总行数 4855 → **4865**；`</style>` / `<body>` / 各 `-UI` 块锚点仅整体后移 10 行，两条巨型数据行与字体巨行**未被触碰**（tut 30,924,428 / dev 1,545,974 字符逐位不变）。
> **① 需求与定位**：`#lp-nav` 的「下载」直链（L2407）进 `#/download`，首个 `.pg-grid.two`（L2963）左卡 GitHub Releases（L2964）、右卡「系统要求」（原 L2965）仅一句系统要求且**零下载链接**；三个网盘入口只在一级首页 hero 的 `#lp-dl-menu`（L2811–L2819）。本轮把右卡内容改为与该面板**完全相同**（文字 / 链接 / 说明 / 图标逐字一致），使 `#/download` 成为自足落点。全站「GitHub Releases 卡 + 紧邻右卡」结构仅此一处（L2794 侧栏那个是纯 `<a>` 链接，非卡片）。
> **② 逐字节复用 + 两处必要差异**：新卡 = `<article class="pg-card"><h3>资源下载</h3>` + L2811–L2819 九行**逐字节原样搬运**（脚本派生，非手抄；`<svg>` outerHTML 运行时对拍全等）+ `</article>`。两处有意差异：**(a) 删 `role="menuitem"`** —— 该角色按 ARIA 规范必须挂在 `role="menu"` 容器下，搬进 `<article>` 即成孤儿角色，且新行不携带任何 `id`（绝不复制 `#lp-dl-menu`，防重复 id）；**(b) 删卡顶 `<span class="pg-ico">'+pgIcon('spark')+'</span>` 装饰瓦** —— 卡内已有三枚 42–44px 真实网盘图标，再顶一枚装饰瓦成四枚堆叠（实测卡高 459→399px 口径为含/不含装饰瓦之差，本轮实测最终 290px），且同文件已有 9 张无 `pg-ico` 的 `.pg-card` 先例，属既有惯例而非特例。**未用 `pgIcon('download')`**：与左卡图标重复，读起来像 bug。
> **③ 零新增 CSS 的依据（本轮成立的前提）**：`.lp-dl-item` / `.lp-dl-item:hover` / `:focus-visible` / `.lp-tile` / `.lp-tile.ic-xl,-bd,-yd` / `.lp-dl-meta` / `.lp-dl-name` / `.lp-dl-desc` / `.lp-dl-go`（L1331–1335、L1365–1372）**全部是无祖先限定的全局类选择器**，放进 `.pg-card` 直接生效；`.lp-dl-menu` 自身的绝对定位不随行外溢。`.lp-dl-item` 的全部 JS 消费者（R21 状态机 `find()` L3711、R28 FLIP L3926/L3946，均为 R44 后行号）均经 `getElementById('lp-dl-menu')` + `menu.querySelectorAll()` 限定，该节点在 `#/download` 下不存在故 `menu` 为 `null` → 状态机与 FLIP 天然惰性。类在 R21 涟漪 `SEL`（L3706）内，故新行自动获得与一级界面**同款**按压回弹 + 指针波心涟漪（委托式 `pointerdown` + `closest(SEL)`，`.r21-b` 仅加 `position:relative` + `overflow:hidden`，不改盒尺寸）。
> **④ 明确不做（按最小化改动）**：不抽共享 `netdiskItems()` 助手（须改写 `lpView()` 的 R21/R29 所属行，且新行与面板行存在 `role` 差异，风险高于 1.9KB 重复）；不加 CSS 停止左卡被 grid `align-items:stretch` 拉伸等高（改造前两卡即 227/227 等高，属站内既有惯例；实测改后 290/290，`≤640px` 解单列后自然脱钩为 290/227）；不动 L2794 侧栏 GitHub 链接、不动 `#/download` 的「开始使用」卡与 `#/download/start` 的「安装」卡、不动 `pgShell` 副标题「并确认系统要求与数据边界」。
> **⑤ 零新增依赖 / 零外链不变量保持 / 字体免重做**：`<link>`（非 `data:`）/`<script src>`/外链 img/`iframe`/`url(http)` 恒 0，`@font-face{` 恒 2（均 `data:`），R44 **零 CSS 改动故零新 hex**、零新增动画。新可见文案（资源下载 / 迅雷网盘 / 百度网盘 / 移动云盘 / 提取码 / 免提取码 · 直链访问）**全部逐字取自同一文件的 `lpView()`**，R36 Noto 子集无需重做。三条网盘 URL 由全站 1 次变 **2 次**。
> **⑥ 验证（本工作树实测）**：`tests/r42_migration_check.py` **39 PASS / 0 FAIL / 0 NOT-RUN**（唯一访问 `#/download` 的常驻探针：A2 文案零丢失、A4b 卡网格计数 5 卡 2 网格不变、A6c 返回链、C4 五断点×双主题×六视图零溢出、C6 console）；`tests/r37_bento_check.py`（含 html5lib strict）**33 PASS / 0 FAIL / 1 NOT-RUN**，与基线逐项一致，`#/` 首页 `dlItems` 仍 3 条；`r38`/`r39`/`r41`/`r43` 回归全绿。另做一次性改造前后**九视图逐字段对拍**：差异只落在 `#/download` 一个视图，差异轴恰为 `{h3, tw, hrefs}` 三轴，卡数与网格数不变，卡标题恰为原位替换「系统要求 → 资源下载」，新增链接恰为三条网盘 URL 且零删除；`#/download/start` 标题集合与改造前逐位相同（原系统要求整句在该页「安装」卡逐字留存，站内信息不丢失）。运行时取证：瓦 44×44 / 圆角 12px / 三色互异、行 66px 与一级界面等价、`.r21-b` 挂载与松手零残留、三行可 Tab 聚焦、无重复 id、无孤儿 `role=menuitem`、点击确被当作新标签导航（经本地拦截，零真实外网请求）、禁 JS 不破版、六断点（1440/960/641/640/390/360）×双主题零横向溢出。取证脚本与 12 张截图均在工作树**外部**的一次性临时目录，验毕即删、**不入库**（本轮无新增常驻探针，见「已知限制 ④」）。
> **回滚** = 把新 11 行整段还原为原单行原文（逐字）：`    +'<article class="pg-card"><span class="pg-ico">'+pgIcon('spark')+'</span><h3>系统要求</h3><p>Windows 10 (1803+) / Windows 11，x64 架构。</p></article>'`。零注释对、零 CSS、零 JS 块，故无其它不可追加项。
> **已知限制**：① 1.9KB 网盘行标记在 `lpView()` 与 `pgDownloadView()` **两处重复**，换提取码须改两处（抽共享助手被否，见 ④）；② 页面副标题「并确认系统要求与数据边界」在本页失去「系统要求」卡的落点，属用户确认的有意取舍，信息仍在 `#/download/start`；③ 左卡在 `>640px` 档被拉伸等高、底部留白（用户确认接受）；④ 探针**未新增常驻项**，本轮取证为一次性脚本，防回归依赖 r42 A4b 的卡计数与 C4 溢出矩阵，若日后有人再改此卡内容，常驻探针不会报语义错。
> **探针待办（父仓库）**：`tests/r31_links_check.py` 冻结的 outbound href 清单为**多重集**口径时，三条网盘 URL 由 1 次变 2 次会误报，须按 R42 ④ 先例更新基线（本工作树无该脚本）。

> **R45 勘误（20261101）**：当前文件 = R44 基线 + **R45 landing 暗底舞台色彩作用域收口**（CSS 层 `/* ═══ R45:BEGIN … R45:END ═══ */` **L2397–2499**，插于 R43:END 与 `</style>` 之间；JS 块 `<!-- R45-UI:BEGIN … R45-UI:END -->` **L4967–5024**，插于 R41-UI:END 与 `</body>` 之间；`</style>` L2500、`<body>` L2502、`</body>` L5025、文件尾 **L5026**，总 5026 行、34,856,177 字节；两条巨型数据行 tut 30,924,428 / dev 1,545,974 字符与两条字体巨行**未被触碰**）。**纯追加**：R34/R36/R38/R40/R41/R42/R43/R44 各块、全部模板、路由、数据结构与既有类名零改动。
> **① 根因＝色彩作用域断层，不是渲染链路故障**：顶部常驻导航 `#lp-nav .lp-links` 挂两套色彩选择器——R36 四枚色点 `.lp-thdot`（写 `.lp-root` 的 `lp-theme-*`，存 `nikki_lp_theme`）与 R38 三态 `.look-btn`+`#look-menu`（写 `html[data-look]`，存 `nikki_look`）。`lp-theme-energy`/`lp-theme-deep` 会把 landing 底刷成暗底（R34 L1584–1585 的 `body::before` **position:fixed 视口渐变** `#0B0C10→#181A22` / `#024F97→#1D6EB6`），但 R34 只给**当时存在**的板块做了暗底适配（`.lp-eyebrow`/`.lp-sub`/`.lp-foot`/`.lp-hero::before` 走 `--lp-*-ink` 墨口，`#lp-nav`/`.about-sec`/`.lp-cta` 各有显式规则），R40–R44 新增板块直接消费亮色令牌。**实测**（浅色模式，扫遍整条固定渐变取**最劣端**，与滚动位置无关）：`--tx` 1.21–1.76、`--mut` 1.10–3.59、`--ac` 1.17–3.82、`#lp-nav .lp-gh` 图标 vs 其自身 `background:var(--card)` 白药丸 **1.18（GitHub 入口隐形）**。关键取证：`.pg-sec h2`/`.pg-next h2`/`.pg-data strong`/`.lpx-card h3`/`.pg-card h3`/`.lp-dl-name` **根本没声明 `color`**，靠继承 L1253 `.lp-root{color:var(--tx)}`，故只有**祖先令牌翻转**能抵达，逐条改接 `--lp-*-ink` 会系统性漏掉。`pgShell()` 与 `lpView()` 都产出 `<div class="lp-root'+lpThemeCls()">`，主题类在二/三级页同样在位——所以不是「色点在新板块不生效」，而是「生效了但把文字推到不可读」。
> **② 手段**：T1 只在 `.lp-root` 上翻 `--tx/--mut/--bd` 并新增一个与 R34 同族的墨口 `--lp-ac-ink`（默认 `var(--ac)`，故 slim/spectrum 与深色模式 computed 逐位不变）；S1 把新板块卡面**逐类显式**写暗玻璃，四值逐字取自 R34 L1590 `.about-sec`（`rgba(22,28,42,.62)` + `rgba(255,255,255,.09)` + `--lp-ink-bright`），使 `.lpx-stat/.lpx-card/.pg-card/.pg-next/.lpx-det-in` 与既有 `.about-sec` **同值**（探针 E3 断言六者 computed 全等，这是「与原有板块统一」的可证形式）。
> **③ energy 与 deep 必须分开取值（本轮唯一二次修正）**：deep 渐变浅端 `#1D6EB6`（L≈0.147）下，`--color-siri-4` 仅 **2.84**、`--lp-ink-bright` 仅 **4.48**、`rgba(232,236,244,.78)` 仅 3.36，均不足正文 AA 4.5；energy 渐变浅端 `#181A22` 下同组值 9.30–14.66 富余。故 `.lp-root.lp-theme-deep` 的 `--tx/--mut/--lp-ac-ink` 三档一律取纯白 `--color-neutral-1`（5.31），层级改由字号与字重承担——**与 R38 L1794 已为 deep 的眉题/页脚选 `--color-neutral-1` 的既有决定同口径**，非新发明。energy 保留 `.78` 透明度以维持层级。
> **④ 禁翻清单（本轮成立的前提）**：`--ac/--ac-deep/--ac-soft/--card` 在 `.lp-root` 上**一律不翻**——它们被 `.lp-dl-btn`（`#8ecbff`/`#0b2e4f`，r20 与 r29 精确断言）、`.lp-cta{background:var(--ac)}`（r20/r25 断言）、R41 L2234 `.lpx-card.is-open>.lpx-ico{color:var(--card)}`、L1637 色点选中环共同消费。`--card`/`--bg` 仅允许出现在与 `.lp-root` **隔离**的两个作用域 `#lp-nav`（N1：`#lp-nav` 是 body 直接子节点，在 `.lp-root` 之外，够不着 T1，故镜像 R26 自身 tone 机制单点覆写，一处收口同修 `.lp-gh`/`.lp-themebtn`/`.look-btn` 三枚白药丸）与 `#look-menu`（M1：由 R38-UI 挂在 body 上）；`:has(.lp-root…)` 是关系选择器不是祖先作用域，探针 A10 据此校验改写面。同理 `--lp-eyebrow-ink/--lp-sub-ink/--lp-foot-ink/--lp-title-grad/--lp-grad-fallback/--lp-wm-ink/--lp-ink-bright/--lp-font` 全层零重指派（守 r38 V5）。
> **⑤ 窄屏恢复配色入口（折叠为单枚圆钮）**：R42 为消化 GitHub 圆钮把色点隐藏档从 R36 的 `≤560px` 扩到了 `≤900px`，致 `≤900px` 完全无配色入口。**实测**（`.lp-links` 为 `overflow-x:auto`，取 `scrollWidth-clientWidth`）：inline 色点组宽 100px，在 769/768/820 档分别要多占 **22/22/0**px；**32px 圆钮 + `gap:26px` 在 769/768/820/900 档溢出增量恒为 0**；`≤640` 档连 R42 已确认的 390px `+43` 都无余量（641 档加圆钮即 `+46`）。故折叠档钉为 **`769–900px`**（沿用 R42 的 900 与 R40 的 768 两档，**不新造断点**），`≤768` 仍隐藏并记为已知限制。基态 `display:none` 使 `≥901` 与 `≤768` 自动隐藏，无需额外媒体查询。R45-UI **零改 R36-UI**：色点组仍是**同一批 DOM 节点**（只加 `.is-open` 类，不搬迁、不复制），故 R36-UI 的 `syncPressed()` 选择器 `'#lp-nav .lp-thdot'`（L4320）照常命中、无重复 `data-lp-theme`；浮层的绝对定位包含块是 `position:fixed` 的 `#lp-nav`，因此既不被 `.lp-links` 的 `overflow-x:auto` 裁切也不占 flex 行宽。R36 单独回滚时本块因 `if(!dots.querySelector('.lp-thdot'))return` 空转，不破版。
> **⑥ plain 与深色模式必须惰性**：`plain` 态下 `.lp-theme-*` 类**仍挂在** `.lp-root`（L1972 只隐藏色点），故 CSS 全层带 `html:not([data-theme="dark"]):not([data-look="plain"])`；深色 `--bg:#1D1D1F`/`--tx:#e8ecf4`（L849）本已自洽，`html:not([data-theme="dark"])` 保证 R45 不参与。**顺带修掉一处本轮自造缺陷**：折叠圆钮初版在 `plain` 下仍显示，而 `plain` 已隐藏色点 → 点开是空浮层；补 `html[data-look="plain"] #lp-nav .lp-thdots-toggle{display:none}`（`(1,2,1)` 稳定压过媒体查询的 `(1,1,0)`，零 `important`，也不反转 L1972 自身）。
> **⑦ 零新增依赖 / 零外链不变量保持 / 字体免重做**：外链 link、`<script src>`、`iframe`、`url(http)`、外链 `<img>` 恒 0，图标 link 恒 2 枚且均 `data:`，`@font-face{` 恒 2。R45 CSS 层**零 hex**（仅 rgba 与既有令牌），改写面恰为 `--tx/--mut/--bd/--card/--bg/--lp-ac-ink` 六个（A11 锁定）。**零新增可见中文文案**：折叠圆钮为纯图标 + `::after` 色样，其 `aria-label='配色主题'` 逐字复用 R36-UI L4326，R36 Noto 子集无需重做。零新增动画（仅 `transition` 镜像 `.lp-themebtn`，并补 `prefers-reduced-motion` 关断）。
> **⑧ 验证（本工作树实测）**：新增 `tests/r45_theme_scope_check.py`（Playwright + html5lib + stdlib，`file://` 自起、无端口）**72 项 = 72 PASS / 0 FAIL / 0 NOT-RUN**（A1–A11 源码级含禁翻清单与改写面、B1–B2 泄漏/惰性、C1 `.lp-dl-btn` 色值未动、D1–D3 深色与 plain 惰性、E1 暗底 AA 全量、E2 审计清单零落空、E3 新板块卡面与 `.about-sec` 同值、F1–F8 折叠触发器可见性与开合/`aria-expanded`/选色持久化/Escape 归还焦点/`hashchange` 关闭/plain 豁免/**浮层几何未被裁**、G1 视口矩阵、H1–H2 console 与 `requestfailed` 双零；`--skip-slow` 跳 E 组与断点矩阵）。**改前/改后 A/B 对拍**：把 R45 CSS 层正则剥离生成对照副本再比，改前 1.10–1.76 的全部项改后升至 **5.31–14.86**，slim/spectrum 与深色与 plain 三态 computed 逐位不变。E1 首轮曾报「卡面↔页面底 1.01/1.65<3.0」——该断言口径本身错设（AGENTS R37 已知限制② 已文档化全站卡面↔页面底分离度为 1.09/1.25，所有主题皆然，非本轮引入），故撤掉该阈值，改由 E3 断言「与既有 `.about-sec` 同值」这一真正的一致性要求；`.pg-badge` 落空系路由取错（该元素只在 `#/download` L3065 在位）、`.lpx-det-in` 落空系 R41 面板惰性创建（须先 `.click()` 一张 `.lpx-card-toggle` 并等 600ms），两者均为探针缺陷而非产品缺陷，已各自修正。另：html5lib strict 原件 **0 错误**、全部 **22** 个 JS 块 `node --check` 通过、两条巨型数据行逐位不变。**回归全绿零 FAIL**：`r42_migration_check` 39/39、`r37_bento_check` 34 PASS / 0 FAIL / 1 NOT-RUN（F1/F2 功能快照逐位一致——折叠圆钮**无文字节点**，`body.innerText` 未变，故**无需重落 `tests/r37-baseline.json`**）、`r38_visual_check` 30/30、`r39_type_check` 24/24、`r41_cards_detail_check` 25/25、`r43_icon_check` 25 PASS / 0 FAIL / 1 NOT-RUN。截图归档 `tests/r45-shots/`（11 张：四主题 × 1440/850/390，含 slim 与 deep 的 850px 展开浮层明暗两态）。
> **已知限制**：① `≤768px` 无 landing 配色入口（该档加圆钮即破版，与改前一致，非恶化）；② `.about-soc-btn`（L1909 白药丸）、`.about-pop`、`.ab-ic-dy`/`.ab-ic-gh`（L1150/L1525 写死 `#111827`）在暗底 `.about-sec` 上仍是白斑——属 R32 以前的**既有板块**，拉进本轮成套重绘须同时翻 `#111827` 字形，风险大于收益，按最小化改动不做；③ **发现但未修**的 R34 存量缺陷：L1592 `…:has(.lp-theme-energy) .lp-cta{color:var(--lp-ink-bright)}` 特异度 `(0,3,1)` 压过 L1341 `html[data-theme="dark"] .lp-cta{color:#0f1420}` `(0,2,1)`，致**深色模式 + energy/deep 下主 CTA 亮字叠亮蓝底约 2.6:1** 不达标；属既有板块且被 r20/r25 精确色值断言占用，本轮只在文档与探针口径中记录，未改动（要修须在 R34 块内加 `html[data-theme="dark"]` 分支，破其独立回滚能力）；④ 折叠档 `769–900px` 的可用性依赖 `.lp-links` 当前项数，若日后往导航再加控件须重跑 G1 的 `+58px` 预算；⑤ 本层依赖 `:has()` 与 `:is()`（Safari ≥15.4），不支持的引擎整层不生效 → 回落改前浅底，内容仍可读、不破版，与 R34 L1583 同一渐进口径；⑥ 父仓库 `r15/r19/r20/r24–r31` 探针与 `npm run vreg` 在本工作树不可用（工具链在父仓库）。
> **回滚** = 删除 `/* ═══ R45:BEGIN … R45:END ═══ */` 与 `<!-- R45-UI:BEGIN … R45-UI:END -->` 两处注释对之间内容（**全为追加，无任何不可追加项**：未动 `.lp-root`/`:root` 令牌定义、未动任何模板行、未动任何既有选择器、未新增 hex、未新增文案、未重指派任何 `--lp-*-ink`/`--ac*`/`--card`）；并删除 `tests/r45_theme_scope_check.py` 与 `tests/r45-shots/`。**本工作树无 R44 整文件快照**（磁盘上只有 `backup-r40-20261030` / `backup-r41-20261031` / `backup-r42-20261101` 三份，R43/R44 两轮均未新建快照），故本轮**不可**用「还原整文件」方式回滚，只能删两处注释对；如需整文件回滚请先自行落一份 `backup-r45-*` 快照。

> **R46–R49 勘误（20261111）**：当前文件 = R45 基线 + **R46 教程数据惰性解析** + **R47 教程截图 PNG→WebP q90** + **R48 注入截图惰性解码** + **R49 Inter 字体子集化**。整文件 34,856,177 → 8,999,762 字节（33.24 → 8.58 MiB，**−74.2%**），brotli q11 后 4.91 MiB。**这是本项目第一次有意修改 `#tut-data` 数据行内容**（R47），`smoke.mjs` 的 SHA 冻结必须随之重落。
>
> **R46 · 教程数据惰性解析**（主脚本 IIFE 6 处，+35/−11 行；无 R46 注释对以外的不可追加项）
> ① 顶层 `var DATA=JSON.parse(#tut-data)` 与 `MODS/ORDER/byId/modById` 索引构建收进 `ensureTut()`：首次调用解析并缓存（`DATA` 作哨兵），三个派生对象保持**同一引用**、只在 `ensureTut()` 内填充，故下游闭包零改动。
> ② `USER_SB` 从加载期 IIFE 改为 `buildUserSb()`（惰性 + 字符串缓存），`syncSidebar()` 改为消费该函数；dev 侧栏仍用加载期 `DEV_SB`（dev-data 仅 1.5 MB / 约 3 ms）。
> ③ `render()` 仅在命中 `#/tutorial`、`#/all`、`#/mX`、`#/mX/mYpZ` 时调 `ensureTut()`——**必须前置于路由解析**，因为深链校验本身依赖 `byId/modById`。
> ④ `render()` 仅为教程/开发者视图调 `syncSidebar()`：landing/identity 的 `#sidebar` 恒为 `display:none`，不再为它解析 30.9 MB。
> ⑤ 搜索输入首次触发 `ensureTut()`。
> 验证 19/19：两条数据块逐字节未变、零外链不变量全等（link 2 / script src 0 / iframe 0 / 外链 img 0 / url(http) 0 / @font-face 2 / img 53 / style 1）、22 个 JS 块 `node --check` 通过、CRLF 保留、5026 → 5050 行。
> 已知限制：`#/m999` 这类非法深链会先解析数据再回落 landing（可接受，代价一次解析）。
> 回滚 = 删 `R46:BEGIN/END` 之间新增的 `ensureTut()` + 还原 `USER_SB` 为 IIFE + 还原 4 处 R46 调用点。
>
> **R47 · 教程截图 PNG → WebP q90**（**只改 `#tut-data` 内容**，48 处等位置换）
> ① 48 张 1400×900 截图：22.09 MiB PNG（base64 29.46 MiB）→ WebP q90 3.82 MiB（base64 5.09 MiB），整文件 33.24 → 8.88 MiB。
> ② 在原始文本层按 `data:image/png;base64,` 单遍替换、按图片 sha256 映射目标载荷；`#tut-data` 之前与之后的内容逐字节不变，两侧 JSON 去掉图片载荷后深度等价（36 页 / 9 模块 / id 与顺序一致）。
> ③ 画质：PSNR 均值 38.86 dB、最低 34.53 dB（`m6p1-02.png`，渐变游戏截图）；三联对照图见 `perf/reports/quality-compare-q90.png`；需要零损失可改 `--level lossless`（25.21 MiB，逐位相同）。
> ④ **`smoke.mjs` SHA 冻结重落**：`#tut-data` 旧 `109f8f6c70827d72478fc9b8a8524b5b8b1072c00fc2898c30d5322a0808a81b` → 新 `a15fbd324a9b9f381ade4332f1576f09cf8cd3c534dcf910c638c9a241429372`；`#dev-data` 不变（`8f564a5d…7c76`）。
> ⑤ 工具链（随本工作树新增、可复现）：`perf/tools/extract_shots.py` → `convert_webp.py` → `build_optimized.py` → `verify.py`（仅依赖 Pillow）；`verify.py` 26/26 PASS，`quality.py` 出 PSNR 报告，`bench.py` 出体积/带宽矩阵。
> 回滚 = 从 git 历史取回 R46 版数据行（或 `git checkout 性能/数据惰性加载 -- "Meow Star Map 官网.html"`）。
> 已知限制：WebP 需 Safari 14+，低于项目既有 `:has()`（Safari 15.4+）门槛，不新增兼容风险；`perf/assets/` 与 `perf/dist/` 为可重建产物，已 gitignore。
>
> **R48 · 注入截图的惰性解码**（`wrapImgShells()` 与封面卡各一处，+493 B）
> ① 注入的 `<img>` 补 `loading="lazy"` 与 `decoding="async"`；已显式声明者不覆盖，自闭合标签归一化。
> ② `#/all` 连续阅读仍不包裹，保持原有「控性能」口径。
> 验证：22 个 JS 块 `node --check` 通过；属性注入单测 6 例（无重复属性 / 无漏包 / 已有不覆盖 / 自闭合归一化）。
> 回滚 = 还原 `wrapImgShells()` 一行与封面卡的 `decoding="async"`。
>
> **R49 · Inter 可变字体按站点字符子集化**（只替换 Inter `@font-face` 的 base64 载荷）
> ① Inter Variable 352,240 B（2937 glyphs / cmap 2852）→ 118,640 B（866 glyphs / cmap 381），保留 `opsz`+`wght` 变量轴、全部 layout features 与 name 表。
> ② 目标码位 = 站点全文（剥掉 `data:` 载荷）中 Inter 可渲染的 126 个 ∪ 常用西文安全区间（ASCII / Latin-1 / 常规标点 / 货币 / 箭头 / 数学 / 几何，均与字体 cmap 求交）= 381。
> ③ 校验：目标码位 0 缺失、ASCII 全覆盖、family 名与变量轴不变、`format("woff2")` 未动；全文件 diff 恰好 1 行。Noto Sans SC（366,732 B / 1500 glyphs）未触碰。
> 工具链：fonttools 4.68.0 + brotli 1.2.1（与 R36 登记口径一致，装在工作区临时目录，未污染全局环境）。
> 已知限制：新增西文文案超出这 381 码位范围时缺字回退系统字体；需要覆盖则按 R36 流程重跑子集化。
> 回滚 = 从 git 历史还原 Inter 载荷。
>
> **探针待办**：`tests/r37-baseline.json` 需重落，差异为**单一轴 `sidebarLinks`**（**只落在 light 遍的 `#/` 与 `#/identity` 两个单元格**：47 → 0；dark 遍因同文档 hash 导航不重载、侧栏已缓存，数值不变。R47–R49 对 F2 零影响，已用浏览器实测确认：图片 `data:image/webp`、`loading=lazy`/`decoding=async`、零资源请求、两套字体均加载、全程零 pageerror。另注 `#/identity` 的 `bodyTextLen` 取决于 `localStorage.nikki_role`（未设 134 / role=user 147），基线记的是 147，属环境态、非本轮引入），旧基线已留存为 `tests/r37-baseline.pre-r46.json`，签认记录见 `tests/r46-r37-f2-diff.txt`；`smoke.mjs` 的 `#tut-data` SHA 冻结见 R47 ④；r38/r39/r41/r42/r43/r45 预期不受影响；本工作树无 Python playwright，探针复跑仍记 **NOT-RUN**，但已用 DSH 浏览器插件完成 F2 快照与运行时实测复核（上句数据即来自该实测）。

当前文件 = R29 基线 + R31 卡片三项视效增量（`</style>` 前插入 R31 CSS 层 39 行 + 文件尾 `</body>` 前依次插入 R31C-UI / R31A-UI / R31B-UI 三个脚本块，**R21 状态机、R28 FLIP、R29 玻璃零改动**）。本轮**零新增依赖**（纯 CSS + 内联 JS，复用 MOTION 块内嵌 GSAP 3.13.0），**零外链不变量保持**（`<link>`/`<script src>`/`@font-face`/外链 img 均为 0，outbound href 与 R31 前逐字一致）。当前关键锚点：`<style>` 止于 L1513（R31 层 L1474–1512、R29 层 L1451–1473、R28 层 L1442–1450）；`<body>` L1515；R21-UI L2583–2707；R26-SVG L2708–2718；R26-UI L2719–2786；R28-UI L2787–2870；R29-UI L2871–2935；**R31C-UI L2936–2964（门卡 `.r31-ring` 注入）；R31A-UI L2965–3078（3D 倾斜 + 弹簧回正 + 指针离场归零）；R31B-UI L3079–3185（关于板块 Fluid Morph）**；`</body>` L3186；文件尾 L3187（总 3187 行）。下文旧表行号仅供历史参照。

> **R31 三项视效要点**：① 3D 透视倾斜——`perspective(800px) rotateX/rotateY`，fine 指针 hover 跟随 / coarse 指针拖拽跟随，自写 rAF 弹簧积分器（`k=180,c=22` → ζ≈0.82）回正，交互期挂 `.r31-tilt` 摘掉 transform 过渡通道；触屏位移 >8px 抑制合成 click 防误触。② Fluid Morph——资源下载沿用 R28；**新增** R31B 参数化 `makeMorph` 工厂把同一机制扩面到「关于」QQ 面板 `#about-qq-panel`（居中基态 `xPercent:-50`，与 `lp-dl-menu` 同构）与微信弹窗（变形目标 `.about-wx-dialog`），开启 `expo.out` .52s / 关闭 `power3.in` .32s，关闭经 `.r31-ghost` 残影壳（QQ z71 / 微信 z91）。③ 旋转 conic 描边（`@property --r31-a` + `::before` mask 环形）+ 底部呼吸弥散背光（`filter:drop-shadow` 动画 5.5s；与 hover `box-shadow` 属性独立故叠加共存，且不受 `.ms-card{overflow:hidden}` 裁切）——`.gate-role` 因 `::before`(P11)/`::after`(P6) 均被占用，改由 R31C-UI 注入 `.r31-ring` 子元素承载。**注意**：`.cover-grid .ms-card` 的 `cardIn` 入场动画（L393，`fill:both` 会钉住 transform）在 `html.g-ok` 下本就被 L429 置为 `animation:none`；R31 背光规则按 L429 同特异度覆盖，GSAP 可用时零行为变化。调试钩子 `window.__r31`（`ver:'r31.0'`，`cfg.tilt`/`cfg.morph`，`stats.tilts/springs/morphQq/morphWx/ghost`）。

> **R29 勘误（20261003）**：当前文件 = R28 基线 + R29 面板液态玻璃增量（`</style>` 前插入 R29 层 23 行 + 文件尾 `</body>` 前插入 R29-UI 脚本块 65 行 + lpView() 模板移动云盘 href 单行替换，**R21 状态机与 R28 FLIP 零改动**）。当前关键锚点：`<style>` 止于 L1474（R29 层 L1451–1473、R28 层 L1442–1450、R27 层 L1434–1441）；`<body>` L1476；lpView() 模板按钮行+面板 L1838–1854（网盘三项 href 在 L1842/1845/1848）；R21-UI L2544–2668；R26-SVG L2669–2679；R26-UI L2680–2747；R28-UI L2748–2831；R29-UI L2832–2896；`</body>` L2897；文件尾 L2898（总 2898 行）。下文旧表行号仅供历史参照。

> **R28 勘误（20261003）**：当前文件 = R27 基线 + R28 面板流体变换增量（`</style>` 前插入 R28 层 9 行 + 文件尾 `</body>` 前插入 R28-UI 脚本块，**R21 状态机零改动**）。本勘误时点关键锚点（行号随后续轮次漂移，现行基线以 R29 勘误与分区表锚点为准）：`<style>` 止于 L1451（R28 层 L1442–1450、R27 层 L1434–1441）；`<body>` L1453；MOTION L1480–1505；ENHANCE L2088–2303；R21-UI L2521–2645（`SEL` 在 L2530）；R26-SVG L2646–2656；R26-UI L2657–2724；R28-UI L2725–2808；`</body>` L2809；文件尾 L2810（总 2810 行）。下文旧表行号仅供历史参照。

> **R27 勘误（20261003）**：当前文件 = R26 基线 + R27 按钮动效扩面增量（`</style>` 前插入 R27 层 8 行 + R21-UI `SEL` 扩面一行改写，**JS 逻辑零改动**）。本勘误时点关键锚点（行号随后续轮次漂移，现行基线以 R29 勘误与分区表锚点为准）：`<style>` 止于 L1442（R27 层 L1434–1441、R26 层 L1404–1433、R25 层 L1390–1402）；`<body>` L1444；内嵌数据块 L1469–1470；MOTION L1471 起；ENHANCE L2079–2294；THEME-UI L2295 起；ABOUT-UI L2420 起；R21-UI L2512–2636（`SEL` 在 L2521）；R26-SVG L2637–2647；R26-UI L2648–2715；`</body>` L2716；文件尾 L2717（总 2717 行）。下文旧表行号仅供历史参照。

> **R26 勘误（20261003）**：当前文件 = R25 基线 + R26 导航液态玻璃增量（CSS 层 30 行 + 两按钮箭头 span/配套 CSS 删除 5 行 + SEL 补 `.lp-dl-item` + 文件尾 R26-SVG/R26-UI 共 79 行）。本勘误时点关键锚点（行号随后续轮次漂移，现行基线以 R29 勘误与分区表锚点为准）：`<style>` 止于 L1434（R26 层 L1404–1433、R25 层 L1390–1402）；`<body>` L1436；内嵌数据块 L1461–1462；MOTION L1463 起；ENHANCE L2071–2286；THEME-UI L2287 起；ABOUT-UI L2412 起；R21-UI L2504–2628；R26-SVG L2629–2639；R26-UI L2640–2707；`</body>` L2708；文件尾 L2709。下文旧表行号仅供历史参照。

> **R25 勘误（20261003）**：当前文件 = R21 完成态更名副本（与 R22 时点源文件 `用户使用教程.backup-r22-20261002.html` 同源；该快照存于父仓库 / 外部，本工作树未纳入）+ R25 按钮规范层增量（`</style>` 前插入 15 行）。R22/R23 的改动**不在当前基线**（其章节条目与 r22/r23/r24 探针仅作历史记录）。本勘误时点关键锚点（行号随后续轮次漂移，现行基线以 R29 勘误与分区表锚点为准）：`<style>` 止于 L1408（R25 层 L1393–1407）；内嵌数据块 L1435–1436；`lpView()` L1766；ENHANCE L2045–2260；ABOUT-UI L2386–2477；R21-UI L2478–2602；文件尾 L2604。下文旧表行号仅供历史参照。

### 总览（R55 基线快照；20261126 实测。绝对行号随每轮增量漂移，定位一律以 grep 锚点为准，见下方「CSS 样式分区」与「可回滚注释对标记汇总」）

| 区域 | grep 锚点 / 行号（R55 基线） | 说明 |
|------|------|------|
| `<head>` 头部 | 1–25 | `THEME:BEGIN/END`（L6–19）防闪烁脚本 + `R43-ICON:BEGIN/END`（L21–24）两枚 `data:` 图标 link |
| `<style>` 起始 | L26 | 全量 CSS（`</style>` L2686） |
| `<body>` 静态骨架 | L2688 起 | `LP-NAV:BEGIN/END`（L2689–2707）一级导航 + `#topbar` / `#mask` / `#sidebar` / `#app` |
| 内嵌数据块 | L2723 `#tut-data`（21,358,276 字符）/ L2724 `#dev-data`（1,545,974 字符） | 教程 JSON（`home` / `modules` 9 / `pages` 36）+ 开发者文档 JSON（12 板块 / 104 篇 / 823,995 字）——**严禁触碰** |
| 六语词典块 | `I18N-DATA:BEGIN/END`（L2725–2733） | `#i18n-en/fr/es/ru/ar` + `#i18n-tut-en`（由 `build_i18n.py` 注入，勿手改） |
| i18n 运行时 | `I18N:BEGIN/END`（L2734–3150） | i18next 23.16.8 UMD（MIT）内嵌 + `window.__i18n` 引擎 + `T/TN` 别名 + `setLang()` + `i18nTutApply()` + `__i18n.boot()` |
| `<!-- MOTION -->` 块 | `MOTION:BEGIN/END`（L3151–3176） | GSAP 3.13.0 内嵌库（核心 + ScrollTrigger，含 Observer；无 ScrollToPlugin/Flip/CustomEase） |
| 主脚本（路由 + 渲染） | L3178 起 | 惰性解析 `ensureTut()`（L3188，`R46:BEGIN/END` L3181–3197）/ 侧栏 / 视图渲染 / hash 路由（`render()` L3769） |
| `<!-- ENHANCE -->` 块 | `ENHANCE:BEGIN/END`（L4049–4264） | 三次精修交互增强 |
| `<!-- THEME-UI -->` 块 | `THEME-UI:BEGIN/END`（L4265–4331） | 主题切换按钮 UI（topbar `#themebtn` + lp-nav `.lp-themebtn` 双挂载） |
| `<!-- ATM-UI -->` 块 | `ATM-UI:BEGIN/END`（L4332–4350） | 漂浮几何氛围层 |
| `<!-- TOAST-UI -->` 块 | `TOAST-UI:BEGIN/END`（L4351–4393） | Toast 通知队列 |
| `<!-- ABOUT-UI -->` 块 | `ABOUT-UI:BEGIN/END`（L4395–4486） | 关于板块（社交 + 微信二维码弹窗；二维码 JPEG 在 L4402） |
| `<!-- R21-UI -->` 块 | `R21-UI:BEGIN/END`（L4487–4611） | 资源下载下拉面板状态机 + 全局按钮按压回弹 / 坐标涟漪 |
| `<!-- R26-SVG -->` 块 | `R26-SVG:BEGIN/END`（L4612–4622） | 导航液态玻璃折射滤镜 |
| `<!-- R26-UI -->` 块 | `R26-UI:BEGIN/END`（L4623–4690） | 导航高光 / tone 滚动脚本 |
| `<!-- R28-UI -->` 块 | `R28-UI:BEGIN/END`（L4691–4774） | 面板流体变换（FLIP + 残影壳） |
| `<!-- R29-UI -->` 块 | `R29-UI:BEGIN/END`（L4775–4839） | 面板液态玻璃（按钮浅蓝 + 液态玻璃 + 上缘高光带） |
| `<!-- R31C-UI -->` 块 | `R31C-UI:BEGIN/END`（L4840–4868） | 门卡 `.r31-ring` 注入（`.gate-role` 伪元素被占用的替代路径） |
| `<!-- R31A-UI -->` 块 | `R31A-UI:BEGIN/END`（L4869–4982） | 卡片 3D 透视倾斜 + 弹簧回正（含指针离场归零） |
| `<!-- R31B-UI -->` 块 | `R31B-UI:BEGIN/END`（L4983–5089） | 关于板块 Fluid Morph（QQ 面板 + 微信弹窗两实例） |
| `<!-- R36-UI -->` 块 | `R36-UI:BEGIN/END`（L5090–5157） | landing 配色四枚色点 + `nikki_lp_theme` 持久化 |
| `<!-- R37-UI -->` 块 | `R37-UI:BEGIN/END`（L5158–5213） | 逐卡短边比例圆角（内联 `--r-bento`） |
| `<!-- R38-UI -->` 块 | `R38-UI:BEGIN/END`（L5215–5381） | 外观三态 `data-look` + 菜单（`nikki_look` 持久化） |
| `<!-- R40-UI -->` 块 | `R40-UI:BEGIN/END`（L5382–5402） | 二级页导航高亮 `syncNav()`（L5388） |
| `<!-- R41-UI -->` 块 | `R41-UI:BEGIN/END`（L5403–5681） | landing 卡片行尾整行详情面板 |
| `<!-- R45-UI -->` 块 | `R45-UI:BEGIN/END`（L5682–5739） | 769–900px 档配色入口折叠圆钮 |
| `</body></html>` | L5740–5741 | 文件结尾（总 5,742 行，末行为空行；CRLF 5,741） |

> **R22-UI / R22 高级动效层 / R23 深化不在当前基线**：R22/R23 改动已退出（仅作历史记录，见下方「精修区域标识 · R22/R23」），故上表不含 R22-UI 块；R25–R55 为 CSS 增量层，定位见「CSS 样式分区」表的 `R25:BEGIN`–`R55:BEGIN` 锚点。

### CSS 样式分区（`<style>` 自 L26 起；`</style>` L2686）

> **锚点约定（20261004 起，20261126 刷新）**：各层定位一律以「行号 / 定位锚点」列的标记 grep 为准（如 `grep -n "R55:BEGIN"`，中文标记直接 grep 逐字文本）；尾段各层随后续每轮增量整体漂移，绝对行号仅存于本表与各轮勘误（时点快照）。

| 位置 / 定位锚点 | 注释标记 | 内容 |
|---------|---------|------|
| L26 起 | `<style>` … `</style>`（L2686） | 全量 CSS；下表按源码顺序排列 |
| 基础样式段 | — | `:root` 令牌 / 布局 / 组件 / 顶栏 / 侧栏 / 封面网格 / 详情页 |
| 二次精修层段 | `/* ═══ 二次精修层 ═══ */` | P1 令牌与排印 · P2 卡片微交互 · P3 液态玻璃 · P4 详情页阅读 |
| 三次精修层段 | `/* ═══ 三次精修层 ═══ */` | P5 动效引擎 · P6 阅读进度条 · P7 液态玻璃 v2 · P8 骨架拟真 |
| 四次精修层段 | `/* ═══ 四次精修层 ═══ */` | P9 排印留白 · P10 形状统一 · P11 液态玻璃 v2 · P12 微交互 |
| 五次精修层段 | `/* ═══ 五次精修层 ═══ */` | R13 全设备响应式适配层（390/768/1440/1920/2560） |
| 六次精修层段 | `/* ═══ 六次精修层 ═══ */` | P13 留白节奏 · P14 微交互精修 · P15 液态玻璃 v3 · P16 骨架与空态 v3 |
| 七次精修层段 | `/* ═══ 七次精修层 ═══ */` | P17 深色主题（`html[data-theme="dark"]` 作用域）· P18 科技质感 · P19 技术债 |
| 八次精修层段 | `/* ═══ 八次精修层 ═══ */` | P21 令牌扩展 · P22 Toast · P23 漂浮几何视差 · P24 前轮遗留 |
| 锚点 grep `响应式补齐层` | 多行注释块 + `关于板块层` | R14 触控适配 + 关于板块 CSS（R19 起仅社交/微信） |
| 锚点 grep `UI 细节清零层` | 起＝多行注释块「UI 细节清零层 · R15」；止＝单行 `… UI 细节清零层 · R15:END …`（L1237） | R15 UI 细节清零层（FAQ 间距 / 尾部边距 / 移动端层叠修复） |
| L1239–1311 | `R18:BEGIN … R18:END` | R18 一级首页层（`#lp-nav` 毛玻璃导航 / hero / 滚动淡入 / 暗色与降级） |
| L1313–1345 | `R19:BEGIN … R19:END` | R19 一级首页聚焦层（`.lp-dl` 下载区块 / `.gate-back` / 图标贴片） |
| L1346–1399 | `R21:BEGIN … R21:END` | R21 收纳与动效层（hero 弹性满屏 / `.lp-dl-btn`+`.lp-dl-menu` / `.r21-*` 按压回弹与涟漪 / 矮视口压缩） |
| L1400–1414 | `R25:BEGIN … R25:END` | R25 按钮规范对齐层（双按钮 16px 圆角 / `.lp-cta` 线框化 / 内联图标） |
| L1415–1444 | `R26:BEGIN … R26:END` | R26 导航液态玻璃层（高光扫动带 / `data-lg-tone` / `url(#lg-refract)` 声明对） |
| L1445–1452 | `R27:BEGIN … R27:END` | R27 按钮动效扩面适配层（inline 锚点承载缩放与涟漪裁剪 / summary marker 防裁剪） |
| L1453–1461 | `R28:BEGIN … R28:END` | R28 面板流体变换层（FLIP 屏蔽 / `.r28-ghost` 残影壳） |
| L1462–1484 | `R29:BEGIN … R29:END` | R29 面板液态玻璃层（`.lp-dl-btn` 浅蓝 / 玻璃底 / 上缘高光带 / tone 覆写） |
| L1485–1523 | `R31:BEGIN … R31:END` | R31 卡片三项视效层（3D 倾斜 / conic 环 / 呼吸背光） |
| L1524–1529 | `R32:BEGIN … R32:END` | R32 GitHub 同步层（关于板块社交图标配色对齐软件仓库 README） |
| L1530–1595 | `R34:BEGIN … R34:END` | R34 一级界面 Apple 发布会风格层（Inter 内嵌 / `--color-*` 语义 token / 四套 landing 配色主题） |
| L1597–1617 | `R35:BEGIN … R35:END` | R35 全站 Apple 视觉延伸层（字体栈 / `--r-card` / 流式字号） |
| L1618–1649 | `R36:BEGIN … R36:END` | R36 Apple 收尾层 + 中文字体子集化（Noto Sans SC 字体巨行在 L1632） |
| L1650–1738 | `R37:BEGIN … R37:END` | R37 Bento Grid 便当布局层（底色令牌 / 面板让位 / 首卡跨 2×2 / 逐卡比例圆角 / 扁平化） |
| L1739–2035 | `R38:BEGIN … R38:END` | R38 三态外观层（`data-look` / 排印 token / 面板与按钮外观） |
| L2036–2121 | `R39:BEGIN … R39:END` | R39 苹果式排版阶梯层（`--type-*` / `--lh-*` / `--space-*` / 40em 行宽） |
| L2122–2206 | `R40:BEGIN … R40:END` | R40 二级页小卡体系（`.pg-*` / `.lpx-*`） |
| L2207–2319 | `R41:BEGIN … R41:END` | R41 卡片行尾整行详情面板层 |
| L2320–2385 | `R42:BEGIN … R42:END` | R42 三卡迁移至二级页 + 顶部常驻 GitHub 入口 |
| L2386–2396 | `R43:BEGIN … R43:END` | R43 软件图标层（`--app-icon` 单点内联 / 六处消费） |
| L2397–2499 | `R45:BEGIN … R45:END` | R45 landing 暗底舞台色彩作用域收口 |
| L2500–2530 | `R52-I18N-UI:BEGIN … R52-I18N-UI:END` | R52 六语语言选择器 UI（纯 SVG 触发器，无文本节点） |
| L2532–2566 | `R52-I18N-RTL:BEGIN … R52-I18N-RTL:END` | R52 阿拉伯语 RTL 镜像层（`html[dir="rtl"]`） |
| L2568–2574 | `R52-I18N-FONT:BEGIN … R52-I18N-FONT:END` | R52 按语种字体栈（Inter 子集外的字形回落系统字体） |
| L2575–2652 | `R53-HOME-RHYTHM:BEGIN … R53-HOME-RHYTHM:END` | R53 一级首页布局节奏层（纯 CSS，作用域限 `.lp-root:has(.lpx-stats)`） |
| L2653–2673 | `R54:BEGIN … R54:END` | R54 常驻导航主入口布局（`.lp-routes` / `.lp-actions` 分组） |
| L2674–2685 | `R55:BEGIN … R55:END` | R55 常驻导航文字间距统一（七入口内容宽度 + 统一 padding 与字号） |

### `<body>` 静态 HTML 骨架（L2688–2721）

| 行号 | 元素 | 说明 |
|------|------|------|
| 2688 | `<body data-view="home">` | 静态初始值，JS 路由动态切换 `data-view`（首帧即被 `render()` 覆写） |
| 2690–2706 | `<nav id="lp-nav">` | 一级首页毛玻璃导航（`LP-NAV:BEGIN/END` 注释对 L2689–2707）。R54 起结构：`.lp-brand` + `.lp-links`（内含 `.lp-routes` 四条产品路由 + `.lp-actions` 三个主动作）+ `.lp-gh` GitHub 圆钮 |
| 2708–2718 | `<header id="topbar">` | 顶栏：汉堡菜单 `#burger` · Logo · 搜索框 `#searchwrap`（L2711，`.tut-only`）· 主题切换 `#themebtn`（JS 注入） |
| 2719 | `<div id="mask">` | 侧栏展开时的半透明遮罩 |
| 2720 | `<aside id="sidebar">` | 侧栏容器（内容由 JS `syncSidebar()` 动态填充） |
| 2721 | `<main id="app">` | 主内容区（初始为骨架屏，JS `render()` 填充实际视图） |

### 主脚本路由与视图渲染（R55 基线锚点）

**路由入口**：`function render()`（L3769），监听 `hashchange`（L3122），根据 `location.hash` 设置 `body[data-view]` 并渲染对应视图。未知 hash 一律回落 `landing`（一级首页）；landing 子页判定与 `lpTitles` 分发在 L3816 附近。

| 视图 | data-view | 路由 hash | 渲染函数 / 行号 | 说明 |
|------|-----------|-----------|----------------|------|
| L1 一级首页 | `landing` | `#/`（默认/未知回落） | `lpView()`（L3547）+ `render()` 内 landing 分支 | R21 收纳型 Landing：hero（「资源下载」实心按钮 + 下拉面板 与 单一 CTA 同行，CTA → `#/identity`）+ 核心能力 stats + 主要功能 6 卡 + 产品优势 3 卡（R41 起支持点卡行尾展开详情）+ 关于板块 + 页脚；hero 弹性占满首屏 |
| L2（营销） | `landing` | `#/features`、`#/resonance`、`#/privacy`、`#/download` | `pgFeaturesView()` 等四页（L3627 起） | R40 建、R42 吸收三张大卡；统一走 `pgShell()`（L3610）+ `.pg-grid > .pg-card` |
| L3（营销） | `landing` | `#/download/start` | `pgGettingStartedView()`（L3735） | R42 建的三级页「开始使用」；`pgShell` 可选尾参使返回链指向 `#/download` |
| 身份选择门 | `identity` | `#/identity`（仅显式进入） | `render()` 内 identity 分支 | 用户/开发者双卡分流（`.gate`）+ `.gate-back` 返回首页；不强制首访 |
| L2 教程首页 | `home` | `#/tutorial` | `render()` 内 home 分支 + `buildHomeGrid()`（L3235） | 英雄区 + 封面网格，数据来自 `#tut-data`（R46 起惰性解析） |
| L3 连续阅读 | `all` | `#/all` | `render()` 内 | 全教程连续阅读模式 |
| L3 模块页 | `module` | `#/<模块id>` | `render()` 内 | 模块概览 + 页面列表 + 相关模块 |
| L4 详情页 | `page` | `#/<模块id>/<页面id>` | `render()` 内 | 面包屑 + 正文 + 上下翻页 |
| L2 开发者工作台 | `dev` | `#/dev` | `renderDev()`（L3468）→ `devHome()`（L3349） | 开发者专属工作区，数据来自 `#dev-data` |
| L3 开发者板块 | `dev` | `#/dev/<板块id>` | `devCat()`（L3378） | 板块文档列表 + 过滤 |
| L3+ 开发者子分类 | `dev` | `#/dev/<板块>/<子分类>` | `devGroup()`（L3411） | 子分类文档组 |
| L4 开发者文档详情 | `dev` | `#/dev/<板块>/<文档id>` | `devDocPage()`（L3431） | 文档正文 + TOC |

**关键辅助函数**：

| 函数 | 行号 | 用途 |
|------|------|------|
| `setLang()` | L3018 | R52 语言切换（`nikki_lang`；非法语种显式返回 `false` 且不落任何状态） |
| `low()` / `esc()` | L3202 / L3203 | 小写缓存 / HTML 转义 |
| `ensureTut()` | L3188 | R46 惰性解析 `#tut-data`，填充 `MODS/ORDER/byId/modById`（`R46:BEGIN/END` L3181–3197） |
| `wrapImgShells()` / `hydrateShells()` | L3205 / L3217 | 图片壳包裹与 hydration（R48 注入 `loading="lazy"` / `decoding="async"`） |
| `buildHomeGrid()` | L3235 | 构建首页封面网格 |
| `getRole()` / `setRole()` / `pick()` | L3263–3265 | 身份选择与记忆（`nikki_role`；`pick()` 选完跳 `#/dev` 或 `#/tutorial`） |
| `buildUserSb()` | L3275 | R46 惰性构建用户侧栏 |
| `syncSidebar()` | L3314 | 侧栏内容生成（用户/开发者两套） |
| `crumbs()` | L3321 | 面包屑导航生成 |
| `devHome()` / `devCat()` / `devGroup()` / `devDocPage()` | L3349 / L3378 / L3411 / L3431 | 开发者视图四层渲染 |
| `renderDev()` | L3468 | 开发者视图路由分发 |
| `lpThemeCls()` | L3509 | R36 landing 配色主题类恢复（`nikki_lp_theme`） |
| `pgIcon()` / `lpFooterView()` | L3517 / L3536 | R40 十四枚内联 SVG 图标 / 页脚模板 |
| `lpView()` | L3547 | Landing 模板（R21：资源下载按钮 + 下拉面板 与 CTA 同行） |
| `pgShell()` | L3610 | R40 二/三级页外壳（可选尾参 `backHref` / `backText`） |
| `pgDownloadView()` | L3707 | `#/download` 页面（R44 起右卡为「资源下载」面板逐字复用） |
| `pgGettingStartedView()` | L3735 | `#/download/start` 三级页 |
| `lpEnhance()` | L3753 | Landing 滚动淡入（IntersectionObserver，reduced-motion 降级） |
| `render()` | L3769 | hash 路由总入口 |
| `i18nTutApply()` | L4019 | R52 教程包合并（zh 下为空操作） |
| `syncNav()` | L5388 | R40 二级页导航高亮（前缀匹配，剥 `@` 锚点） |
| R21-UI 面板/动效引擎 | L4487–4611 | 下拉面板状态机（六路关闭 + 视口钳制）+ `pointerdown` 委托涟漪与按压回弹（R27 扩面 19 组），reduced-motion 全停 |
| R45-UI 折叠配色入口 | L5682–5739 | 769–900px 档把四枚色点折成单枚 32px 圆钮 + 纵向浮层 |

### 可回滚注释对标记汇总

> 「定位锚点」列为第 1 列注释对的 grep 定位标记（如 `grep -n "R55:BEGIN"`）；行号随后续轮次整体漂移，历史绝对行号见各轮勘误（时点快照）。

| 标记 | 定位锚点 | 回滚方式 |
|------|------|----------|
| `<!-- THEME:BEGIN -->` … `<!-- THEME:END -->` | `THEME:BEGIN` | 删除之间内容（防闪烁脚本） |
| `<!-- MOTION:BEGIN -->` … `<!-- MOTION:END -->` | `MOTION:BEGIN` | 删除之间内容（GSAP 库） |
| `<!-- ENHANCE:BEGIN -->` … `<!-- ENHANCE:END -->` | `ENHANCE:BEGIN` | 删除之间内容（精修交互；注意先还原内部 R22 弹簧级联注释对 L2204–2210） |
| `/* R22:BEGIN */ … /* R22:END */`（enhance 内 JS） | 2204–2210（**历史行号，当前基线不含**） | 还原为单轨 `if(kids.length)tl.from(kids,{opacity:0,y:14,duration:.45,stagger:.035},'-=0.12');` |
| `<!-- THEME-UI:BEGIN -->` … `<!-- THEME-UI:END -->` | `THEME-UI:BEGIN` | 删除之间内容（主题切换钮，双挂载工厂） |
| `<!-- ATM-UI:BEGIN -->` … `<!-- ATM-UI:END -->` | `ATM-UI:BEGIN` | 删除之间内容（漂浮几何） |
| `<!-- TOAST-UI:BEGIN -->` … `<!-- TOAST-UI:END -->` | `TOAST-UI:BEGIN` | 删除之间内容（Toast 通知） |
| `<!-- ABOUT-UI:BEGIN -->` … `<!-- ABOUT-UI:END -->` | `ABOUT-UI:BEGIN` | 删除之间内容（关于板块：社交+微信弹窗；挂载锚点 `[data-about-slot]` 在 landing 内） |
| `<!-- R21-UI:BEGIN -->` … `<!-- R21-UI:END -->` | `R21-UI:BEGIN` | 删除之间内容（下拉面板状态机 + 全局按钮动效）+ 还原 `lpView()` 模板段与 lp-nav「下载」处理器 |
| `<!-- R22-UI:BEGIN -->` … `<!-- R22-UI:END -->` | 2625–2938（**历史行号，当前基线不含**） | 删除之间内容（面板 FLIP/残影壳 + 全局滚动物理 + R23 深化标记）+ 删除 CSS R22 层 + 还原 enhance() 内 R22 对 |
| `<!-- LP-NAV:BEGIN -->` … `<!-- LP-NAV:END -->` | `LP-NAV:BEGIN` | 删除之间内容（一级首页导航） |
| `/* R18:BEGIN */ … /* R18:END */`（CSS） | `R18:BEGIN` | 删除之间内容（R18 一级首页层）+ 还原 `render()` landing 分支 |
| `/* R19:BEGIN */ … /* R19:END */`（CSS） | `R19:BEGIN` | 删除之间内容（R19 聚焦层）+ 还原 `lpView()`/lp-nav/门页模板/SECTION_HTML |
| `/* R21:BEGIN */ … /* R21:END */`（CSS） | `R21:BEGIN` | 删除之间内容（R21 收纳与动效层）+ 还原 `lpView()` 模板段与 lp-nav「下载」处理器 |
| `/* R22:BEGIN */ … /* R22:END */`（CSS） | 1394–1423（**历史行号，当前基线不含**） | 删除之间内容（R22 高级动效层：CTA conic 环/背光、lpMenuIn 屏蔽、`.r22-ghost`、reduced-motion 静止化）+ 删除 R22-UI 块 + 还原 enhance() 内 R22 对（会一并移除 R23） |
| `/* R25:BEGIN */ … /* R25:END */`（CSS） | `R25:BEGIN` | 删除之间内容（按钮规范层）+ 还原 `lpView()` 两处按钮模板（移除内联 SVG 图标） |
| `/* R26:BEGIN */ … /* R26:END */`（CSS） | `R26:BEGIN` ＋ `R26-SVG:BEGIN` / `R26-UI:BEGIN` | 删除之间内容（导航液态玻璃层）+ 删除 `<!-- R26-SVG:BEGIN/END -->`（折射滤镜）与 `<!-- R26-UI:BEGIN/END -->`（高光/tone 脚本）+ 还原 `lpView()` 两处按钮模板尾部箭头 span（`lp-dl-chev`/`lp-go`）及其 CSS |
| `/* R27:BEGIN */ … /* R27:END */`（CSS） | `R27:BEGIN` | 删除之间内容（动效扩面适配层）+ R21-UI `SEL` 行还原为 `button,.lp-cta,.alllink,.pager a,.lp-dl-item` |
| `/* R28:BEGIN */ … /* R28:END */`（CSS） | `R28:BEGIN` ＋ `R28-UI:BEGIN` | 删除之间内容（面板流体变换层）+ 删除 `<!-- R28-UI:BEGIN/END -->` |
| `/* R29:BEGIN */ … /* R29:END */`（CSS） | `R29:BEGIN` ＋ `R29-UI:BEGIN` | 删除之间内容（按钮浅蓝+面板液态玻璃层）+ 删除 `<!-- R29-UI:BEGIN/END -->` + 还原 lpView() 模板移动云盘 href（`lp-dl-item` 三链之一）+ 还原 r20 探针两行色值断言 |
| `/* R31:BEGIN */ … /* R31:END */`（CSS） | `R31:BEGIN` | 删除之间内容（卡片三项视效层：`.r31-tilt`/conic `::before` 环/`.r31-ring`/`r31spin`+`r31breath` keyframes/`.r31-ghost`/`.r31-on`/`--r31-glow`/reduced-motion+print 降级） |
| `<!-- R31C-UI:BEGIN -->` … `<!-- R31C-UI:END -->` | `R31C-UI:BEGIN` | 删除之间内容（`.gate-role` 注入 `.r31-ring`；残留 `<i>` 无样式无副作用） |
| `<!-- R31A-UI:BEGIN -->` … `<!-- R31A-UI:END -->` | `R31A-UI:BEGIN` | 删除之间内容（3D 倾斜 + 弹簧回正引擎） |
| `<!-- R31B-UI:BEGIN -->` … `<!-- R31B-UI:END -->` | `R31B-UI:BEGIN` | 删除之间内容（关于板块 Fluid Morph：QQ 面板 + 微信弹窗两实例） |
| `/* R37:BEGIN */ … /* R37:END */`（CSS，L1650–1738） | `R37:BEGIN` | 删除之间内容（Bento Grid 层：`.wrap-home/.wrap-dev` 让位页面底、`.cover-grid/.mod-grid/.skel-grid/.quick-grid/.pagecards` gap 16px、`.sec-tip` 区块 24px、首卡跨 2×2 与 Hero 内部构图、`--r-bento` 消费点、去渐变描边与静置投影扁平化、`.dev-stats .stat b` 去渐变、暗色 `.ms-cover-ph`/`.stat`/`.skel-body` 配套、≥1440px 四列档、≤767px 解跨列）+ **另需还原两处就地令牌（本层唯一非纯追加项）**：`--bg:#f4f6fa;` 与 `--bg:#0f1420;--bd:#2a3244;--tx:#e8ecf4;--mut:#9aa6bd;--card:#161c2a;` |
| `<!-- R37-UI:BEGIN -->` … `<!-- R37-UI:END -->`（JS，L5158–5213） | `R37-UI:BEGIN` | 删除之间内容（逐卡短边比例圆角：单 `ResizeObserver` + `rAF` 批量写内联 `--r-bento`，`clamp(16px, 0.07×min(宽,高), 34px)`，`#app` `MutationObserver` 重挂 + `isConnected` 显式 `unobserve` 释放）。删除后 CSS 侧 `var(--r-bento, var(--r37-r))` 自动回落 26px，**不破版**，故可与 CSS 层独立回滚 |
| `/* R38:BEGIN */` … `/* R38:END */`（CSS，L1739–2035）+ `<!-- R38-UI:BEGIN -->` … `<!-- R38-UI:END -->`（JS，L5215–5381） | `R38:BEGIN` / `R38-UI:BEGIN` | 删除两个注释对之间内容；另还原两处非纯追加：`<html data-look="neutral">` 与 head THEME 脚本的 `nikki_look` 读取 |
| `/* R39:BEGIN … R39:END */`（CSS） | `R39:BEGIN` | 删除之间内容（苹果式排版阶梯层：`--type-*`/`--lh-*`/`--space-*`/`--measure-prose` 与 A–F 六组规则，纯 CSS 零 JS/DOM/文案）|
| `/* R40:BEGIN … R40:END */`（CSS）+ `/* R40-VIEW:BEGIN … R40-VIEW:END */`（模板）+ `<!-- R40-UI:BEGIN … R40-UI:END -->`（JS） | `R40:BEGIN` / `R40-VIEW:BEGIN` / `R40-UI:BEGIN` | 删除三处注释对之间内容（`.lpx-*`/`.pg-*` 小卡体系、`pgIcon`/`lpFooterView`/`pgShell` 与四个二级页模板、`syncNav` 高亮脚本）+ 还原 `render()` 的 landing 子页判定与 `lpTitles` 分发 + 还原 `#lp-nav` 的 `.lp-nav-link` 四项 |
| `/* R41:BEGIN … R41:END */`（CSS）+ `<!-- R41-UI:BEGIN … R41-UI:END -->`（JS） | `R41:BEGIN` / `R41-UI:BEGIN` | 删除两处注释对之间内容（卡片行尾整行详情面板：`.lpx-card-toggle`/`.lpx-detpanel`/`.lpx-det-*` 与惰性建面板脚本）|
| `/* R42:BEGIN … R42:END */`（CSS）+ `/* R42-VIEW:BEGIN … R42-VIEW:END */`（模板） | `R42:BEGIN` / `R42-VIEW:BEGIN` | 删除两处注释对之间内容 + 还原 `lpView()` 三卡、`pgShell()` 签名与四页调用、`pgFeaturesView`/`pgResonanceView`/`pgDownloadView` 文案、`render()` 三处、R40-UI `syncNav()`、`LP-NAV` 与 `#topbar` 两处 markup |
| `/* R43:BEGIN … R43:END */`（CSS）+ `<!-- R43-ICON:BEGIN … R43-ICON:END -->`（head link 对） | `R43:BEGIN` / `R43-ICON:BEGIN` | **非纯追加**：删除两处注释对之间内容 + **逐字还原六处 `📷` 图标字形**（`.lp-brand-mark`/`.lg-emoji`/`.sb-all`/`.q-emoji`/`.dev-actions .alllink`/`.gate-emoji`）+ 还原四探针的零外链口径（r37 S5/S5c、r38 S4、r39 S0、r42 A10a/A10a2）+ 还原 `tests/r37-baseline.json`（或直接从 `tests/r37-baseline.pre-r43.json` 取回） |
| **无注释对**（R44 为 `pgDownloadView()` 内单行就地替换 → 11 行） | grep `"<h3>资源下载</h3>"`（全文件恰 1 处，且在 `pgDownloadView` 的 `.pg-grid.two` 内） | **非纯追加、零 CSS、零 JS 块**：把该 `<article>` 的 11 行整段还原为原单行 `    +'<article class="pg-card"><span class="pg-ico">'+pgIcon('spark')+'</span><h3>系统要求</h3><p>Windows 10 (1803+) / Windows 11，x64 架构。</p></article>'`。详见「R44 勘误（20261101）」 |
| `/* ═══ R45:BEGIN … R45:END ═══ */`（CSS，L2397–2499）+ `<!-- R45-UI:BEGIN … R45-UI:END -->`（JS，L5682–5739） | `R45:BEGIN` / `R45-UI:BEGIN` | **纯追加，两处注释对删尽即完全回滚，无任何不可追加项**：未动 `:root`/`.lp-root` 令牌定义、未动任何模板行与既有选择器、未新增 hex / 中文文案 / 动画、未重指派 `--lp-*-ink`/`--ac*`/`--bg`/`--card`（`--card`/`--bg` 仅在 `#lp-nav` 与 `#look-menu` 两个隔离作用域内新赋，不在 `.lp-root` 上）。R45-UI 对 R36-UI **只读不改**（复用其 `.lp-thdots` 产物，只加 `.is-open` 类、不搬迁不复制），故 R36 可独立回滚且 R45-UI 空转不破版。另删 `tests/r45_theme_scope_check.py` |
| `/* ══ R46:BEGIN … R46:END ═══ */`（JS，L3181–3197） | `R46:BEGIN` | 删除之间内容（`ensureTut()` 惰性解析）+ 还原 `USER_SB` 为加载期 IIFE + 还原 4 处 R46 调用点（教程路由判定 / 侧栏 / 搜索 / `render()`） |
| `<!-- I18N-DATA:BEGIN -->` … `<!-- I18N-DATA:END -->`（L2725–2733） | `I18N-DATA:BEGIN` | 删除之间内容（`#i18n-en/fr/es/ru/ar` + `#i18n-tut-en` 五个词典块）。**勿手改**：由 `python perf/tools/build_i18n.py --write` 重新生成 |
| `<!-- I18N:BEGIN -->` … `<!-- I18N:END -->`（L2734–3150） | `I18N:BEGIN` | 删除之间内容（i18next 23.16.8 UMD 内嵌 + `window.__i18n` 引擎 + `T/TN` 别名 + `setLang()` + `i18nTutApply()` + `__i18n.boot()`）+ 还原主脚本 5 处挂点与 R38 `optsHtml/relabel`、R36/R45 的 `i18n:change` 监听 |
| `/* ══ R52-I18N-UI:BEGIN … R52-I18N-UI:END ═══ */`（CSS，L2500–2530） | `R52-I18N-UI:BEGIN` | 删除之间内容（六语语言选择器 UI，纯 SVG 触发器） |
| `/* ══ R52-I18N-RTL:BEGIN … R52-I18N-RTL:END ═══ */`（CSS，L2532–2566） | `R52-I18N-RTL:BEGIN` | 删除之间内容（阿拉伯语 RTL 镜像层） |
| `/* ══ R52-I18N-FONT:BEGIN … R52-I18N-FONT:END ═══ */`（CSS，L2568–2574） | `R52-I18N-FONT:BEGIN` | 删除之间内容（按语种字体栈） |
| `/* ══ R53-HOME-RHYTHM:BEGIN … R53-HOME-RHYTHM:END ═══ */`（CSS，L2575–2652） | `R53-HOME-RHYTHM:BEGIN` | 删除之间内容（一级首页布局节奏层，纯 CSS，**无任何不可追加项**） |
| `/* ══════ R54:BEGIN … R54:END ══════ */`（CSS，L2653–2673） | `R54:BEGIN` | 删除之间内容 + **移除 `LP-NAV` 中 `.lp-routes` / `.lp-actions` 两个包裹 `div`**（保留其子节点原顺序），随后 `python perf/tools/build_site.py` 再生 `site/` |
| `/* ══════ R55:BEGIN … R55:END ══════ */`（CSS，L2674–2685） | `R55:BEGIN` | 删除之间内容（R54 结构与行为自动恢复），随后再生 `site/` |

---

## 关键开发约定

### 软件图标（R43 起）

站点的软件图标是**一张图、一处内联、六处消费**，不是 emoji 也不是外部文件：

- **母图**：`:root{--app-icon:url("data:image/webp;base64,…")}`（WebP 256×256，源图 1:1 方图，只缩放不裁剪）。全文件仅此一份。
- **消费**：`<span class="app-ic" aria-hidden="true"></span>`，`width/height:1em` ⇒ 自动等于所在槽位字号；`background-image` 长写 ⇒ 不覆盖瓦片的 `background` 简写底色。
- **换图**：重新生成三段 base64（favicon PNG 64²、apple-touch-icon PNG 180²、母图 WebP 256²），替换 `--app-icon` 与 head 两枚 `<link>` 的载荷即可，**六处标记无需再动**。
- **favicon**：`<head>` 内两枚 `data:` 内联 `<link>`（`rel="icon"` + `rel="apple-touch-icon"`）；这是全站仅有的 `<link>`，探针按「href 非 `data:` 者计 0」守零外链口径。
- **不要新增的**：`assets/` 真实图片文件（破单文件自包含契约）、`og:image`（data: 抓不到、外链 img 会破 A10a）、`.gr-emoji`/`.ms-emoji`/`pgIcon()`/`.lp-tile`/`.ab-ic-*` 等**非软件图标**图形。

### 主题与偏好机制

- **存储**：`localStorage.nikki_theme`，值为 `light` / `dark` / `auto`（默认 `auto`，由 JS 实时同步 `prefers-color-scheme`；**`light` 态有意不设 `data-theme` 属性**，仅 dark 态设 `html[data-theme="dark"]`）。
- **落点**：`html[data-theme]` 属性；深色样式仅通过 `html[data-theme="dark"]` 作用域定义。
- **防闪烁**：`<head>` 顶部内联 `<script>`（`THEME:BEGIN` / `THEME:END` 注释对之间），首帧前同步解析并设置属性。
- **回滚**：删除 `THEME:BEGIN`…`THEME:END` 注释对之间内容 + R7 深色样式分区 + THEME-UI 块。
- **外观偏好（R38）**：`localStorage.nikki_look` = `neutral`（默认）/`color`/`plain`，落点 `html[data-look]`；与 `nikki_theme`、`nikki_lp_theme` 独立；plain 压过 landing 主题并隐藏配色圆点。触发器为 topbar / lp-nav / identity 三处纯图标按钮 + 单一隐藏菜单；回滚见「R38 勘误」。
- **身份偏好**：`localStorage.nikki_role`（`user` / `dev`），门页 `pick()` 写入。
- **语言偏好（R52）**：`localStorage.nikki_lang`，取值 `zh` / `en` / `fr` / `es` / `ru` / `ar`（默认 `zh`）；落点 `html[lang]` + `html[data-lang]` + `html[dir="rtl"]`（仅阿拉伯语）。判定链 `__i18nPin > ?lang= > localStorage.nikki_lang > navigator.languages > zh`；`__i18nPin` 专供探针确定性钉 `zh`（Chromium 默认 en-US，否则 7 支既有探针基线会成片失配）。非法语种显式回落 `zh` 且 `setLang()` 返回 `false`、不落任何状态（**不得谎报成功**）。语言切换**不新增路由**。
- **landing 色彩作用域铁律（R45 起，新增 landing 板块必读）**：`lp-theme-energy` / `lp-theme-deep` 会把 landing 底刷成**暗底**（`body::before` 是 `position:fixed` 的视口渐变，`#0B0C10→#181A22` / `#024F97→#1D6EB6`）。新板块若直接写 `--tx`/`--mut`/`--bd`/`--card`/`--ac`，在暗底上会掉到 **1.1–1.8:1**（R40–R44 首轮即此不可读）。正确姿势：文字与表面一律走 `.lp-root` 上已翻好的继承令牌（`color:var(--tx)` / `background:var(--card)`），或走 landing 墨口 `--lp-eyebrow-ink`/`--lp-sub-ink`/`--lp-foot-ink`/`--lp-ac-ink`（`--lp-ac-ink` 默认 `var(--ac)`，浅态零差异）。**卡片表面须与 `.about-sec` 同值**才能算「与原有板块统一」，可证形式见 r45 E3（六者 computed 全等）。两条硬约束：① **不要**在 `.lp-root` 上翻 `--card`/`--ac`/`--ac-soft`（`.lp-dl-btn` 的 `#8ecbff`/`#0b2e4f` 与 `.lp-cta{background:var(--ac)}` 被 r20/r25/r29 精确断言占用）；② `#lp-nav` 与 `#look-menu` **都在 `.lp-root` 之外**（分别是 body 直接子节点、body 挂载浮层），够不着祖先翻转，须各自单点覆写（N1/M1），且 `:has(.lp-root…)` 是关系选择器、不是祖先作用域。`plain` 态下 `.lp-theme-*` 类**仍在** `.lp-root` 上，任何暗底适配规则都必须带 `:not([data-look="plain"])` 才不推翻 R38 的 plain 组。
- **R53 landing 布局作用域（R53 起，新增 landing 板块必读）**：R53 的排版节奏规则挂在 `body[data-view="landing"] #app .lp-root:has(.lpx-stats)` 上——**只有带 stats 区块的一级首页命中**，四个二级页走 `.pg-*` 体系不命中。给一级首页加新区块时，若希望它跟随 R53 的留白与栅格，须确认该区块所在视图仍带 `.lpx-stats`；否则会因选择器不匹配而完全不受 R53 影响。

### 五级界面架构（R21 起收拢入口）

通过 `body[data-view]` 属性控制视图切换：

| 层级 | data-view 值 | 路由 | 说明 |
|------|-------------|------|------|
| L1 | `landing` | `#/` | 一级首页，**聚焦「关于 + 下载」**：hero（「资源下载」实心按钮 + 下拉面板（三网盘项）居 CTA 左侧，CTA → `#/identity`）+ 核心能力 stats + 主要功能 6 卡 + 产品优势 3 卡（R41 起支持点卡行尾展开详情）+ 关于板块（首屏底部免滚动）+ 页脚；隐藏顶栏/侧栏，显示 `#lp-nav`；**不再有任何教程/开发者直链，无独立下载区块**；R42 起三张整宽大卡（产品介绍 / 共鸣录横幅 / 开始使用）已迁往二级页；R53 起本层受 `R53-HOME-RHYTHM` 排版节奏层约束（作用域限 `.lp-root:has(.lpx-stats)`） |
| L2（营销） | `landing` | `#/features`、`#/resonance`、`#/privacy`、`#/download` | R40 建的四个产品介绍二级页，`view` 仍为 `landing`（共用 `#lp-nav` 与 `.pg` 的 92px 顶部留白），仅模板与 `document.title` 分流；统一走 `pgShell` + `.pg-grid > .pg-card` 小卡体系，**R42 起页内零大卡** |
| L3（营销） | `landing` | `#/download/start` | R42 建的三级页「开始使用」，承载版本 / 系统要求 / 三步 / FAQ；`pgShell` 可选尾参使返回链指向 `#/download` 而非首页 |
| 门页 | `identity` | `#/identity` | 身份选择门 = 文档入口唯一收拢点（用户/开发者双卡分流），隐藏顶栏与侧栏；仅显式进入，不强制首访；`.gate-back` 可返回 L1 |
| L2 | `home` / `dev` | `#/tutorial` / `#/dev` | 教程首页（隐藏侧栏）/ 开发者工作台 |
| L3 | （默认/模块/all） | `#/mX`、`#/all` | 模块页 / 连续阅读，显示侧栏导航 |
| L4 | （默认/详情） | `#/mX/mYpZ`、`#/dev/...` | 详情页，面包屑 + 上下翻页 |

开发者视图额外通过 `body[data-view="dev"]` 切换紫色令牌（`--dvc` 系列变量）。

**常驻导航结构（R54 / R55）**：`#lp-nav` = `.lp-brand` + `.lp-links`（内含 `.lp-routes` 四条产品路由 + `.lp-actions` 三个主动作「进入 / 下载 / 关于」）+ `.lp-gh` GitHub 圆钮。R54 起产品路由独立横滑、三个主动作独占剩余宽度；R55 起七个文字入口统一为内容宽度（`flex:0 0 auto` + `padding-inline:2px` + `white-space:nowrap`，基础 13.5px、≤560px 12.5px），组间 gap 用 `clamp(8px,1.25vw,22px)`、≤400px 收至 4px。三个主动作**不**加 `.lp-nav-link` 类，以免被 `syncNav()` 当作路由项。

**六语覆盖（R52 起）**：营销侧（L1 + 五个二/三级页 + 页脚 + 关于 + `#lp-nav` + 下载面板 + 配色/外观/主题 + 卡片详情）为 zh/en/fr/es/ru/ar 六语；工作区侧（身份门 / 教程族 / 开发者页框）只有 zh/en，其余语种回落英文并给出一行双语通告（`notice.bi`）；**开发者文档库正文永久不译**。

### 响应式断点

（下列为源文件中实际存在的媒体查询，20261126 按 `grep "@media"` 全量核对。）

| 断点 | 用途 |
|------|------|
| `≤ 1100px` | 开发者文档布局单列化，TOC 隐藏 |
| `≤ 960px` | 侧栏收起为汉堡菜单，封面网格 2 列；R53 在 `641–960px` 档改 2 列 stats / 卡片栅格 |
| `≤ 900px` | R19 下载卡三列 → 单列（R21 起已收拢为下拉面板，仅剩回滚价值）；R42 起隐藏 landing 配色色点行 |
| `≤ 768px` | Landing hero 收紧（R18/R21） |
| `≤ 767px` | R37 单列档复位 `grid-column:auto`（否则 `span 2` 撑出隐式轨道把卡片压成 2px 宽） |
| `≤ 720px`（高度） | R21 矮视口首屏再压缩；R53 在矮视口收紧 hero / 关于 / 页脚留白 |
| `≤ 640px` | R42 隐藏重复的 `#lp-dl-link` 下载按钮；R53 在此档改 1 列卡片栅格；R54/R55 在此档让 `.lp-actions` 按内容宽度排布 |
| `≤ 600px` | 封面网格单列 |
| `≤ 560px` | 顶栏紧凑模式、骨架屏单列、lp-nav 紧凑；R55 在此档把七个文字入口字号降至 12.5px |
| `≤ 480px` | 更窄档的补充压缩 |
| `≤ 400px` | R54 在此档把导航 gap 收到 4px、品牌 `flex-basis` 收到 104px |
| `≥ 641px` | R54 三个主动作严格三等分（R55 改为内容宽度） |
| `769–900px` | R45 折叠配色入口圆钮的生效档（R42 曾把色点隐藏档扩到 ≤900px，致该档一度无配色入口） |
| `≥ 961px` | R53 大屏档：区块宽 `min(1440px, 100% − 64px)`、导航内边距按视口居中 |
| `≥ 1024px` / `≥ 1101px` | 开发者文档宽屏布局 |
| `≥ 1440px` | R37 四列 Bento 档（9 卡 = 4+8 = 12 格铺 3 行零空洞） |
| `≥ 1920px` | 超宽屏补充档 |
| `prefers-reduced-motion` | 全局禁用动画（R21 涟漪/回弹、R22 FLIP/残影、GSAP 入场在 JS 层也直接跳过） |
| `prefers-reduced-transparency` | 玻璃层降级（R26 起导航两栏经 `@supports` 豁免） |
| `pointer:coarse` / `hover:hover` | 触屏与精确指针分支（R31 倾斜、玻璃高光、涟漪） |

审计覆盖视口：390 / 768 / 1440 / 1920 / 2560 px；R51/R54 另覆盖 360 / 390 / 640 / 641 / 850 / 1440 等宽度。

## 精修区域标识

CSS 中以注释分隔符标记各精修层，格式为 `/* ═══ 第N次精修层（日期）：… ═══ */`：

- **P1**：令牌与排版（阴影/圆角/字体栈/数字等宽/细滚动条）
- **P2**：卡片微交互（emoji 瓦片/封面缓放/stagger 入场）
- **P3**：液态玻璃精修（边缘高光/液态渐变/焦点柔光圆）
- **P4**：详情页阅读精修（杂志式表格/截图柔影/引用圆角）
- **R7**：深色主题分区（`html[data-theme="dark"]` 作用域）
- **R8 / R14 / R15**：后续响应式与交互精修轮次
- **R18**：一级首页层（`R18:BEGIN/END` 注释对，`#/` Landing + `#lp-nav`；配套 `LP-NAV:BEGIN/END` HTML 块与 `render()` landing 分支）
- **R19**：一级首页聚焦层（`R19:BEGIN/END` 注释对；下载剥离为 `.lp-dl` 独立区块、文档入口收拢至 `#/identity` 门页、`.gate-back`）
- **R21**：一级首页收纳与全局按钮动效层（`R21:BEGIN/END` CSS + `R21-UI:BEGIN/END` JS；`.lp-dl` 三卡收拢为 hero 内「资源下载」实心按钮+下拉面板、hero 弹性满屏使关于板块首屏贴底、全局按钮按压回弹 `r21-press/r21-pop` 与坐标涟漪 `r21-rip`）
- **R22**（历史轮次，**当前基线不含**）：高级动效层（GSAP FLIP 面板变换 + `.r22-ghost` 残影壳 + 全局滚动物理 + `__r22` 钩子）
- **R23**（历史轮次，**当前基线不含**）：R22 深化轮（残影壳补间 transform 化 / lastRect 时效加固 / TOC sticky 冻结 / 手感参数收拢 `window.__r23`）
- **R25**：一级首页按钮规范对齐层（`R25:BEGIN/END` CSS + `lpView()` 两处按钮模板内联 Feather SVG 图标）
- **R26**：导航液态玻璃 + 按钮箭头清理 + 动效扩面层（`R26:BEGIN/END` CSS + `R26-SVG/BEGIN/END`（`filter#lg-refract`）+ `R26-UI/BEGIN/END`（rAF 滚动脚本））
- **R27**：三/四级页+正文链接按钮动效扩面层（`R27:BEGIN/END` CSS + R21-UI `SEL` 扩面一行）
- **R28**：面板流体变换层（`R28:BEGIN/END` CSS + `R28-UI:BEGIN/END` JS）
- **R29**：面板液态玻璃层（`R29:BEGIN/END` CSS + `R29-UI:BEGIN/END` JS + lpView() 模板移动云盘 href 单行替换）
- **R32**：关于板块社交图标配色同步层（`R32:BEGIN/END` CSS）
- **R33**：品牌更名轮（209 处软件名替换为 Meow Star Map / 喵星图系；`localStorage` 键 `nikki_*`、`NikkiPhotos_*` 目录、`gongeo.us-nikki-tracker`、《无限暖暖》与角色引用**有意保留**）
- **R34**：一级界面 Apple 发布会风格层（`R34:BEGIN/END` CSS：Inter 内嵌、`--color-*` 语义 token、四套 landing 配色主题）
- **R35**：全站 Apple 视觉延伸层（`R35:BEGIN/END` CSS：字体栈、`--r-card`、流式字号）
- **R36**：Apple 收尾层 + Noto Sans SC 中文字体子集化（`R36:BEGIN/END` CSS + `R36-UI:BEGIN/END` JS：四枚配色色点 + `nikki_lp_theme`）
- **R37**：Apple 风格 Bento Grid 便当布局层（`R37:BEGIN/END` CSS + `R37-UI:BEGIN/END` JS；详见「R37 勘误（20261026）」全量口径）
- **R38**：三态外观层（`R38:BEGIN/END` CSS + `R38-UI:BEGIN/END` JS：`html[data-look]` + `nikki_look`）
- **R39**：苹果式排版阶梯层（`R39:BEGIN/END` CSS，纯 CSS 零 JS/DOM/文案）
- **R40**：产品介绍二级页与 `.pg-*` / `.lpx-*` 小卡体系（`R40:BEGIN/END` CSS + `R40-VIEW:BEGIN/END` 模板 + `R40-UI:BEGIN/END` JS）
- **R41**：卡片行尾整行详情面板层（`R41:BEGIN/END` CSS + `R41-UI:BEGIN/END` JS）
- **R42**：三卡迁移至二级页 + 顶部常驻 GitHub 入口（`R42:BEGIN/END` CSS + `R42-VIEW:BEGIN/END` 模板）
- **R43**：软件图标层（`R43:BEGIN/END` CSS + `R43-ICON:BEGIN/END` head link 对；六处 `📷` 就地替换）
- **R44**：**无注释对**——`pgDownloadView()` 内单行就地替换为 11 行资源下载卡
- **R45**：landing 暗底舞台色彩作用域收口（`R45:BEGIN/END` CSS + `R45-UI:BEGIN/END` JS）
- **R46**：教程数据惰性解析（`R46:BEGIN/END` JS：主脚本内 `ensureTut()`）
- **R47 / R48 / R49**：**只改载荷、不新增注释对**——R47 教程截图 PNG→WebP q90、R48 注入截图惰性解码（`loading="lazy"` + `decoding="async"`）、R49 Inter 可变字体子集化；详见「R46–R49 勘误」
- **R50**：**只改载荷、不新增注释对**——单文件版无损 WebP + 多文件版 `site/` 架构；详见「R50 勘误」
- **R51**：i18n 探针（无 CSS/JS 层，产出 `tests/r51_i18n_check.py` + `tests/i18n_pin.py`）
- **R52**：六语国际化（`R52-I18N-UI/RTL/FONT` 三段 CSS + `I18N-DATA` 词典块 + `I18N` 运行时块）
- **R53**：一级首页布局节奏层（`R53-HOME-RHYTHM:BEGIN/END` CSS，纯 CSS，作用域限 `body[data-view="landing"] #app .lp-root:has(.lpx-stats)`）
- **R54**：常驻导航主入口布局（`R54:BEGIN/END` CSS + `LP-NAV` 结构新增 `.lp-routes` / `.lp-actions` 两层）
- **R55**：常驻导航文字间距统一（`R55:BEGIN/END` CSS，七入口内容宽度 + 统一 padding 与字号）

每层可独立回滚：删除对应注释对之间的 CSS 块即可（**非纯追加的例外**：R37 两处令牌、R43 六处图标、R44 单行替换、R54 `LP-NAV` 两个包裹 `div`）。

## 快照与历史归档（现状）

- **本工作树不含整文件快照目录**：`backups/`、`*.backup-*.html`、`gui-test-screenshots/` 都在 `.gitignore` 内。历史命名格式为
  `Meow Star Map 官网.backup-<标记>-<日期>.html`（R25 起）或 `用户使用教程.backup-<标记>-<日期>.html`（R24 及之前），
  快照实体存于父仓库 / 外部留存。**当前工作树没有快照**，故 R43 起各轮只能删注释对回滚，不能「还原整文件」。
- **父仓库口径（仅作历史溯源，本工作树不存在）**：`p9`→P9精修、`r8`→R8精修、`r14`→R14全设备适配、`r15`→R15精修、
  `r18`→R18一级首页与路由重构、`r19`→R19一级首页聚焦重构、`r21`→R21一级首页收纳与全局动效、`r22`→R22高级动效与交互、
  `r23`→R23深化动效、`r25`→R25按钮规范对齐、`r26`→R26导航液态玻璃、`r27`→R27按钮动效扩面、`r28`→R28面板流体变换、
  `r29`→R29面板液态玻璃与按钮浅蓝。这些轮次报告已于 2026-10-06 清理删除。
- **一次性工作区**：`.i18n-tmp/`（R52 改造前的整文件备份 + 探针日志 + 一次性补丁脚本）已被 `.gitignore` 排除，
  属可丢弃的临时产物，**不入库、不作为回滚依据**。

## 路由速查（R55 起）

| Hash | 视图 | 说明 |
|------|------|------|
| `#/` | `landing` | 一级首页（关于+下载聚焦；唯一出口 = hero CTA / lp-nav「进入」→ `#/identity`；「资源下载」按钮展开三网盘下拉面板；未知 hash 也回落至此）。R54 起导航结构为 `.lp-routes`（四条产品路由）+ `.lp-actions`（进入 / 下载 / 关于）+ `.lp-gh` GitHub 圆钮 |
| `#/features` | `landing` | 二级页「功能总览」（R40 建；R42 吸收产品介绍卡 → title/lead 即卡内两句 + §1 三张要点小卡） |
| `#/resonance` | `landing` | 二级页「共鸣录」（R42 吸收共鸣录横幅卡；页尾残留大 banner 已拆为 h2 + pg-tip + pg-link） |
| `#/privacy` | `landing` | 二级页「隐私与本地数据」 |
| `#/download` | `landing` | 二级页「下载与支持」（R42 起 FAQ 已迁出，新增「开始使用」入口小卡；R44 起首区块为 GitHub Releases 卡 + **资源下载卡**（迅雷 / 百度 / 移动云盘三链，内容逐字复用一级首页 `#lp-dl-menu`） |
| `#/download/start` | `landing` | **三级页「开始使用」**（R42 建，承载版本 / 系统要求 / 三步 / FAQ；`pgShell` 尾参返回 `#/download`；深链 `#/download/start@faq` 可用） |
| `#/tutorial` | `home` | 教程首页 |
| `#/all` | `all` | 连续阅读 |
| `#/mX`、`#/mX/mYpZ` | `module` / `page` | 教程模块页 / 详情页 |
| `#/dev`、`#/dev/...` | `dev` | 开发者工作台（板块/子分类/文档） |
| `#/identity` | `identity` | 身份选择门（L1 CTA / lp-nav「进入」/ 顶栏「切换身份」进入；门页含返回 L1 链接） |

教程数据块（`#tut-data`，行 L2723，21,358,276 字符）内的 47 处 `#/mX` 内链与路由前缀解耦，改动路由时**严禁触碰数据行**。
R50 起该块内 48 张截图改为无损 WebP（行长度由 30,924,428 变为 21,358,276，仅图片载荷变化）；R52 起 `#tut-data` 与 `#dev-data` 长度逐位不变。

> 语言切换走 `?lang=` 查询参数或 `localStorage.nikki_lang`，**不新增路由**；`html[lang]` / `html[data-lang]` 驱动文案与字体栈，`html[dir="rtl"]` 驱动阿拉伯语镜像层。

> **R50 勘误（20261116）**：当前文件 = R49 基线 + **R50 性能/极速加载**（`性能/极速加载` 分支，从 `main` 新建）。两项交付：
> **① 单文件版**：`#tut-data` 内 48 张 1400×900 截图由 PNG 换为**无损 WebP**（`lossless, method=6, exact`），图片载荷 22.09 → 15.25 MiB；整文件 34,547,054 → **24,980,902 B**（相对 main 的 34,851,151 降 28.3%）。只替换图片载荷：`#tut-data` 之外的 head/tail 逐字节相同、JSON 去载荷后深度等价、CRLF 计数 5058 / `</script>` 24 不变、48/48 解码后与 PNG **逐像素相同**、22 个 JS 块 `node --check` 通过、零外链不变量全等（link 2 data: / script src 0 / iframe 0 / 外链 img 0 / url(http) 0 / @font-face 2 / img 53 / style 1）。工具链：`perf/tools/{extract_shots,convert_shots,build_lossless}.py`。
> **② 多文件版 `site/`（线上部署）**：首屏 `site/index.html` 1,186,206 B（1.13 MiB；字体与图标仍内联，保证 `file://` 可用），教程数据 69,450 B、开发者文档 2,088,814 B、48 张截图 15,991,294 B（按页 / `#/all` 也 lazy）、关于二维码 238,007 B（外置 + lazy）。教程/开发者数据改为 classic script 按需加载（非 fetch/module，file:// 不触发 CORS）；路由未就绪先渲染占位、加载完成自动重渲；入口 hover 与空闲时预取。实测（Chromium 147 headless，本地 HTTP，无压缩）：首屏传输 1.20 MiB vs 单文件 32.95 MiB（**27.5×**），FCP 112 vs 332 ms、DCL 226 vs 1036 ms；`#/all` 只请求 3/48 张图。工具链：`perf/tools/build_site.py`；报告口径已并入本文件「R50 勘误」与根 `README.md`「性能与构建工具链」（原 `perf/README.md` 已于 20261126 清理删除）。
> **③ 验证**：10 路由功能签名（view/title/h1+h2/links/imgs/textLen/sidebar/broken）与 console/pageerror/requestfailed 逐项与原文件相同（`file://`）；8 场景 × 3 产物截图对比 16/16 PASS（10 项逐像素相同，6 项 ≤2/255 文字抗锯齿抖动；证据 `perf/reports/shots-diff.json`）。仓库探针：r37 32P/1F/2N、r38 27P/1F/2N、r39 23P/0F/1N、r41 25P、r42 39P、r43 25P/0F/1N、r45(--skip-slow) 65P。仅两处探针口径随数据变更调整：`r45 A7` 冻结行长度 30924428 → **21358276**（dev 1545974 未动）、`r43 A6` 改为按**母图载荷本体**计数（原「全文件仅 1 处 webp data URI」在截图 WebP 化后必然为 49 处）。已知失败均非 R50 引入：r37 F2 的 `sidebarLinks` 两格（47→130，R46 惰性侧栏 + 同文档 hash 状态残留，沿 `tests/r46-r37-f2-diff.txt` 口径）、r38 U5 的 scroll 关闭（把 `main` 原件换回后同样 FAIL，`perf/reports/probes/r38-main-baseline.txt`，属 Chrome 147 时序）。html5lib strict 在 25 MB 文件上本机 >20 min 无结果，记 NOT-RUN。
> 回滚：单文件 `git checkout main -- "Meow Star Map 官网.html"`；多文件删除 `site/` 与 `perf/`（`perf/assets`、`perf/dist` 本就不入库）；探针 `git checkout main -- tests/r45_theme_scope_check.py`。

## R52 勘误（20261117）

**范围**：营销侧（落地页 / 5 个二级页 / 页脚 / 关于 / `#lp-nav` / 下载面板 / 配色·外观·主题 / 卡片详情）
提供 **zh en fr es ru ar** 六语；工作区侧（身份门 / 教程族 / 开发者页框）只做 **zh + en**；
**开发者文档库正文永久不提供译文**（产品决定，写入 `locales/README.md`）。

**依赖（唯一新增，内联）**：`i18next` **23.16.8** UMD（MIT，48,727 B，
`sha256 f2e7de67e383d73a5dec769e0829ce3406e3e9eaaf61d269178788afd7a06120`，下载日 2026-11-17），
内嵌于 `<!-- I18N:BEGIN … I18N:END -->`，与 MOTION 块内嵌 GSAP 同一范式。**不用 CDN**：
会破「零外链」不变量（`<script src>` 恒 0）且 `file://` 双击形态失效。Node/Python 侧零新增依赖。

**结构**：
- 译文＝`locales/ui.{en,fr,es,ru,ar}.json` + `locales/tutorial.en.json`（编辑入口）；
  `perf/tools/build_i18n.py`（stdlib）做 `--extract / --check / --write`，把译文幂等注入
  `#i18n-<lang>` 与 `#i18n-tut-en` 数据块。
- 中文**不搬进字典**：源码里 `T('key','中文原文')` 的第二个参数就是 zh 兜底，`LANG==='zh'` 时短路不查表，
  因此改造前后中文输出逐字节同文（r37 F1/F2、r39 textLen、r42 逐字断言零重落）。
- 引擎 `<!-- I18N -->` 块在任何渲染脚本之前执行（位于 `#dev-data` 之后、MOTION 之前），
  暴露 `window.__i18n`（`t/tc/set/apply/boot/tutPage/tutMod/tutHome/bi/noticeHtml`）与全局 `T/TN`。
- 语言判定链：`__i18nPin > ?lang= > localStorage.nikki_lang > navigator.languages > zh`。
  `__i18nPin` 专供探针确定性钉 zh（Chromium 默认 en-US，否则 7 支探针基线成片失配）。
- 教程译文走**独立数据包**且不复制图片：`{{imgN}}` 占位 + 运行时按序回填原 `<img>`（总数 48）。
  合并层 `i18nTutApply()` 就地改写 `DATA.pages/modules/home`，侧栏/面包屑/翻页/搜索/封面墙因此零改动跟进。

**RTL（阿拉伯语）**：`html[dir="rtl"]` 追加式镜像层（`R52-I18N-RTL`），显式镜像 `#sidebar`/`#app` 三段内边距/
`.sb-pages` 缩进与 `::before`/搜索框/`.lead`/`blockquote`/`.pager a.next`/FAB 等；逻辑方向与 bidi 交给浏览器；
`pre/code/kbd/.d-code` 强制 `direction:ltr`；标题 `letter-spacing:0`（负字距会切断阿拉伯连写）。
零 `!important`、零新 hex。

**已知限制**：① 内联 Inter 子集（R49，381 码位）只覆盖站内既有西文，法语/西语重音字符、西里尔、阿拉伯文
按字形回落系统字体（`html[data-lang]` 配了分语种字体栈）；② 阿拉伯语量词统一取复数形式；
③ 工作区侧在 fr/es/ru/ar 下是英文 + 一行双语通告（`ui.notice.bi`），语言菜单仍展示 6 项。

**验证**：`python perf/tools/build_i18n.py --check`（359 键；分层 parity / 空值 / 非法字符 / 教程占位 48 /
零外链 / 8 条 build_site 锚点 / 数据行长度 21358276·1545974 逐位不变）；
`python tests/r51_i18n_check.py`（**70/70 PASS，0 SKIP**：源码级 + 运行时级 + 六语×四断点溢出）；
`python perf/tools/build_site.py`（再生 `site/`，首载 1.19 → 1.34 MiB，`<script src>` 仍 0）。

**回归记录（8 支既有探针 + html5lib，2026-11-17 收尾）**

| 探针 | 结果 | 备注 |
|---|---|---|
| r37 Bento | 33 PASS / 1 FAIL / 1 SKIP | FAIL＝F2 的 2 格 `sidebarLinks` 47→130（已签认，见 `tests/r52-r37-f2-diff.txt`）；SKIP＝R6 本机 playwright 无 reduced_transparency 形参 |
| r38 视觉 | 30 / 30 | — |
| r39 排版 | 24 / 24 | — |
| r41 卡片详情 | 25 / 25 | 首轮 F3 FAIL 暴露真实缺口，见下 |
| r42 迁移 | 39 / 39 | — |
| r43 图标 | 25 / 0 FAIL / 1 NOT-RUN | NOT-RUN＝B1 的 `!DEV` 兜底槽位，dev-data 在位故不渲染（设计如此，A12 源码级覆盖）|
| r45 色彩作用域 | 65 / 65 | G1（769–900 档增量 ≤58px）未被语言触发器破坏 |
| S1 html5lib | 0 error / 0 类 | 输入改二进制流后恢复可用（见下）|

**回归中发现并修掉的三个真实缺口**

1. **R41 `__r41.open(k)` 的键口径**：`keyOf()` 改读 `data-dt` 后，按中文标题调用（r41 F3、既有外部调用方）
   全部落空 → `open()` 增加标题回退匹配，两种口径并行，探针零改动即恢复。
2. **`setLang()` 对非法语种谎报成功**：`norm('xx')||'zh'` 会把 `xx` 归一成 `zh` 并因「同语言」返回 `true`，
   选择器与界面状态可能不一致 → 改为显式 `return false` 且不落任何状态；`?lang=xx` 仍安全回落。
3. **r37 `errs()` 用文本流喂 html5lib**：25MB 文档在编码嗅探阶段抛 `UnicodeDecodeError` →
   改二进制打开（html5lib 的输入契约），S1 恢复为真实报错类型数（当前 0 类）。

外加 r43 `SLOT_MARKUP` 两处锚点随源码同步：槽位标签已改为 `T('dev.sbTut',…)` 调用，
标记更新为新的逐字形态（`A9` 仍要求六条各命中 1 次，实测 1/1/1/1/1/1）。
**生成器唯一改动**：`build_site.py` 里 `for old in SHOTS.glob("*.webp"): old.unlink()` 已移除——
批量 unlink 在受管/沙箱环境会被 safe-delete 守卫拦截并 10s 超时；截图文件名由「内容 SHA → owner-NN」
决定且稳定，重跑直接覆盖，无需预清理（本轮实测 48 张、`problems: []`）。

**回滚**：删 `<!-- I18N:BEGIN/END -->` 与 `<!-- I18N-DATA:BEGIN/END -->` 两对、CSS 三段
（`R52-I18N-UI` / `R52-I18N-RTL` / `R52-I18N-FONT`）、主脚本 5 处挂点（`T/TN` 别名、`i18nTutApply` 及其调用、
`__i18n.boot()`、两个缓存失效钩子）、R38 `optsHtml/relabel`、R36/R45 的 `i18n:change` 监听、
`<title>` 上的 `data-i18n`（已移除）；再删 `locales/`、`perf/tools/build_i18n.py`、`tests/i18n_pin.py`、
`tests/r51_i18n_check.py` 及 7 支探针内的两行 pin。`#tut-data`/`#dev-data` 全程未动（长度与基线逐位相同）。

---

## R53 勘误（20261125 · 工作树未提交）

**范围**：唯一源文件 `Meow Star Map 官网.html` 的 `</style>` 前新增
`/* ══ R53-HOME-RHYTHM:BEGIN … R53-HOME-RHYTHM:END ══ */` 纯 CSS 层（L2575–2652）。
零 JS、零 DOM、零文案、零路由、零 locales、零字体子集、零数据块、零外链、零新 hex、**零不可追加项**。

**问题与目标**：一级首页自 R40 起沿用二级页的 `.lpx-*` 小卡栅格，区块宽度、栅格列数与留白在同一份 CSS 里
与 landing hero / 关于板块 / 页脚各写一套，导致首页纵向节奏与其它视图不统一。本轮把首页的排版节奏集中到一个
**只作用于一级首页**的作用域内重写。

**作用域（本轮成立的前提）**：所有规则挂在
`body[data-view="landing"] #app .lp-root:has(.lpx-stats)` 之下。`.lpx-stats` 只存在于一级首页，
四个二级页 / 三级页走 `.pg-*` 体系不命中该选择器，故本层**不会外溢到营销二级页**。
`:has()` 需 Safari ≥ 15.4；不支持的引擎整层不生效 → 回落改前布局，内容仍可读、不破版。

**内容**：
① 区块容器 `.lpx-section` 宽 `min(1440px, calc(100% - 64px))`、上留白 88px；
② `.lpx-stat-grid` 改 4 列（gap 20px），`.lpx-stat` 内距 `32px 24px`；
③ `.lpx-card-grid` / `.lpx-adv-grid` 改 3 列（gap 24px），`.lpx-card` 内距 32px；
④ 触控目标补齐：`.lpx-more` / `.lpx-det-link` 最小高 44px，页脚链接 `min-height:44px`；
⑤ 正文节奏：`.lpx-card p` 与 `.lpx-det-list li` 行高 1.65；
⑥ 关于板块 `.about-sec` 宽 `min(880px,100%)`、页脚 `.lp-footnav` 3 列（gap 32px）；
⑦ 断点档：`≥961px` 大屏档（区块宽 + 导航内边距按视口居中 + hero 留白）；`641–960px` 档 2 列栅格；
`≤640px` 档 1 列卡片栅格、stats 2 列、页脚 2 列；`max-height:720px` 矮视口收紧 hero / 关于 / 页脚；
⑧ RTL：`html[dir="rtl"]` 下 `#app` 内距归零（逻辑方向已由浏览器接管）；
⑨ 阿拉伯语：`html[data-lang="ar"]` 下卡片正文与详情列表行高提到 1.85。

**验证**：R53–R55 期间常驻探针结果见「R54 / R55 勘误」的回归记录（r42 39/39、r43 25 PASS / 0 FAIL / 1 NOT-RUN、
r45 72/72、r38 29 PASS / 0 FAIL / 1 NOT-RUN、r41 22 PASS / 0 FAIL / 1 SKIP、r51 69 PASS / 0 FAIL / 1 SKIP、
r37 32 PASS / 1 FAIL / 2 NOT-RUN，唯一 FAIL 仍是已签认的 F2 `sidebarLinks 47→130` 同文档残留）。

**已知限制**：① `≤640px` 档卡片改单列后，首页纵向长度显著增加；② 阿拉伯语行高单独提档，未做逐语种排印精修；
③ 本层依赖 `:has()`，旧引擎整层失效。

**回滚**：删除 `R53-HOME-RHYTHM:BEGIN/END` 之间全部内容（纯追加，无不可追加项），随后运行
`python perf/tools/build_site.py` 再生 `site/`。

## R54 常驻导航主入口布局（20261125）

**范围**：唯一源文件 `Meow Star Map 官网.html` 的 `LP-NAV` 结构与 `</style>` 前新增
`/* ═══ R54:BEGIN … R54:END ═══ */` 纯 CSS 层；`site/index.html` 由 `build_site.py` 再生。
零 JS、零文案、零路由、零 locales、零字体子集、零数据块、零外链、零新 hex。

**问题与目标**：`进入 / 下载 / 关于` 与四条产品路由及全部控件共用 `.lp-links` 横滚预算，
三个主入口缺少防收缩与禁止换行规则。旧实现实测 390px 中文主入口被压成两行，641px 法语
`.lp-links` 溢出 278px，部分按钮文字被裁切。

**结构（非纯追加）**：四条 `.lp-nav-link` 原样包入 `.lp-routes`；`a[href="#/identity"]`、
`#lp-dl-link`、`#lp-about-link` 原样包入 `.lp-actions`。顺序、ID、class、`data-route`、
`data-i18n`、href、按钮类型与事件处理不变；三个主动作不加 `.lp-nav-link`，避免被 `syncNav()` 当路由项。

**布局**：`.lp-links` 使用剩余宽度并限制 `max-inline-size:min(100%,1080px)`，避免超宽屏过度拉伸；
`.lp-routes` 独立横滑并隐藏滚动条；`.lp-actions` 占据剩余空间，`≥641px` 三个主动作严格三等分、
单行、居中，组宽按三格最长译文预留；外层与组间距使用 `clamp(8px,1.25vw,22px)`。
`≤640px` 沿用 R42 的 `#lp-dl-link{display:none}`，两个可见主动作不产生空列；`≤400px` gap 收到 4px。
品牌窄屏 `line-height:1.1`，保证 360px 三行紧凑文本也不超出 52px 栏高。全部新增几何使用逻辑属性，RTL 自然镜像。

**用户确认的取舍**：① `≤640px` 保留现有重复下载按钮隐藏规则；② 窄屏允许四条产品路由独立横滑，
优先保护主入口完整可见。未取消或替换任何既有功能。

**验证**：

- 新增 `tests/r54_nav_actions_check.py`；旧实现快速用例 27 PASS / 11 FAIL，复现两行、裁切与溢出。
- 改后单文件与 `site/index.html` 完整矩阵各 **727 PASS / 0 FAIL**：9 宽度 × 6 语 × 明暗、
  6 个 landing 路由、等宽/等距/单行/不裁切/不重叠/路由可滚/功能冒烟/console 双零。
- `build_i18n.py --check` 通过；数据行长度 21358276 / 1545974 不变，CRLF 与零外链契约保持。
- `build_site.py` 通过，`site/index.html` 1,418,076 B（1.35 MiB），48 张截图不变。
- r42 完整 39/39；r43 完整 25 PASS / 0 FAIL / 1 NOT-RUN；r45 完整 72/72。
- r38 29 PASS / 0 FAIL / 1 NOT-RUN；r39 23 PASS / 0 FAIL / 1 NOT-RUN；r41 22 PASS / 0 FAIL / 1 SKIP
  （均按脚本支持项跳过慢检，导航完整矩阵由 R54 覆盖）。
- r51 69 PASS / 0 FAIL / 1 SKIP；本机 Python 不支持 `Path.read_text(newline=...)`，运行时用等价的
  `Path.open(newline="")` 兼容入口执行，未改探针或产品代码。
- r37 32 PASS / 1 FAIL / 2 NOT-RUN；唯一 FAIL 仍是已签认的 F2 `sidebarLinks 47→130` 同文档残留，
  见 `tests/r52-r37-f2-diff.txt`，其余功能轴零差异，不重落基线。
- html5lib 对剥离两条巨型数据脚本后的结构副本校验 **0 error / 0 类**；浏览器实查 1440/390 截图见
  `tests/r54-shots/desktop-1440.png`、`tests/r54-shots/mobile-390.png`。

**已知限制**：① `≤640px` 按既有规则只显示“进入 / 关于”两个主动作，下载页仍由路由“下载”进入；
② 极窄屏路由文字需要在 `.lp-routes` 内横滑，主入口与控件保持可见；③ 360px 品牌可能压缩为三行，
但行高已收至 1.1，实测高度不超过 52px。

**回滚**：删除 R54 CSS 注释对之间全部内容，并移除 `LP-NAV` 中 `.lp-routes` / `.lp-actions`
两个包裹 `div`（保留其子节点原顺序）；随后运行 `python perf/tools/build_site.py` 再生 `site/`。

---

## R55 常驻导航文字间距统一（20261125）

**范围**：唯一源文件 `Meow Star Map 官网.html` 的 `</style>` 前新增
`/* ═══ R55:BEGIN … R55:END ═══ */` 纯 CSS 层；`site/index.html` 由 `build_site.py` 再生。
零 DOM、零 JS、零文案、零路由、零 locales、零字体子集、零数据块、零外链、零新 hex。

**问题**：R54 的四条产品路由按内容宽度排列，三个主动作却占等宽 flex 格，导致实际文字边缘距不一致。
用户确认统一全部七个文字入口（功能 / 共鸣录 / 隐私 / 下载 / 进入 / 下载 / 关于），按文字布局边缘距验收。

**实现**：R55 覆盖 R54 的等宽分配部分：`.lp-links` 恢复 `flex:0 1 auto` 并按内容宽度整体靠右；
`.lp-actions` 恢复内容宽度；七个文字入口统一 `flex:0 0 auto`、`padding-inline:2px`、`white-space:nowrap`、
基础 `font-size:13.5px`，`≤560px` 统一 12.5px。继续共享 `clamp(8px,1.25vw,22px)` gap，
`≤400px` 为 4px；路由独立横滑、`≤640px` 隐藏重复下载按钮、RTL 逻辑属性均保持不变。
相邻文字边缘距理论值为 `gap + 左右 padding`，不再把剩余宽度塞进主动作格内。

**探针**：`tests/r54_nav_actions_check.py` 扩展为七入口采样，使用 `Range.getBoundingClientRect()` 验收文字边缘距，
删除等宽/中心等距断言；保留单行、不裁切、不重叠、无页面溢出、功能冒烟与 console 双零。
路由首尾验收改为“滚动到边界并正确对齐”，极窄屏单条路由比滚动区更宽时不再强求整条同时完整可见。

**验证**：

- 旧 CSS 快速基线 54 PASS / 10 FAIL：641px 法语边缘距差 26.6px，1440px 中文差 135.5px，
  390px 路由/主动作字号差 1px。
- R55 单文件与 `site/index.html` 完整矩阵各 **2580 PASS / 0 FAIL**：13 宽度 × 6 语 × 明暗、
  6 个 landing 路由 × 3 宽度 × 3 语、七入口边缘距/字号/padding/gap/路由可达/功能冒烟。
- `build_i18n.py --check` 通过；数据行 21358276 / 1545974 不变，CRLF 5741/5741，R55 注释对各 1 对。
- `build_site.py` 通过，`site/index.html` 1,418,802 B（1.35 MiB），48 张截图不变。
- r42 完整 39/39；r43 完整 25 PASS / 0 FAIL / 1 NOT-RUN；r45 完整 72/72。
- r38 29 PASS / 0 FAIL / 1 NOT-RUN；r41 22 PASS / 0 FAIL / 1 SKIP；r51 69 PASS / 0 FAIL / 1 SKIP。
- r39 低负载复跑 22 PASS / 1 FAIL / 1 NOT-RUN；唯一 FAIL 为 T13 打印采样得到 48px 旧路由标题，
  期望 30px。R55 选择器仅作用于 `#lp-nav`，未改 h1 或打印规则；按路由切换后的探针采样状态问题保留，
  不改产品代码或冻结断言。
- html5lib 对剥离两条巨型数据脚本后的结构副本校验 **0 error / 0 类**；浏览器实查 1440/390 截图已更新。

**已知限制**：① `≤640px` 仍只显示“进入 / 关于”两个主动作；② 极窄屏单条长路由可能比 `.lp-routes`
可视区更宽，此时只能对齐滚动边界，不能与相邻项同时完整显示；③ 文字间距按 Range 布局盒度量，不承诺逐字形墨迹像素级等距。

**回滚**：删除 R55 CSS 注释对之间全部内容，然后运行 `python perf/tools/build_site.py` 再生 `site/`；
R54 结构与行为自动恢复。专项探针若需回退到 R54 口径，应同步恢复等宽/中心等距断言。

---

## 文档清单与维护口径（20261126）

本仓库的 `.md` 文档共 11 份，维护口径如下：

| 文件 | 定位 | 维护口径 |
|---|---|---|
| `AGENTS.md` | 常驻开发者文档：结构索引、逐轮勘误、开发约定、回滚方式 | **每轮改动后追记**（范围 / 契约影响 / 验证 / 已知限制 / 回滚）；结构表与锚点按当前基线刷新 |
| `README.md` | 项目入口说明：是什么 / 怎么跑 / 怎么测 / 契约 / 第三方资产 | 随基线与体积刷新，数值须实测 |
| `CONTRIBUTING.md` | 贡献指引（提炼 AGENTS.md 既有约定，不另立新规） | AGENTS.md 约定变更时同步 |
| `SECURITY.md` | 安全问题披露指引 | 极少变动 |
| `CODE_OF_CONDUCT.md` | 行为准则 | 极少变动 |
| `locales/README.md` | i18n 译文编辑流程与键归属口径 | 键表结构变化时同步 |
| `site/README.md` | 多文件版产物的部署说明 | 随 `site/` 产物刷新 |
| `.github/ISSUE_TEMPLATE/*.md`、`.github/PULL_REQUEST_TEMPLATE.md` | GitHub 协作模板 | 探针清单与契约清单变更时同步 |

**新增文档的门槛**：轮次报告、临时计划、一次性取证脚本产物一律**不入库**；需要留证的结论写进对应轮次勘误或 `perf/reports/`。
本工作树**只有这一份常驻开发者文档**，不设 per-round 报告文件。

**20261126 清理结果**：物理删除 `perf/README.md`——它是 R50「性能/极速加载」分支期的冻结性能报告：
所述分支已合并进 `main`；`site/` 体积数字已被 R52/R54/R55 超越（1.13 MiB → 1.35 MiB）；
工具清单缺 `build_i18n.py`（照其操作会得到一份缺 i18n 词典的 `site/`）；
「回滚：多文件版删除 `site/` 与 `perf/`」的建议在 i18n 落地后会误删构建工具链。
其中仍然有效的工具链用法与实测口径已迁入根 `README.md`「性能与构建工具链」与本文件「R50 勘误」。


