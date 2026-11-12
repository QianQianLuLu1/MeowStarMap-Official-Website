# AGENTS.md — Meow Star Map 开发者网页

## 项目结构概述

单文件静态教程站点，无构建工具、无框架依赖（指站点本体；测试工具链的运行时与依赖声明见下文「环境装配与工具链路由」章节）。

```
Meow Star Map 官网.html ← 唯一源文件（3516 行，R21 完成态于 R25 更名承接 + R26 + R27 + R28 + R29 + R31 增量 + R32/R33/R34/R35/R36 + R37 Bento Grid 层；R22/R23 高级动效不在当前基线），包含全部 HTML / CSS / JS
package.json         ← npm scripts 入口（setup/doctor + smoke/审计/交互/回归）+ engines.node 版本声明
Makefile             ← make 入口（与 npm scripts 同构；本机未装 make，npm 为主用路径）
requirements.txt     ← Python 依赖锁定版本（playwright/html5lib，唯一声明来源）
tests/               ← GUI 审计脚本 + 注入脚本 + 对比工具
  gui-audit.js         黑盒只读审计（Playwright 页面上下文执行）
  r14_harness.py       全设备响应式校验驱动（Python + Playwright）
  r14_compare.py       基线 vs 修改后截图/审计对比
  r15_interactions.py  交互回归套件（搜索/主题/下载面板/微信弹窗/抽屉/路由直达；R26 起默认页指向「Meow Star Map 官网.html」，R25 更名的迁移遗漏已补）
  r17_interactions.py / r17_matrix.py  R17 交互扩面与多引擎矩阵
  r18_landing_check.py 一级首页专项巡检（R21 起按新口径断言：单一 CTA + 资源下载下拉面板 + 关于板块首屏可见）
  r19_probe.py         R19 探针（R21 口径 27 项：L1 结构/面板开合/回弹涟漪取证/门页分流/弹层回归/主题三态）
  r19_w3c_check.py     R19 HTML5 规范解析校验（html5lib，before/after 对比）
  r20_icons_cta_check.py  R20 网盘图标贴片 + R25 按钮规范校验（file:// 加载，硬编码精确色值/圆角/线框/图标断言）
  r22_motion_check.py  R22 动效探针（24 项：FLIP 终态/残影壳/滚轮阻尼落位/顶底橡皮筋/速度吸附/弹簧级联/reduced-motion 降级/CLS，端口 8661）
  r23_refine_check.py  R23 深化探针（18 项：__r23 钩子与 CFG/setCfg 断言/残影壳 transform 驱动取证/toc sticky 冻结/顶部不补偿/reduced-motion/CLS/390，端口 8662）
  r24_file_check.py    R24 file:// 全路由普查（双协议可用性：路由矩阵 data-view/未知回落/双视口横向溢出/主题映射不变量+刷新持久化/console 普查，无端口）
  r26_nav_glass_check.py  R26 导航液态玻璃探针（23 项：箭头清零/折射声明/高光扫动 --lg-x/tone 亮度自适应与滞回/暗主题反转/.lp-dl-item 涟漪回弹/reduced-motion/390/console，端口 8663）
  r27_buttons_check.py  R27 按钮动效扩面探针（75 项：新覆盖控件逐类 press/波心/pop 取证（pointerdown 捕获+microtask 同源基线，消除 Playwright bb 漂移与 hover transform 过渡相位）、inline-block 计算样式、summary marker 防裁剪、键盘 Enter 中心波、reduced-motion、390 溢出/console，端口 8664）
  r28_panel_flip_check.py  R28 面板流体变换探针（24 项：r28-on 门控/lpMenuIn 屏蔽/FLIP 中段与终态几何对位/hidden 同步翻转/残影壳 fixed+z29+几何定格+双采样补间+自删/Escape 焦点归还/选项点击关闭/中段打断瞬收/路由重渲 rebind/reduced-motion 整体跳过/390 钳制分支/CLS/console 红线，端口 8665；headless 下须 gsap.ticker.lagSmoothing(false) 消除 SwiftShader 帧停顿时间膨胀）
  r29_panel_glass_check.py  R29 面板液态玻璃探针（28 项：按钮浅蓝 #8ecbff+对比度线性化口径/圆角图标/折射声明 url(#lg-refract)/半透明玻璃底/::after 高光带/--lg-x 初值 8% 与滚动位移（390×500，click 自动滚动须先回页顶）/tone 亮度自适应与 #808080 中灰滞回两侧/暗主题 tone 反转与令牌级联/移动云盘新 href 逐字/Escape/R28 ghost 出现又自删/390 溢出/reduced-motion 玻璃保留/console，端口 8666）
  r31_cards_check.py   R31 卡片三项视效探针（24 项：r31-on 门控与 __r31 钩子/倾斜中段 matrix3d 含 perspective/弹簧回正终态清内联+类移除+springs 递增/触屏拖拽倾斜+位移>8px 抑制 click 防误触/QQ 面板 morph 中段 xPercent:-50 居中基准保留+aboutPopIn 被屏蔽/QQ 终态 clearProps 无内联残留+与按钮 centerX 对位/QQ 残影壳 fixed+z71+pointer-events:none 且自删/微信弹窗 morph+遮罩淡入+ab-lock/Escape 焦点归还+残影壳 z91 自删/conic ::before 计算样式+mask 抠环+静止 opacity 0→hover 1/r31breath 动画/暗色与 dev 视图 --r31-glow 令牌切换/.gate-role 注入 .r31-ring/390 无横向溢出/reduced-motion 下倾斜与 morph 整体旁路/CLS 零新增/console+pageerror+HTTP≥400 红线，端口 8667）
  r31_links_check.py   R31 外链与外部资源校验（纯 stdlib：① 零外链资源不变量——<link>/<script src>/@font-face/url(http)/外链 img/iframe/@import 恒为 0，扫描前剥离 >100000 字符的巨型数据行避免假阳性；② outbound href 与冻结清单逐字一致；可选 `--online` 联网可达性探测，2xx/3xx 与 401/403/405/429 均判可达）
  r37_bento_check.py   R37 Bento Grid 专项探针（Playwright + html5lib + stdlib，**file:// 协议、无端口自起**；`--baseline` 落改造前功能基线 / `--skip-w3c` 跳慢检。33 项：零外链两段口径（标记级全文 + 文本级须先剥 >100000 字符巨型行，否则 dev-data 文档正文的 4 处 `@import` 假阳性）+ `@font-face{`==2 与禁用裸词口径 + 数据行按内容定位 + R37 注释对成对 + HTML 注释禁连续双连字符 + 全部 JS 块 node 编译不执行 + V1 配色四值精确（浅 #F5F5F7/#FFF、深 #1D1D1F/#000，含 `.wrap-home/.wrap-dev` 让位断言）+ V2 圆角 == clamp(16,0.07×短边,34) 逐卡、四角相等、静置零投影零渐变描边、`border-radius:inherit` 环等值 + V2b/V2c 作用域收口（非 Bento 零内联变量；`.gate-role`22/`.pagecard`24/`.quick`24/`.step`16 未被动）+ V3/V3b 网格 16px 与区块 24px + V4 Hero 跨 2×2（**断言取 grid-column-START，span 简写不写 -end**）/面积主导/轨道宽对位 + V5 空洞普查 + R1 五断点×双主题×两视图零横向溢出 + R2 单列解跨列（防 `2px 1112px` 隐式轨道）+ R3 手机档 Hero 主导 + R4 骨架同构（用等价脚手架，静态骨架在 domcontentloaded 前已被 render() 覆写）+ R8a CSS 兜底 + R8b 禁 JS 不破版 + V7 渐变文字每页≤1（transparent 须按 `rgba(0,0,0,0)` 计算值判定）+ F1/F2 七视图×双主题功能逐位比对 + F3~F11 交互回归，**本机 prefers-reduced-transparency 恒 reduce，playwright 版无该形参故双态记 NOT-RUN**）
  r43_icon_check.py      R43 软件图标层探针（Playwright + stdlib，**file:// 协议、无端口自起**；`--skip-slow` 跳四断点矩阵。26 项：源码级 A1–A12（📷 计数归零 / link 恰 2 枚且无 href 非 data: 者 / 三段 base64 解码 + PNG·RIFF-WEBP 魔数 / 母图全文仅内联一次 / R43 两对注释对成对 / HTML 注释禁双连字符 / 六处槽位标记逐字在位含 !DEV 兜底那处 / 两条巨行未触碰 / @font-face 仍 2）+ 运行时 B1–B8（五处可达槽位实测 宽=高=fontSize 即「占位=1em」/ 身份门与快捷卡瓦片圆角底色描边未被 background-image 长写吞掉 / --app-icon 在真实浏览器 new Image() 解出 256×256 / 两枚 link 的 DOM href 均 data: / 四断点×双主题×三态零横向溢出且 390 landing 品牌 ≤52px / plain 态灰度化 / console 与 requestfailed 双零 / 禁 JS 下两处静态图标样式仍生效）。口径要点：溢出矩阵不重载页面，改 data-theme/data-look 属性 + set_viewport_size 驱动级联；`.dev-actions` 那处在 renderDev 的 `if(!DEV)` 兜底分支，本构建 dev-data 在位故运行时不可达，记 NOT-RUN 并由 A9 源码级覆盖）
  r45_theme_scope_check.py  R45 landing 暗底舞台色彩作用域收口探针（Playwright + html5lib + stdlib，**file:// 协议、无端口自起**；`--skip-slow` 跳对比度矩阵与断点矩阵。69 项：A1–A11 源码级（R45 两对注释对成对 / HTML 注释禁双连字符 / 外链 link 负向前瞻 0 + 图标 link 恰 2 / script src·iframe·url(http)·外链 img 全 0 / @font-face 仍 2 / 两条数据行按内容定位且长度逐位不变 / 22 个 JS 块 node 编译不执行 / **A9 禁翻清单**：层体不得出现 `--lp-eyebrow-ink:` 等 11 个 landing 墨口与强调色族赋值 / **A10** `--card:`·`--bg:` 只允许出现在 subject 为 `#lp-nav` 或 `#look-menu` 且剥掉 `:has()` 后不含 `.lp-root` 的规则 / **A11** 改写面恰为 tx·mut·bd·card·bg·lp-ac-ink）+ B1/B2 泄漏与暗玻璃生效 + C1 `.lp-dl-btn` 精确色值未动 + D1–D3 深色与 plain 三态惰性（含 plain 下色点仍隐藏）+ E1 暗底 AA 全量 + E2 审计清单零落空 + E3 新板块卡面与既有 `.about-sec` computed 全等 + F1–F7 折叠圆钮可见性/开合/aria-expanded/选色持久化/Escape 归还焦点/hashchange 关闭/plain 豁免 + G1 视口矩阵（文档零溢出·769–900 档 `.lp-links` 增量 ≤58px·品牌 ≤52px）+ H1/H2 console 与 requestfailed 双零）。口径要点：① **对比度须扫遍整条 `body::before` 固定渐变取最劣端**，只按元素当前屏幕位置取样会系统性高估；② 前景须按祖先链合成到舞台之上，而 **body/html 自身底色在 `body::before` 之下**，误入链即把暗底判成浅底（本项目首轮即因此全报 PASS，务必照此实现任何后续对比度探针）；③ 主题态用 `localStorage.nikki_lp_theme` + reload 驱动，不手改 className；`data-theme`/`data-look`/视口用属性与 `set_viewport_size` 驱动级联，不重载；④ 卡面↔页面底分离度**不设为 3:1**（R37 已知限制② 已文档化全站基线 1.09/1.25），一致性改由 E3 的「computed 与 `.about-sec` 全等」表达。
  insert-*.mjs         分阶段 CSS/JS 注入脚本（R7/R8/P9/P13/R14/R15 等，均已生效退役，勿重跑）
  smoke.mjs            快速冒烟测试
  env_check.py         R30 环境装配/体检（--setup：装锁定依赖 + chromium + 补 smoke 基线；默认 doctor 只读体检，纯 stdlib）
  archive-r15/ archive-r16/ archive-r18/  ← 历轮结果 JSON 归档
backups/             ← 精修轮次快照（**本工作树未纳入**，命名语义见文末「备份文件命名语义」；快照在父仓库 / 外部留存）
（无根目录轮次报告：R25–R29 精修报告已于 2026-10-06 清理删除，根目录仅余 `AGENTS.md` 作为常驻文档）
gui-test-screenshots/ ← 审计截图归档（按轮次/日期分目录；**本工作树未纳入**，实际截图随各轮探针结果存放，详见各 `rNN_*.py` 说明）
```

## 环境装配与工具链路由（R30 · 20261004）

### 一次性装配与体检

| 入口 | 首选命令 | 等价形式 | 说明 |
|------|---------|---------|------|
| 装配（幂等） | `npm run setup` | `make setup` ＝ `python tests/env_check.py --setup` | ① `pip install -r requirements.txt`（锁定版）② `playwright install chromium` ③ `tests/baseline.json` 缺失时自动 `smoke:init` 补齐 ④ 末尾自动体检 |
| 体检（只读） | `npm run doctor` | `make doctor` ＝ `python tests/env_check.py` | 查 Python/Node 版本、pip 包逐位对版 requirements.txt、chromium 可无头启动、smoke 基线在位、r14 结果 JSON 前置；任一 FAIL 退出码 1，WARN 不影响退出码 |

**干净检出（clone）后必须先跑一次 setup**：`tests/baseline.json` 与 `tests/r14-*-results.json` 均被 gitignore 不入库——前者缺失时 `npm run smoke` 直接失败（setup 自动补）；后者缺失时 `npm run audit:compare` 无从对比（须先 `audit:baseline` + `audit:after`，或直接 `npm run audit:full`）。

### 声明来源（单一、可复制）

| 事项 | 唯一来源 | 执行者 |
|------|---------|--------|
| Node 版本要求（≥18） | `package.json` → `engines.node` | doctor 读取并强制校验 |
| Python 第三方依赖及锁定版本 | `requirements.txt`（R30 时点：playwright 1.60.0、html5lib 1.1，以文件为准） | setup 安装 / doctor 逐位校验 |
| Python 版本下限（≥3.8） | `tests/env_check.py` → `MIN_PY` 常量 | doctor 强制校验 |

- Node 侧**零第三方依赖**是设计事实（`smoke.mjs` 仅用 node: 内置模块），因此无 package-lock.json，npm 不新增任何依赖包。
- Python 下限 3.8 由探针实际依赖推导（`ThreadingHTTPServer` 3.7+、`sys.stdout.reconfigure` 3.7+、`importlib.metadata` 3.8+，取最高者）；历轮实测基线 Python 3.12 / Node 26。
- 探针一律 `python tests/<脚本>.py` 直跑（与 Makefile `PYTHON := python` 同一解释器口径）；**不建 venv**（未激活的 venv 会打断全部既有入口）。

### 探针路由

| 任务 | 命令（npm 为主；有 make 的环境括注等价 target） |
|------|------|
| 冒烟 | `npm run smoke`（make smoke） |
| 全设备审计三步 | `npm run audit:full`（make audit-full）＝ baseline → after → compare；compare 依赖前两步的结果 JSON |
| 交互回归 | `npm run interact:baseline` / `npm run interact:after`（make interact-baseline / interact-after） |
| 完整回归 | `npm run vreg`（make vreg）＝ 冒烟 + 审计 + 交互 |
| 现场诊断 | `npm run diag`（make diag）；`tests/r15_diag2.py` 无入口，仅手动 `python tests/r15_diag2.py` |
| 轮次专项探针（r17–r29、r31、r24、r19_w3c 等） | 直接 `python tests/<脚本>.py`（端口内嵌自起，无需手动开服务器；**不为其新增 npm scripts / make targets，避免平行工具**）。R31 另加 `python tests/r31_links_check.py [--online]`（外链不变量 + 可选联网可达性） |

> 本机（当前开发机）未装 make：make 入口供有 make 的环境使用，本机一律走 `npm run`。`.gitattributes` 已钉 `Makefile text eol=lf`（GNU make 对 CRLF 续行敏感）。

## HTML 文件章节结构索引

`Meow Star Map 官网.html`（3187 行）的完整章节地图，标注注释标记与行号范围，便于快速定位编辑目标。（**当前基线 = R21 完成态更名 + R25 + R26 + R27 + R28 + R29 + R31 增量**；下方「总览」表已于 2026-10-07 刷新为 R31 基线锚点口径，并移除已退出基线的 R22-UI 块；CSS 分区表与「可回滚注释对标记汇总」一律以 grep 锚点（`R29:BEGIN` 等）为准；行号随轮次漂移；**grep 巨型数据行务必 `cut -c` 截断输出**）

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

### 总览（R31 基线快照；绝对行号随每轮增量漂移，定位一律以 grep 锚点为准，见下方「CSS 样式分区」与「可回滚注释对标记汇总」）

| 区域 | grep 锚点 / 行号（R31 基线） | 说明 |
|------|------|------|
| `<head>` 头部 | 1–（`<style>` 止于 ~L1513） | 防闪烁脚本（`THEME:BEGIN/END`）+ 全量 CSS + title |
| `<body>` 静态骨架 | L1515 起 | Landing 导航 / 顶栏 / 遮罩 / 侧栏 / 主内容区（骨架屏） |
| 内嵌数据块 | `<body>` 内 `#tut-data` / `#dev-data` | 用户教程 JSON + 开发者文档 JSON（**严禁触碰**，smoke 以 SHA 冻结；**R33（20261024）品牌更名注记**：已按指令将数据块内软件名 NikkiGallery / nikkiGallery / WXNN XiangCe / 无限暖暖相册管理工具 / NikkiGalleryManifest / NikkiGallery-Setup / __NIKKI_PRELOAD_DEV__ 统一替换为 Meow Star Map / meowStarMap / 喵星图 / MeowStarMapManifest / MeowStarMap-Setup / __MEOWSTARMAP_PRELOAD_DEV__（共 209 处），SHA 冻结基线失效，后续从父仓库重建数据需以新名口径为准；`localStorage.nikki_theme`/`nikki_role` 键与游戏目录 NikkiPhotos_*、第三方仓库 gongeo.us-nikki-tracker 有意保留） |
| `<!-- MOTION -->` 块 | `MOTION:BEGIN`（L1542–1567） | GSAP 3.13.0 内嵌库（核心 + ScrollTrigger，含 Observer；无 ScrollToPlugin/Flip/CustomEase） |
| 主脚本（路由 + 渲染） | MOTION 块之后 | 数据解析 / 侧栏 / 视图渲染 / hash 路由 |
| `<!-- ENHANCE -->` 块 | `ENHANCE:BEGIN`（L2150–2365） | 三次精修交互增强 |
| `<!-- THEME-UI -->` 块 | `THEME-UI:BEGIN`（L2366–2427） | 主题切换按钮 UI（topbar `#themebtn` + lp-nav `.lp-themebtn` 双挂载） |
| `<!-- ATM-UI -->` 块 | `ATM-UI:BEGIN`（L2428–2446） | 漂浮几何氛围层 |
| `<!-- TOAST-UI -->` 块 | `TOAST-UI:BEGIN`（L2447–2489） | Toast 通知队列 |
| `<!-- ABOUT-UI -->` 块 | `ABOUT-UI:BEGIN`（L2491–2582） | 关于板块（社交+微信弹窗）+ 微信二维码弹窗 |
| `<!-- R21-UI -->` 块 | `R21-UI:BEGIN`（L2583–2707） | 资源下载下拉面板状态机 + 全局按钮按压回弹/坐标涟漪 |
| `<!-- R26-SVG -->` 块 | `R26-SVG:BEGIN`（L2708–2718） | 导航液态玻璃折射滤镜 |
| `<!-- R26-UI -->` 块 | `R26-UI:BEGIN`（L2719–2786） | 导航高光/tone 滚动脚本 |
| `<!-- R28-UI -->` 块 | `R28-UI:BEGIN`（L2787–2870） | 面板流体变换（FLIP+残影壳） |
| `<!-- R29-UI -->` 块 | `R29-UI:BEGIN`（L2871–2935） | 面板液态玻璃（按钮浅蓝 + 液态玻璃 + 上缘高光带） |
| `<!-- R31C-UI -->` 块 | `R31C-UI:BEGIN`（L2936–2964） | 门卡 `.r31-ring` 注入（`.gate-role` 伪元素被占用的替代路径） |
| `<!-- R31A-UI -->` 块 | `R31A-UI:BEGIN`（L2965–3078） | 卡片 3D 透视倾斜 + 弹簧阻尼回正（含指针离场归零） |
| `<!-- R31B-UI -->` 块 | `R31B-UI:BEGIN`（L3079–3185） | 关于板块 Fluid Morph（QQ 面板 + 微信弹窗） |
| `</body></html>` | L3515–3516 | 文件结尾（总 3516 行，R37 基线；R37 CSS 层 L1639–1723、`</style>` L1724、`<body>` L1726、R37-UI L3459–3514） |

> **R22-UI / R22 高级动效层 / R23 深化不在当前基线**：R22/R23 改动已退出（仅作历史记录，见下方「精修区域标识 · R22/R23」与 `r22`/`r23` 探针），故上表不含 R22-UI 块；R25–R31 为 CSS 增量层，定位见「CSS 样式分区」表的 `R25:BEGIN`–`R31:BEGIN` 锚点。

### CSS 样式分区（`<style>` 自 L19 起；`</style>` 行号见 R29 勘误）

> **锚点约定（20261004 起）**：当前基线各层定位一律以「行号 / 定位锚点」列的标记 grep 为准（如 `grep -n "R25:BEGIN"`，中文标记直接 grep 逐字文本）；尾段（R14 补充层起）各层随后续每轮增量整体漂移，活表**不再维护绝对行号**，绝对行号仅存于各轮勘误（时点快照）。口径说明：R25 勘误的「R25 层 L1393–1407」为含标记行口径（R25 时点），R26/R27 勘误的「R25 层 L1390–1402」为层内容口径；现行实测 `R25:BEGIN`=1389、`R25:END`=1403；R26 起各勘误层区间均为含标记行口径。

| 行号 / 定位锚点 | 注释标记 | 内容 |
|---------|---------|------|
| 19–357 | — | 基础样式：`:root` 令牌 / 布局 / 组件 / 顶栏 / 侧栏 / 封面网格 / 详情页 |
| 358–425 | `/* ═══ 二次精修层 ═══ */` | P1 令牌与排印 · P2 卡片微交互 · P3 液态玻璃 · P4 详情页阅读 |
| 426–481 | `/* ═══ 三次精修层 ═══ */` | P5 动效引擎 · P6 阅读进度条 · P7 液态玻璃 v2 · P8 骨架拟真 |
| 482–543 | `/* ═══ 四次精修层 ═══ */` | P9 排印留白 · P10 形状统一 · P11 液态玻璃 v2 · P12 微交互 |
| 544–732 | `/* ═══ 五次精修层 ═══ */` | R13 全设备响应式适配层（390/768/1440/1920/2560） |
| 733–820 | `/* ═══ 六次精修层 ═══ */` | P13 留白节奏 · P14 微交互精修 · P15 液态玻璃 v3 · P16 骨架与空态 v3 |
| 821–997 | `/* ═══ 七次精修层 ═══ */` | P17 深色主题（`html[data-theme="dark"]` 作用域）· P18 科技质感 · P19 技术债 |
| 998–1079 | `/* ═══ 八次精修层 ═══ */` | P21 令牌扩展 · P22 Toast · P23 漂浮几何视差 · P24 前轮遗留 |
| 锚点 grep `响应式补齐层` | `/* ═══ … ═══ */` 多行注释块（标题行「响应式补齐层 · R14（全设备适配核验补齐）· 2026-10-01」）+ `关于板块层` | R14 触控适配 + 关于板块 CSS（R19 起仅社交/微信，`.about-dd*` 已删） |
| 锚点 grep `UI 细节清零层`（起止两处） | 起＝多行注释块「UI 细节清零层 · R15 — 2026-10-01」，止＝单行 `/* ═══… UI 细节清零层 · R15:END ═══… */` | R15 UI 细节清零层（FAQ 间距 / 尾部边距 / 移动端层叠修复） |
| 锚点 `R18:BEGIN`…`R18:END` | `/* ═══ R18:BEGIN … R18:END ═══ */` | R18 一级首页层（`#lp-nav` 毛玻璃导航 / hero / `.lp-panels` 玻璃卡 / 滚动淡入 / 暗色与降级） |
| 锚点 `R19:BEGIN`…`R19:END` | `/* ═══ R19:BEGIN … R19:END ═══ */` | R19 一级首页聚焦层（`.lp-dl` 下载区块样式/`.lp-cap`/`.gate-back`/`.lp-tile` 图标贴片/`.lp-cta` 实心化；R21 起下载卡标记已从模板移除，此层样式保留供回滚） |
| 锚点 `R21:BEGIN`…`R21:END` | `/* ═══ R21:BEGIN … R21:END ═══ */` | R21 收纳与动效层（hero 弹性满屏/关于板块贴底/`.lp-dl-btn`+`.lp-dl-menu` 下拉面板/`.r21-*` 按压回弹与涟漪/矮视口压缩） |
| 1394–1423（历史） | `/* ═══ R22 高级动效层 ═══ */`（`/* R22:BEGIN … R22:END */`） | R22：`@property --r22-ang` + `.r22-on .lp-cta::before` conic 旋转描边 / `::after` 呼吸背光（暗色环配色覆盖）/ `.r22-on .lp-dl-menu.is-open{animation:none}` 屏蔽 lpMenuIn / `.r22-ghost` 残影壳（R23:A 追加 `will-change`，L1416-1417）/ reduced-motion 静止化（**历史行号，当前基线不含**） |
| 锚点 `R25:BEGIN`…`R25:END` | `/* ═══ R25:BEGIN … R25:END ═══ */` | R25 按钮规范对齐层（双按钮 `var(--r-md)`=16px 圆角矩形 / `.lp-cta` 线框化 inset 环 / 按钮内联图标尺寸） |
| 锚点 `R26:BEGIN`…`R26:END` | `/* ═══ R26:BEGIN … R26:END ═══ */` | R26 导航液态玻璃层（两栏 `::after` 边缘高光扫动带 `--lg-x` / `data-lg-tone` 文字令牌覆写 / `@supports` 门控的玻璃底色与 `url(#lg-refract)` 折射声明对） |
| 锚点 `R27:BEGIN`…`R27:END` | `/* ═══ R27:BEGIN … R27:END ═══ */` | R27 按钮动效扩面适配层（`.crumbs a.r21-b,.page-body a.r21-b{display:inline-block}`（inline 锚点承载缩放与涟漪裁剪）+ `.doc-toc-m summary.r21-b{list-style-position:inside}`（防涟漪宿主 overflow:hidden 裁掉折叠三角）） |
| 锚点 `R28:BEGIN`…`R28:END` | `/* ═══ R28:BEGIN … R28:END ═══ */` | R28 面板流体变换层（`.r28-on .lp-dl-menu.is-open{animation:none}` 屏蔽 lpMenuIn（FLIP 接管开启）/ `.r28-ghost` 残影壳（fixed、z-index:29 压按钮行 z31 之下、pointer-events:none、transform-origin 0 0、will-change）/ reduced-motion 壳 display:none 兜底） |
| 锚点 `R29:BEGIN`…`R29:END` | `/* ═══ R29:BEGIN … R29:END ═══ */` | R29 面板液态玻璃层（`.lp-dl-btn` 浅蓝 #8ecbff＋深藏青字 / `url(#lg-refract)` 声明对玻璃底 / `::after` 上缘高光带 / `data-lg-tone` 令牌覆写） |

### `<body>` 静态 HTML 骨架（L1515–L1539）

| 行号 | 元素 | 说明 |
|------|------|------|
| 1515 | `<body data-view="home">` | 静态初始值，JS 路由动态切换 `data-view`（首帧即被 `render()` 覆写） |
| 1516–1525 | `<nav id="lp-nav">` | 一级首页毛玻璃导航（`LP-NAV:BEGIN/END` 注释对）：品牌 + 进入(`#/identity`)/下载/关于 + 主题按钮挂点（R19 起不再有教程/开发者直链） |
| 1526–1535 | `<header id="topbar">` | 顶栏：汉堡菜单 `#burger` · Logo · 搜索框 `#searchwrap`（`.tut-only`）· 主题切换 `#themebtn`（JS 注入） |
| 1536 | `<div id="mask">` | 侧栏展开时的半透明遮罩 |
| 1537 | `<aside id="sidebar">` | 侧栏容器（内容由 JS `syncSidebar()` 动态填充） |
| 1538 | `<main id="app">` | 主内容区（初始为骨架屏，JS `render()` 填充实际视图） |

### 主脚本路由与视图渲染（L1479–L2060）

**路由入口**：`function render()`（L1826），监听 `hashchange`（~L1963），根据 `location.hash` 设置 `body[data-view]` 并渲染对应视图。未知 hash 一律回落 `landing`（一级首页）。

| 视图 | data-view | 路由 hash | 渲染函数 / 行号 | 说明 |
|------|-----------|----------|----------------|------|
| L1 一级首页 | `landing` | `#/`（默认/未知回落） | `lpView()`（L1782）+ `render()` 内 landing 分支（~L1869） | R21 收纳型 Landing：hero（「资源下载」实心按钮+下拉面板 与 单一 CTA 同行，CTA → `#/identity`）+ 关于板块（`__aboutMount` 挂入 `[data-about-slot]`，仅社交/微信）+ 页脚；hero 弹性占满首屏，关于板块贴底免滚动 |
| 身份选择门 | `identity` | `#/identity`（仅显式进入） | `render()` 内 ~L1840 | 用户/开发者选择门页 `.gate`（文档入口唯一收拢点）+ `.gate-back` 返回一级首页；不强制首访 |
| L2 教程首页 | `home` | `#/tutorial` | `render()` 内 ~L1861 | 英雄区 + 封面网格，数据来自 `#tut-data`（原 `#/` 已降级至此） |
| L3 连续阅读 | `all` | `#/all` | `render()` 内 | 全教程连续阅读模式 |
| L3 模块页 | `module` | `#/<模块id>` | `render()` 内 | 模块概览 + 页面列表 + 相关模块 |
| L4 详情页 | `page` | `#/<模块id>/<页面id>` | `render()` 内 | 面包屑 + 正文 + 上下翻页 |
| L2 开发者工作台 | `dev` | `#/dev` | `renderDev()` → `devHome()`（L1623） | 开发者专属工作区，数据来自 `#dev-data` |
| L3 开发者板块 | `dev` | `#/dev/<板块id>` | `devCat()` | 板块文档列表 + 过滤 |
| L3+ 开发者子分类 | `dev` | `#/dev/<板块>/<子分类>` | `devGroup()` | 子分类文档组 |
| L4 开发者文档详情 | `dev` | `#/dev/<板块>/<文档id>` | `devDocPage()` | 文档正文 + TOC |

**关键辅助函数**：

| 函数 | 行号 | 用途 |
|------|------|------|
| `low()` / `esc()` | ~L1477 | 小写缓存 / HTML 转义 |
| `wrapImgShells()` / `hydrateShells()` | ~L1480 | 图片壳包裹与 hydration |
| `buildHomeGrid()` | L1516 | 构建首页封面网格 |
| `getRole()` / `setRole()` / `pick()` | ~L1530 | 身份选择与记忆（`pick()` 选完跳 `#/dev` 或 `#/tutorial`） |
| `syncSidebar()` | ~L1589 | 侧栏内容生成（用户/开发者两套） |
| `crumbs()` | ~L1595 | 面包屑导航生成 |
| `renderDev()` | ~L1742 | 开发者视图路由分发 |
| `lpView()` / `lpEnhance()` | L1782 / L1810 | Landing 模板（R21：资源下载按钮+下拉面板 与 CTA 同行）/ 滚动淡入（IntersectionObserver，reduced-motion 降级） |
| lp 导航「关于」处理器 | ~L1968 | `#lp-about-link`→`.about-sec` 平滑滚动（不写 hash）；`#lp-dl-link` 改由 R21-UI 块接管（滚动到按钮行并展开面板） |
| `[data-role-pick]` 委托 | ~L1980 | 门页双卡点击 → `pick()` |
| R21-UI 面板/动效引擎 | 2512–2636 | 下拉面板状态机（外点/Escape/选项点击/重渲 六路关闭 + 视口钳制）+ `pointerdown` 委托涟漪与按压回弹（SEL=L2521 `button,.lp-cta,.alllink,.pager a,.lp-dl-item` + R27 扩面 19 组（侧栏/面包屑/列表卡/quick/封面卡/板块卡/step/相关 chips/TOC/正文行内链接/logo/搜索联想），reduced-motion 全停） |
| `R22-UI` 流体变换 / 滚动物理（**历史轮次，当前基线不含**） | — | R22/R23 高级动效（面板 FLIP + `.r22-ghost` 残影壳 + 全局滚动物理 + `__r22`/`__r23` 钩子）**不在当前基线**；仅作历史记录，回滚方式见文末「可回滚注释对标记汇总」与「精修区域标识 · R22/R23」 |

### 可回滚注释对标记汇总

> 「定位锚点」列为第 1 列注释对的 grep 定位标记（如 `grep -n "R25:BEGIN"`）；行号随后续轮次整体漂移，本表不维护现行绝对行号，历史绝对行号见各轮勘误（时点快照）。

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
| `/* R37:BEGIN */ … /* R37:END */`（CSS，L1639–1723） | `R37:BEGIN` | 删除之间内容（Bento Grid 层：`.wrap-home/.wrap-dev` 让位页面底、`.cover-grid/.mod-grid/.skel-grid/.quick-grid/.pagecards` gap 16px、`.sec-tip` 区块 24px、首卡跨 2×2 与 Hero 内部构图、`--r-bento` 消费点、去渐变描边与静置投影扁平化、`.dev-stats .stat b` 去渐变、暗色 `.ms-cover-ph`/`.stat`/`.skel-body` 配套、≥1440px 四列档、≤767px 解跨列）+ **另需还原两处就地令牌（本层唯一非纯追加项）**：L20 `--bg:#f4f6fa;` 与 L842 `--bg:#0f1420;--bd:#2a3244;--tx:#e8ecf4;--mut:#9aa6bd;--card:#161c2a;` |
| `<!-- R37-UI:BEGIN -->` … `<!-- R37-UI:END -->`（JS，L3459–3514） | `R37-UI:BEGIN` | 删除之间内容（逐卡短边比例圆角：单 `ResizeObserver` + `rAF` 批量写内联 `--r-bento`，`clamp(16px, 0.07×min(宽,高), 34px)`，`#app` `MutationObserver` 重挂 + `isConnected` 显式 `unobserve` 释放）。删除后 CSS 侧 `var(--r-bento, var(--r37-r))` 自动回落 26px，**不破版**，故可与 CSS 层独立回滚 |
| `/* R38:BEGIN */` … `/* R38:END */`（CSS，L1731–2027）+ `<!-- R38-UI:BEGIN -->` … `<!-- R38-UI:END -->`（JS，L3820–3973） | `R38:BEGIN` / `R38-UI:BEGIN` | 删除两个注释对之间内容；另还原两处非纯追加：`<html data-look="neutral">`（L2）与 head THEME 脚本的 `nikki_look` 读取；或整文件还原 `Meow Star Map 官网.backup-r38-20261027.html` |
| `/* R39:BEGIN … R39:END */`（CSS） | `R39:BEGIN` | 删除之间内容（苹果式排版阶梯层：`--type-*`/`--lh-*`/`--space-*`/`--measure-prose` 与 A–F 六组规则，纯 CSS 零 JS/DOM/文案）|
| `/* R40:BEGIN … R40:END */`（CSS）+ `/* R40-VIEW:BEGIN … R40-VIEW:END */`（模板）+ `<!-- R40-UI:BEGIN … R40-UI:END -->`（JS） | `R40:BEGIN` / `R40-VIEW:BEGIN` / `R40-UI:BEGIN` | 删除三处注释对之间内容（`.lpx-*`/`.pg-*` 小卡体系、`pgIcon`/`lpFooterView`/`pgShell` 与四个二级页模板、`syncNav` 高亮脚本）+ 还原 `render()` 的 landing 子页判定与 `lpTitles` 分发 + 还原 `#lp-nav` 的 `.lp-nav-link` 四项 |
| `/* R41:BEGIN … R41:END */`（CSS）+ `<!-- R41-UI:BEGIN … R41-UI:END -->`（JS） | `R41:BEGIN` / `R41-UI:BEGIN` | 删除两处注释对之间内容（卡片行尾整行详情面板：`.lpx-card-toggle`/`.lpx-detpanel`/`.lpx-det-*` 与惰性建面板脚本）|
| `/* R42:BEGIN … R42:END */`（CSS）+ `/* R42-VIEW:BEGIN … R42-VIEW:END */`（模板） | `R42:BEGIN` / `R42-VIEW:BEGIN` | 删除两处注释对之间内容 + 还原 `lpView()` 三卡、`pgShell()` 签名与四页调用、`pgFeaturesView`/`pgResonanceView`/`pgDownloadView` 文案、`render()` 三处、R40-UI `syncNav()`、`LP-NAV` 与 `#topbar` 两处 markup；或整文件还原 `Meow Star Map 官网.backup-r42-20261101.html` |
| `/* R43:BEGIN … R43:END */`（CSS）+ `<!-- R43-ICON:BEGIN … R43-ICON:END -->`（head link 对） | `R43:BEGIN` / `R43-ICON:BEGIN` | **非纯追加**：删除两处注释对之间内容 + **逐字还原六处 `📷` 图标字形**（`.lp-brand-mark`/`.lg-emoji`/`.sb-all`/`.q-emoji`/`.dev-actions .alllink`/`.gate-emoji`）+ 还原四探针的零外链口径（r37 S5/S5c、r38 S4、r39 S0、r42 A10a/A10a2）+ 还原 `tests/r37-baseline.json`（或直接从 `tests/r37-baseline.pre-r43.json` 取回） |
| **无注释对**（R44 为 `pgDownloadView()` 内单行就地替换 → 11 行） | grep `"<h3>资源下载</h3>"`（全文件恰 1 处，且在 `pgDownloadView` 的 `.pg-grid.two` 内） | **非纯追加、零 CSS、零 JS 块**：把该 `<article>` 的 11 行整段还原为原单行 `    +'<article class="pg-card"><span class="pg-ico">'+pgIcon('spark')+'</span><h3>系统要求</h3><p>Windows 10 (1803+) / Windows 11，x64 架构。</p></article>'`（总行数 4865 → 4855）。详见「R44 勘误（20261101）」 |
| `/* ═══ R45:BEGIN … R45:END ═══ */`（CSS，L2397–2499）+ `<!-- R45-UI:BEGIN … R45-UI:END -->`（JS，L4967–5024） | `R45:BEGIN` / `R45-UI:BEGIN` | **纯追加，两处注释对删尽即完全回滚，无任何不可追加项**：未动 `:root`/`.lp-root` 令牌定义、未动任何模板行与既有选择器、未新增 hex / 中文文案 / 动画、未重指派 `--lp-*-ink`/`--ac*`/`--bg`/`--card`（`--card`/`--bg` 仅在 `#lp-nav` 与 `#look-menu` 两个隔离作用域内新赋，不在 `.lp-root` 上）。R45-UI 对 R36-UI **只读不改**（复用其 `.lp-thdots` 产物，只加 `.is-open` 类、不搬迁不复制），故 R36 可独立回滚且 R45-UI 空转不破版。另删 `tests/r45_theme_scope_check.py`。详见「R45 勘误（20261101）」 |

---

## 关键开发约定

### 软件图标（R43 起）

站点的软件图标是**一张图、一处内联、六处消费**，不是 emoji 也不是外部文件：

- **母图**：`:root{--app-icon:url("data:image/webp;base64,…")}`（WebP 256×256，源图 1:1 方图，只缩放不裁剪）。全文件仅此一份。
- **消费**：`<span class="app-ic" aria-hidden="true"></span>`，`width/height:1em` ⇒ 自动等于所在槽位字号；`background-image` 长写 ⇒ 不覆盖瓦片的 `background` 简写底色。
- **换图**：重新生成三段 base64（favicon PNG 64²、apple-touch-icon PNG 180²、母图 WebP 256²），替换 `--app-icon` 与 head 两枚 `<link>` 的载荷即可，**六处标记无需再动**。
- **favicon**：`<head>` 内两枚 `data:` 内联 `<link>`（`rel="icon"` + `rel="apple-touch-icon"`）；这是全站仅有的 `<link>`，探针按「href 非 `data:` 者计 0」守零外链口径。
- **不要新增的**：`assets/` 真实图片文件（破单文件自包含契约）、`og:image`（data: 抓不到、外链 img 会破 A10a）、`.gr-emoji`/`.ms-emoji`/`pgIcon()`/`.lp-tile`/`.ab-ic-*` 等**非软件图标**图形。

### 主题切换机制

- **存储**：`localStorage.nikki_theme`，值为 `light` / `dark` / `auto`（默认 `auto`，由 JS 实时同步 `prefers-color-scheme`；**`light` 态有意不设 `data-theme` 属性**，仅 dark 态设 `html[data-theme="dark"]`）。
- **落点**：`html[data-theme]` 属性；深色样式仅通过 `html[data-theme="dark"]` 作用域定义。
- **防闪烁**：`<head>` 顶部内联 `<script>`（`THEME:BEGIN` / `THEME:END` 注释对之间），首帧前同步解析并设置属性。
- **回滚**：删除 `THEME:BEGIN`…`THEME:END` 注释对之间内容 + R7 深色样式分区 + THEME-UI 块。
- **外观偏好（R38）**：`localStorage.nikki_look` = `neutral`（默认）/`color`/`plain`，落点 `html[data-look]`；与 `nikki_theme`、`nikki_lp_theme` 独立；plain 压过 landing 主题并隐藏配色圆点。触发器为 topbar / lp-nav / identity 三处纯图标按钮 + 单一隐藏菜单；回滚见「R38 勘误」。
- **landing 色彩作用域铁律（R45 起，新增 landing 板块必读）**：`lp-theme-energy` / `lp-theme-deep` 会把 landing 底刷成**暗底**（`body::before` 是 `position:fixed` 的视口渐变，`#0B0C10→#181A22` / `#024F97→#1D6EB6`）。新板块若直接写 `--tx`/`--mut`/`--bd`/`--card`/`--ac`，在暗底上会掉到 **1.1–1.8:1**（R40–R44 首轮即此不可读）。正确姿势：文字与表面一律走 `.lp-root` 上已翻好的继承令牌（`color:var(--tx)` / `background:var(--card)`），或走 landing 墨口 `--lp-eyebrow-ink`/`--lp-sub-ink`/`--lp-foot-ink`/`--lp-ac-ink`（`--lp-ac-ink` 默认 `var(--ac)`，浅态零差异）。**卡片表面须与 `.about-sec` 同值**才能算「与原有板块统一」，可证形式见 r45 E3（六者 computed 全等）。两条硬约束：① **不要**在 `.lp-root` 上翻 `--card`/`--ac`/`--ac-soft`（`.lp-dl-btn` 的 `#8ecbff`/`#0b2e4f` 与 `.lp-cta{background:var(--ac)}` 被 r20/r25/r29 精确断言占用）；② `#lp-nav` 与 `#look-menu` **都在 `.lp-root` 之外**（分别是 body 直接子节点、body 挂载浮层），够不着祖先翻转，须各自单点覆写（N1/M1），且 `:has(.lp-root…)` 是关系选择器、不是祖先作用域。`plain` 态下 `.lp-theme-*` 类**仍在** `.lp-root` 上，任何暗底适配规则都必须带 `:not([data-look="plain"])` 才不推翻 R38 的 plain 组。

### 五级界面架构（R21 起收拢入口）

通过 `body[data-view]` 属性控制视图切换：

| 层级 | data-view 值 | 路由 | 说明 |
|------|-------------|------|------|
| L1 | `landing` | `#/` | 一级首页，**聚焦「关于 + 下载」**：hero（「资源下载」实心按钮 + 下拉面板（三网盘项）居 CTA 左侧，CTA → `#/identity`）+ 核心能力 stats + 主要功能 6 卡 + 产品优势 3 卡（R41 起支持点卡行尾展开详情）+ 关于板块（首屏底部免滚动）+ 页脚；隐藏顶栏/侧栏，显示 `#lp-nav`（功能/共鸣录/隐私/下载 四个二级页直链 + 进入/下载/关于 + **R42 新增 `.lp-gh` GitHub 圆钮**）；**不再有任何教程/开发者直链，无独立下载区块**；R42 起三张整宽大卡（产品介绍 / 共鸣录横幅 / 开始使用）已迁往二级页 |
| L2（营销） | `landing` | `#/features`、`#/resonance`、`#/privacy`、`#/download` | R40 建的四个产品介绍二级页，`view` 仍为 `landing`（共用 `#lp-nav` 与 `.pg` 的 92px 顶部留白），仅模板与 `document.title` 分流；统一走 `pgShell` + `.pg-grid > .pg-card` 小卡体系，**R42 起页内零大卡** |
| L3（营销） | `landing` | `#/download/start` | R42 建的三级页「开始使用」，承载版本 / 系统要求 / 三步 / FAQ；`pgShell` 可选尾参使返回链指向 `#/download` 而非首页 |
| 门页 | `identity` | `#/identity` | 身份选择门 = 文档入口唯一收拢点（用户/开发者双卡分流），隐藏顶栏与侧栏；仅显式进入，不强制首访；`.gate-back` 可返回 L1 |
| L2 | `home` / `dev` | `#/tutorial` / `#/dev` | 教程首页（隐藏侧栏）/ 开发者工作台 |
| L3 | （默认/模块/all） | `#/mX`、`#/all` | 模块页 / 连续阅读，显示侧栏导航 |
| L4 | （默认/详情） | `#/mX/mYpZ`、`#/dev/...` | 详情页，面包屑 + 上下翻页 |

开发者视图额外通过 `body[data-view="dev"]` 切换紫色令牌（`--dvc` 系列变量）。

### 响应式断点

| 断点 | 用途 |
|------|------|
| `≤ 1100px` | 开发者文档布局单列化，TOC 隐藏 |
| `≤ 900px` | R19 下载卡三列 → 单列（R21 起卡片已收拢为下拉面板，该规则仅剩回滚价值） |
| `≤ 960px` | 侧栏收起为汉堡菜单，封面网格 2 列 |
| `≤ 768px` | Landing hero 收紧（R18/R21） |
| `≤ 720px`（高度） | R21 矮视口首屏再压缩（hero/about/foot 留白收紧，保关于板块一屏可见） |
| `≤ 600px` | 封面网格单列 |
| `≤ 560px` | 顶栏紧凑模式，骨架屏单列，lp-nav 紧凑；R21 双按钮紧凑与关于板块压缩 |
| `prefers-reduced-motion` | 全局禁用动画（R21 涟漪/回弹、R22 FLIP/残影/滚动物理在 JS 层也直接跳过或整体停用） |

审计覆盖视口：390 / 768 / 1440 / 1920 / 2560 px。

## 精修区域标识

CSS 中以注释分隔符标记各精修层，格式为 `/* ═══ 第N次精修层（日期）：… ═══ */`：

- **P1**：令牌与排版（阴影/圆角/字体栈/数字等宽/细滚动条）
- **P2**：卡片微交互（emoji 瓦片/封面缓放/stagger 入场）
- **P3**：液态玻璃精修（边缘高光/液态渐变/焦点柔光圆）
- **P4**：详情页阅读精修（杂志式表格/截图柔影/引用圆角）
- **R7**：深色主题分区（`html[data-theme="dark"]` 作用域）
- **R8 / R14 / R15**：后续响应式与交互精修轮次
- **R18**：一级首页层（`R18:BEGIN/END` 注释对，`#/` Landing + `#lp-nav`；配套 `LP-NAV:BEGIN/END` HTML 块与 `render()` landing 分支）
- **R19**：一级首页聚焦层（`R19:BEGIN/END` 注释对；下载剥离为 `.lp-dl` 独立区块、文档入口收拢至 `#/identity` 门页、`.gate-back`；关于板块 `.about-dd*` 下载下拉已删）
- **R21**：一级首页收纳与全局按钮动效层（`R21:BEGIN/END` CSS + `R21-UI:BEGIN/END` JS 注释对；`.lp-dl` 三卡收拢为 hero 内「资源下载」实心按钮+下拉面板、hero 弹性满屏使关于板块首屏贴底、全局按钮按压回弹 `r21-press/r21-pop` 与坐标涟漪 `r21-rip`；注意 `.lp-cta-row` 需 `z-index:31` 压过 about 卡，否则 g-ok 填充动画的层叠上下文会盖住面板）
- **R22**（历史轮次，**当前基线不含**）：高级动效层（`R22:BEGIN/END` CSS（L1394-1423）+ `R22-UI:BEGIN/END` JS 注释对（L2625-2938）+ enhance() 内 R22 对（L2204-2210）；① 资源下载按钮→面板 GSAP FLIP 流体变换（开启 `power4.out` 0.55s，关闭 `.r22-ghost` 残影壳 0.32s 且**不延迟 `hidden` 翻转**，MutationObserver 零侵入监听 R21 状态机）② `.lp-cta` conic 旋转描边（`@property --r22-ang`，伪元素实现，**不动按钮本体**以保全 r20 精确色值断言）+ `::after` 呼吸背光 ③ 全局滚动物理：滚轮全程阻尼接管 + 顶/底橡皮筋（`#app` translateY）+ 速度吸附语义锚点，iOS/reduced-motion 整体停用，内层滚动容器与键盘/滚动条放行 ④ enhance() 弹簧级联 `elastic.out(1,0.72)`；调试钩子 `window.__r22`）
- **R23**（历史轮次，**当前基线不含**）：R22 深化轮（**无独立注释对**，全部改动位于 R22 块内部并带 `/* R23 */` 行级标记；R22 整体回滚会一并移除 R23，单独撤销=还原带标记行）：① 残影壳补间 transform 化（`playClose()` 几何定格 + `will-change`，消除逐帧 layout；圆角非均匀缩放轻微椭圆化为已知取舍）② lastRect 时效加固（`fonts.ready` + `#lp-dl-wrap` ResizeObserver → `scheduleRect()`，经 watchMenu 重挂链路复用）③ 底边橡皮筋 `.doc-toc` sticky 冻结（`tocFix()` 以父网格行顶为参照判定 sticky 生效中 → `setPull()` 写 `-appY` 反向位移，`clearOv()` 清理；**sticky 在 transform 祖先下仍生效但被画布带跑，非跳自然流位；sticky 元素自身 offsetTop 已含位移不可作参照**；toc 仅 ≥1366px 视口且仅开发文档详情页渲染）④ 手感参数收拢 `CFG={vThresh,projMs,sessMs,snapTolVh,noUndo,ovMax,rubWheel,rubTouch}`（默认=R22 现值，行为零变化）+ `window.__r23={ver:'r23.0',cfg,setCfg}`（`__r22` 契约不变，r22 探针零回归）⑤ iOS 轻吸附评估维持现状（scrollTo 会打断原生 momentum）；测试 `tests/r23_refine_check.py`（18 项，端口 8662；CLS 断言与 r22 同口径——教程详情页导航存在既有侧栏 CLS 位移，改前后逐位一致，与轮次无关）
- **R25**：一级首页按钮规范对齐层（`R25:BEGIN/END` CSS 注释对 + `lpView()` 两处按钮模板内联 SVG 图标；① `.lp-cta`/`.lp-dl-btn` 圆角 `var(--r-md)`=16px 圆角矩形 ② `.lp-cta` 线框化：透明底 + `inset 0 0 0 1.5px var(--ac)` 描边环（非文字 3:1 达标），文字亮色用 `--ac-deep`（对 `--bg` 5.3:1 ≥4.5）、暗色用 `--ac`（5.9:1），hover 填 `--ac-soft` ③ Feather v4.29.2（MIT）内联 SVG 图标：资源下载=download、选择身份进入=user，`aria-hidden`，20px（≤560px 18px）`flex-shrink:0`；r20_icons_cta_check.py 口径已同步（实心断言转移至 `.lp-dl-btn`，新增线框/圆角/图标/等高断言，截图目录 r25-20261003））
- **R26**：导航液态玻璃 + 按钮箭头清理 + 动效扩面层（`R26:BEGIN/END` CSS 注释对 + `R26-SVG:BEGIN/END`（`filter#lg-refract`＝feTurbulence+feDisplacementMap scale14）+ `R26-UI:BEGIN/END`（rAF 滚动脚本）；① 两按钮删除尾部箭头：`.lp-dl-chev`（▾）与 `.lp-go`（→）span 及其 CSS（R21 reduced-motion 清单同步去掉 `.lp-dl-chev`），左侧 download/user 功能图标保留，面板内 `.lp-dl-go` 保留 ② `#topbar`/`#lp-nav` `::after` 边缘高光扫动带（1.5px 渐变，`background-position-x:var(--lg-x)`＝8%+滚动进度×84%，暗色减淡）③ 轻微折射：`backdrop-filter:url(#lg-refract) blur() saturate()` 声明对（blur 在前 url 在后，不支持 url() 的引擎整条丢弃自动回退纯模糊；Chromium 系生效）④ `data-lg-tone` 亮度自适应：R26-UI 于导航下沿 5 点 `elementsFromPoint` 找首个不透明背景（渐变取首色标）→ 相对亮度均值 + 滞回 0.45/0.55 → 写 tone；CSS 经作用域令牌（`--tx/--mut/--bd`）+ 玻璃底色覆写适配子元素；`html[data-theme]`/`body[data-view]` MutationObserver 即时重算，门页清残留 tone ⑤ **能力判断豁免透明度偏好**：本机 `EnableTransparency=0` → `prefers-reduced-transparency` 恒激活，导航两栏改用 `@supports (backdrop-filter…)` 门控压过 P11 实底降级（仅两栏豁免，其余玻璃面维持 P11 行为）⑥ R21 SEL 补 `.lp-dl-item`（网盘下拉三项涟漪回弹）；测试 `tests/r26_nav_glass_check.py`（23 项，端口 8663），截图目录 r26-20261003）
- **R27**：三/四级页+正文链接按钮动效扩面层（`R27:BEGIN/END` CSS 注释对 + R21-UI `SEL` 扩面一行，**JS 逻辑零改动**；① `SEL` 追加 19 组选择器：侧栏五类 `.sb-home/.sb-all/.sb-modlink/.sb-grp/.sb-pages a`、面包屑 `.crumbs a`、列表卡 `.pagecard`、快捷入口 `.quick`、L2 顺带 `.ms-card/.mod-card/.step`、相关 chips `.rel a/.mod-rel a`、开发者 TOC `.doc-toc a/.doc-toc-m a/.doc-toc-m summary`、正文行内链接 `.page-body a`（含 `.d-anchor`）、顶栏 `#topbar .logo`、搜索联想 `#searchdrop .sr`（`<button>` 类历轮已全局生效，本轮补齐的是链接式控件）② CSS 仅两行：inline 锚点转 inline-block（`transform`/`overflow:hidden` 在 inline 上无效）+ summary `list-style-position:inside` 防 `overflow:hidden` 裁掉默认折叠三角 ③ 引擎三路挂载已覆盖动态内容：`scan()`（初始）/`#app` MutationObserver（重渲）/pointerdown 兜底（侧栏与搜索联想在 `#app` 外走兜底路径）④ 需求与 R21 引擎逐字吻合：press `scale(.95)` → pop 0.38s `cubic-bezier(.34,1.56,.64,1)` 先过冲 1.05 再回 1；涟漪 `clientX/Y−getBoundingClientRect()` 精确波心、键盘 Enter/Space 降级中心波 ⑤ 已核实 `#topbar` 为 flex（`.alllink`/`.logo` 是 flex item 已块化，无需适配）、正文容器 `.page-body` 四处（教程详情/连续阅读/模块概览/开发者文档）；测试 `tests/r27_buttons_check.py`（75 项，端口 8664），截图目录 r27-20261003）
- **R28**：面板流体变换层（`R28:BEGIN/END` CSS 注释对 + `R28-UI:BEGIN/END` JS 注释对，**R21 状态机零改动**，需求=Orange OS 7「从哪里来回哪里去」；① 开启=MutationObserver 监听 `#lp-dl-menu[hidden]` 翻转后真面板 FLIP：`transformOrigin:'0 0'` 手写反演（非钳制 `xPercent:-50`、clampMenu 钳制 `xPercent:0` 双分支），自按钮矩形+按钮圆角+opacity .55 补间至面板位，`power4.out` 0.55s，终态 clearProps 还原样式表基态；选项 `.lp-dl-item` y:10/opacity:0 级联 delay .08 stagger .05 ② 关闭=hidden 同步翻转零延迟（r19 探针口径不变）+ `.r28-ghost` 残影壳（面板 rect 几何定格+缓存背景/边框/圆角/阴影，rAF+scroll/resize 刷新 lastRect）`power3.in` 0.32s 缩回按钮位（圆角同步过渡）自删，z29 压在按钮行 z31 之下呈「吸收」感 ③ 打断：开启中途关闭/resize→`snapEnd()` 瞬收清内联残留（尊重 clampMenu `transform:none`，无壳——无连续几何起点）；路由重渲→`#app` childList observer `rebind()` 重抓重挂+清壳 ④ 降级：无 GSAP 不挂 `html.r28-on` 回退 lpMenuIn；reduced-motion JS 整体跳过+CSS 壳 display:none 兜底 ⑤ `window.__r28={ver:'r28.0',cfg:{durOpen,durClose,openOp,closeOp,itemY,itemSt},stats:{morphOpen,ghost}}` 钩子；已知取舍：残影壳非均匀缩放圆角轻微椭圆化（R23 同款）、壳不含文字、中段打断瞬收；测试 `tests/r28_panel_flip_check.py`（24 项，端口 8665），截图目录 r28-20261003；r26 探针按压取证段同步加 900ms 静置（FLIP 期面板非静止位））
- **R29**：面板液态玻璃层（`R29:BEGIN/END` CSS 注释对 + `R29-UI:BEGIN/END` JS 注释对 + lpView() 模板移动云盘 href 单行替换，**R21 状态机与 R28 FLIP 零改动**；① `.lp-dl-btn` 浅蓝化：`#8ecbff` 底 + `#0b2e4f` 深藏青字（线性化 WCAG ≈8:1），hover `#79bffb`，亮暗主题同色，几何/内联图标（stroke=currentColor 自动跟随）零改动 ② `.lp-dl-menu` 液态玻璃：复用 R26 设施——`@supports` 门控内半透明底（亮 `rgba(255,255,255,.55)`/暗 `rgba(22,28,42,.58)`）+ `backdrop-filter` 声明对（`blur(20px) saturate(170%)` 在前、`url(#lg-refract) blur(20px) saturate(170%)` 在后，不支持 url() 的引擎整条丢弃回退纯模糊；滤镜 `#lg-refract` 为 R26-SVG 既有，零新增 SVG）+ `::after` 上缘高光带（1.5px 渐变，`left/right:var(--r-lg)` 内缩避 22px 圆角外溢，`background-position-x:var(--lg-x,50%)`）+ `data-lg-tone` 令牌覆写（`--tx/--mut/--bd/--ac/--ac-soft`，亮暗 tone × 亮暗主题四组合镜像 R26 层令牌覆写段）③ R29-UI 克隆 R26-UI 机制换宿主 `#lp-dl-menu`：`bgLumAt`（elementsFromPoint 首个不透明背景，跳过菜单自身与 `.r28-ghost`；**亮度口径=通道加权均值/255 伽马空间非线性化 RL，#808080≈0.50 落滞回带**）底缘下 8px 五点采样、滞回 0.45/0.55 写 tone；`--lg-x = 8%+滚动进度×84%`；hidden 翻转 MO 触发——开启瞬间 R28 FLIP 中段几何非静止故**先只更新 lg-x，680ms 后补采静止位 tone**，scroll/resize/theme/view MO 常规触发；try/catch 静默降级 ④ reduced-motion：玻璃为静态 CSS 保留（R26 同口径），FLIP/lpMenuIn 既有跳过逻辑不动；`prefers-reduced-transparency` 沿用 R26 豁免口径（本机 EnableTransparency=0 恒激活）⑤ 已知取舍：R28 ghost 残影壳复制 computed 半透明底但无 backdrop-filter（残影阶段无折射，既有降级路径）；移动云盘 href 更换为 `https://yun.139.com/shareweb/#/w/i/2xTrLAojYVTme/*z9yB02Re7uUB:/`（与旧链同构格式，r15/r18/r19 的 `yun.139.com` 子串断言不受影响）；r20 探针两行色值断言同步（亮暗均 rgb(142,203,255)/rgb(11,46,79)）；测试 `tests/r29_panel_glass_check.py`（28 项，端口 8666），截图目录 r29-20261003；**HTML 注释禁 `--` 坑二次确认（R29-UI 注释写 lg-x 不写 --lg-x，w3c 探针归零）**）

- **R37**：Apple 风格 Bento Grid 便当布局层（`R37:BEGIN/END` CSS 注释对 + `R37-UI:BEGIN/END` JS 注释对；详见「R37 勘误（20261026）」全量口径。要点速览：① 全站底色令牌就地换为 浅 `#F5F5F7`/`#FFFFFF` · 深 `#1D1D1F`/`#000000`；② **`.wrap-home`/`.wrap-dev` 让位 `var(--bg)`**，否则 `--bg` 仅 L22 一处消费而被白面板盖死、深色下面板与卡片同为 `#000` 不可辨（两条并列规则的特异度分别对齐 L520 与 L957，源码顺序获胜、零 `important`）；③ `.cover-grid` 与 `.mod-grid` 首卡跨 2 列 × 2 行（全文件首批 `grid-column/grid-row`；`:first-child` 恰为权重最高的真实入口卡，零新类名、零模板改动，R21 `SEL`/R31A `TILT`/GSAP 串原样生效；`≤767px` 必须解跨列，否则 1 列网格内 `span 2` 撑出 `2px 1112px` 隐式轨道把卡片压成 2px 宽）；④ 新增 `≥1440px` 四列档，Hero 占墙比 66%→49%，9 卡恰铺 3 行零空洞；⑤ 逐卡比例圆角 `clamp(16px, 0.07×min(宽,高), 34px)`，由 R37-UI 单 `ResizeObserver` + `rAF` 写内联 `--r-bento`，CSS `var(--r-bento, var(--r37-r))` 兜底 26px；系数由规范字面 18% 工程修正为 7%（18% 在实测短边 213–748px 会给到 15–135px、Hero 近胶囊）；⑥ 间距收敛 16px（压掉 L693 的 28px 与 L708 的 32px）+ `.sec-tip` 区块 24px；⑦ 两网格卡去 L973–976 双层渐变描边与静置投影、仅留 1px `--bd` 发丝边，hover 层级反馈复用既有 `translateY` + 强调色边框 + R31 conic 环，**零新增动画**；⑧ `.dev-stats .stat b` 去渐变以守「每页至多一处渐变文字」（须同时清 `background-image`/`background-clip`/`-webkit-text-fill-color`，否则数字因 `color:transparent` 隐形）。**零新增依赖、零外链不变量保持、DOM 零新增可见文案（故不触发 R36 Noto 子集化）**；测试 `tests/r37_bento_check.py`（file:// 协议、无端口；33 项 = 31 PASS / 0 FAIL / 2 NOT-RUN）；已知限制：标准单段圆弧 ≠ 连续圆角、卡面↔页面底差仅 1.09:1（浅）/1.25:1（深）无法与单一描边同达 WCAG 1.4.11 3:1（改造前既有发丝边亦 1.13:1，不引入新失效）

每层可独立回滚：删除对应注释对之间的 CSS 块即可（**R37 例外**：除删两个注释对外，还须还原 L20 与 L842 的两处令牌原文，它是本表唯一非纯追加的轮次）。

## 备份文件命名语义

`backups/`（精修快照目录，本工作树未纳入，快照存于父仓库 / 外部）下文件命名格式：

```
Meow Star Map 官网.backup-<标记>-<日期>.html   ← R25 起新源文件名前缀
用户使用教程.backup-<标记>-<日期>.html          ← 旧源文件名（R24 及之前的历史快照）
用户使用教程.r6.20260930.html
```

| 组成部分 | 含义 |
|---------|------|
| `backup-` | 通用快照前缀 |
| `backup-<标记>-` | 精修轮次或功能标记（如 `p9`、`r8`、`r14`、`r15`、`r18`、`r19`、`r19icons`、`r21`、`r22`、`r23`、`r25`、`r26`、`r27`、`about`、`gui-audit`、`responsive`） |
| `r6.` | 修订版本号前缀（旧格式） |
| `YYYYMMDD` | 快照日期 |

> 注：以下轮次报告名仅作标记溯源参考，**本工作树未纳入任何轮次报告**；其中 R25–R29 精修报告已于 2026-10-06 清理删除，早期报告（`p9`/`r8`/`r14`/`r15`/`r18`/`r19`/`r21`）亦不在本工作树，快照与报告存于父仓库 / 外部。

标记与精修报告对应关系（历史溯源）：`p9` → P9精修报告、`r8` → R8精修报告、`r14` → R14全设备适配、`r15` → R15精修报告、`r18` → R18一级首页与路由重构报告、`r19` → R19一级首页聚焦重构报告、`r21` → R21一级首页收纳与全局动效报告、`r22` → R22高级动效与交互报告（历史）、`r23` → R23深化动效报告（历史）、`r25` → R25按钮规范对齐与工具链迁移报告（已清理删除）、`r26` → R26导航液态玻璃与按钮动效统一报告（已清理删除）、`r27` → R27三四级页按钮动效扩面报告（已清理删除）、`r28` → R28面板流体变换动效报告（已清理删除）、`r29` → R29面板液态玻璃与按钮浅蓝报告（已清理删除）。

## 路由速查（R21 起）

| Hash | 视图 | 说明 |
|------|------|------|
| `#/` | `landing` | 一级首页（关于+下载聚焦；唯一出口 = hero CTA / lp-nav「进入」→ `#/identity`；「资源下载」按钮展开三网盘下拉面板；未知 hash 也回落至此） |
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

30.9MB 教程数据块内 47 处 `#/mX` 内链与路由前缀解耦，改动路由时**严禁触碰数据行**（`smoke.mjs` 以 SHA 冻结）。
