# 贡献指引

本站以单文件 HTML 为站点源，同时维护 `locales/`、`perf/`、`tests/` 和生成的多文件版 `site/`；改动可能涉及多个文件。本指引只汇总项目**已经形成的习惯**（权威出处是 [AGENTS.md](AGENTS.md)），不另立新规。

## 改动前必读

1. 通读 [AGENTS.md](AGENTS.md) 的「当前基线与仓库边界」「目录、工具链与探针」「源码导航与硬契约」「关键开发约定」「响应式断点」与「注释对与安全回滚」。
2. 定位编辑目标一律用 **grep 锚点**（如 `grep -n "R37:BEGIN"`），不要依赖绝对行号——行号随每轮增量漂移；grep 巨型数据行时务必截断输出（如 `cut -c`）。
3. 涉及 landing 新板块时，必读 AGENTS.md「landing 色彩作用域铁律（R45 起）」与「R53 landing 布局作用域」，否则暗底主题下文字会不可读、或首页新板块不受 R53 排版节奏约束。
4. 涉及常驻导航（`#lp-nav`）时，注意 R54/R55 的结构与间距约定：产品路由在 `.lp-routes`、三个主动作在 `.lp-actions`，三个主动作**不得**加 `.lp-nav-link` 类（会被 `syncNav()` 当作路由项）。

## 硬契约（探针守护，违反即回归失败）

- **零外链资源**：`<link>`（非 `data:`）/ `<script src>` / 外链 img / `iframe` / `url(http)` / `@import` 恒为 0；图标 link 恰 2 枚且均 `data:`，`@font-face{` 恰 2 处且均 `data:`。单文件源不新增外部资源；`site/assets/` 仅由 `build_site.py` 从内联源生成。
- **两条巨型数据行严禁触碰**：`#tut-data`（L2723，21,358,276 字符）/ `#dev-data`（L2724，1,545,974 字符）——教程与开发者文档 JSON。
- **六语词典块勿手改**：`#i18n-en/fr/es/ru/ar` 与 `#i18n-tut-en` 由 `python perf/tools/build_i18n.py --write` 生成；译文改 `locales/*.json`，走 [locales/README.md](locales/README.md) 的单向流程。
- **跨轮次选择器契约不改名**：R21 涟漪 `SEL`、R31A `TILT` 宿主串、GSAP 入场/clearProps 串等。
- **HTML 注释内禁止连续双连字符**（W3C 合规，项目历史上踩过两次）。
- **新增可见中文文案须再子集化 Noto Sans SC**（见 AGENTS.md「源码导航与硬契约」）；若新文案全部逐字取自站内既有句子则免重做，探针有对应断言。新增西文/西里尔/阿拉伯文超出 Inter 子集（381 码位）时按字形回落系统字体，无需重做子集，但需在变更摘要中写明。
- 软件图标是「一张图、一处内联、六处消费」，换图方式见 AGENTS.md「软件图标（R43 起）」。

## 改动的组织方式

- 新改动按**注释对**组织（CSS 用 `/* RNN:BEGIN … RNN:END */`，脚本块用 `<!-- RNN-UI:BEGIN … RNN-UI:END -->`），保证可独立回滚；轮次编号沿用既有递增习惯（当前基线 R55）。
- 尽量纯追加；确有就地改写（非纯追加项）时，必须在 AGENTS.md 当前回滚表中**逐字登记还原方法**（R37 两处令牌、R43 六处图标、R44 单行替换、R54 `LP-NAV` 两个包裹 `div`）。
- 改动完成后更新 AGENTS.md 的当前状态、变更摘要、验证结果、已知限制和回滚方式，不追加逐轮勘误。仅改载荷时同样更新当前状态。

## 验证闭环（先写用例并确认失败）

项目惯例是「先写可复现探针并确认失败 → 改动 → 逐项转绿 → 回归既有探针」：

1. 环境：Python 3.12 实测基线（`perf/` 语法要求 3.10+；r51 直跑需 3.13+，3.12 用 `Path.open(newline='')` 兼容包装）+ `pip install playwright html5lib` + `playwright install chromium`；Node 用于 `node --check`。探针一律 `python tests/<脚本>.py` 直跑，**不建 venv**。构建工具链另需 `pip install -r perf/requirements.txt`（Pillow）。
2. 新探针放 `tests/`，`file://` 直开、无端口自起，依赖未跑项显式记 NOT-RUN。不为探针新增 npm scripts / make targets（避免平行工具）。
3. 改动后回归 `tests/` 下 9 支常驻探针（r37 / r38 / r39 / r41 / r42 / r43 / r45 / r51 / r54），用法见各脚本头部与 [README](README.md)。
4. **基线推进须留痕**：若功能快照基线需要推进，旧基线留存为 `*.pre-rNN.json` 并附差异签认记录。
5. 截图证据归档 `tests/rNN-shots/`，随轮次入库。

## 报告问题与提交改动

- 托管仓库：<https://github.com/QianQianLuLu1/MeowStarMap-Official-Website>。已提交 HEAD 与 `origin/main` 同步；工作树可能有未提交文档改动，以 `git status` 为准。按 `.github/` 内 Issue / PR 模板提交；也可经软件仓库 [Issues](https://github.com/QianQianLuLu1/MeowStarMap/issues) 或站内「关于」板块社交入口反馈。
- 报告站点问题时请附：路由 hash、浏览器/引擎与版本、视口宽度、主题态（明暗 / neutral-color-plain / landing 配色）、**界面语言**（zh/en/fr/es/ru/ar）、控制台报错。
- 分支命名与提交信息格式：暂无固定约定（保持现状，不另立新规）。

## 需要先沟通的情形

- 触碰任何既有轮次注释对内部的代码（会破坏该轮独立回滚能力）；
- 改动数据块、路由前缀、localStorage 键名（含 `nikki_*` 五个偏好键）；
- 更换下载链接/提取码（注意 R44 起网盘行在两处重复，须同步改）；
- 增删 i18n 键（会同时影响 `locales/ui.*.json` 的分层 parity 与 `ui.zh.json` 键表快照）；
- 任何会改变探针冻结断言（精确色值、几何、计数）的视觉调整。
