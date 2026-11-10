# 贡献指引

本站是单文件静态站点，全部改动都落在 `Meow Star Map 官网.html` 一个文件里，历史上以「轮次（RNN）增量层」方式演进。本指引只汇总项目**已经形成的习惯**（权威出处是 [AGENTS.md](AGENTS.md)），不另立新规。

## 改动前必读

1. 通读 [AGENTS.md](AGENTS.md) 的「项目结构概述」「关键开发约定」与相关轮次勘误。
2. 定位编辑目标一律用 **grep 锚点**（如 `grep -n "R37:BEGIN"`），不要依赖绝对行号——行号随每轮增量漂移；grep 巨型数据行时务必截断输出（如 `cut -c`）。
3. 涉及 landing 新板块时，必读 AGENTS.md「landing 色彩作用域铁律（R45 起）」，否则暗底主题下文字会不可读。

## 硬契约（探针守护，违反即回归失败）

- **零外链资源**：`<link>`（非 `data:`）/ `<script src>` / 外链 img / `iframe` / `url(http)` / `@import` 恒为 0；图标 link 恰 2 枚且均 `data:`，`@font-face` 恰 2 处且均 `data:`。不新增 `assets/` 真实资源文件（破单文件自包含契约）。
- **两条巨型数据行严禁触碰**：`#tut-data` / `#dev-data`（教程与开发者文档 JSON）。
- **跨轮次选择器契约不改名**：R21 涟漪 `SEL`、R31A `TILT` 宿主串、GSAP 入场/clearProps 串等。
- **HTML 注释内禁止连续双连字符**（W3C 合规，项目历史上踩过两次）。
- **新增可见中文文案须再子集化 Noto Sans SC**（流程见 AGENTS.md「R36 勘误」）；若新文案全部逐字取自站内既有句子则免重做，探针有对应断言。
- 软件图标是「一张图、一处内联、六处消费」，换图方式见 AGENTS.md「软件图标（R43 起）」。

## 改动的组织方式

- 新改动按**注释对**组织（CSS 用 `/* RNN:BEGIN … RNN:END */`，脚本块用 `<!-- RNN-UI:BEGIN … RNN-UI:END -->`），保证可独立回滚；轮次编号沿用既有递增习惯。
- 尽量纯追加；确有就地改写（非纯追加项）时，必须在 AGENTS.md 对应轮次勘误中**逐字登记还原方法**（先例：R37 两处令牌、R43 六处图标、R44 单行替换）。
- 改动完成后在 AGENTS.md 追记本轮勘误：范围、契约影响、验证结果、已知限制、回滚方式——这是项目既有的变更记录方式。

## 验证闭环（先写用例并确认失败）

项目惯例是「先写可复现探针并确认失败 → 改动 → 逐项转绿 → 回归既有探针」（R37 起形成闭环）：

1. 环境：Python ≥ 3.8 + `pip install playwright html5lib` + `playwright install chromium`；Node 用于 JS 块编译校验。探针一律 `python tests/<脚本>.py` 直跑，**不建 venv**（AGENTS.md 明令）。
2. 新探针放 `tests/`，`file://` 直开、无端口自起，依赖未跑项显式记 NOT-RUN。不为探针新增 npm scripts / make targets（避免平行工具，父仓库口径）。
3. 改动后回归 `tests/` 现存常驻探针（r37 / r38 / r39 / r41 / r42 / r43 / r45），用法见各脚本头部与 [README](README.md)。
4. **基线推进须留痕**：若功能快照基线（如 `tests/r37-baseline.json`）需要推进，旧基线留存为 `*.pre-rNN.json` 并附差异签认记录（先例：`tests/r42-r37-f2-diff.txt`、`tests/r43-r37-f2-diff.txt`）。
5. 截图证据归档 `tests/rNN-shots/`，随轮次入库。

## 报告问题与提交改动

- 托管仓库已创建：<https://github.com/QianQianLuLu1/MeowStarMap-Official-Website>（当前为空仓库，待推送本工作树）；推送后按 `.github/` 内 Issue / PR 模板提交。在此之前，问题可经软件仓库 [Issues](https://github.com/QianQianLuLu1/MeowStarMap/issues) 或站内「关于」板块社交入口反馈。
- 报告站点问题时请附：路由 hash、浏览器/引擎与版本、视口宽度、主题态（明暗 / neutral-color-plain / landing 配色）、控制台报错。
- 分支命名与提交信息格式：暂无固定约定（保持现状，不另立新规）。

## 需要先沟通的情形

- 触碰任何既有轮次注释对内部的代码（会破坏该轮独立回滚能力）；
- 改动数据块、路由前缀、localStorage 键名；
- 更换下载链接/提取码（注意 R44 起网盘行在两处重复，须同步改）；
- 任何会改变探针冻结断言（精确色值、几何、计数）的视觉调整。