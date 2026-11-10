# Meow Star Map 官网（MeowStarMap-official-website）

「喵星图（Meow Star Map）」的官方网站：产品介绍 + 全流程使用教程 + 开发者文档，三合一的**单文件静态站点**。喵星图是一款面向《无限暖暖》的桌面媒体管理工具，软件本体见 [QianQianLuLu1/MeowStarMap](https://github.com/QianQianLuLu1/MeowStarMap)。

- 本仓库：<https://github.com/QianQianLuLu1/MeowStarMap-Official-Website>（已创建，待推送本工作树）
- 线上地址：暂无公开线上地址；本地 HTML 文件即完整站点
- 软件仓库：<https://github.com/QianQianLuLu1/MeowStarMap>
- 软件下载：软件仓库 [Releases](https://github.com/QianQianLuLu1/MeowStarMap/releases)，或站内「资源下载」面板（迅雷 / 百度 / 移动云盘）

## 项目是什么

整个站点只有一个源文件 `Meow Star Map 官网.html`（约 34.9 MB），包含全部 HTML / CSS / JS，以及内联的教程与开发者文档数据、字体子集、图标与封面图。**无构建工具、无框架、零外部资源请求**——所有资源以 `data:` 内联，离线双击即可完整运行。

站点通过 hash 路由组织五级界面（详见 [AGENTS.md](AGENTS.md)「五级界面架构」与「路由速查」）：

| 入口 | 内容 |
|------|------|
| `#/` | 一级首页：产品介绍、资源下载、关于 |
| `#/features` / `#/resonance` / `#/privacy` / `#/download` / `#/download/start` | 产品介绍二级页与「开始使用」三级页 |
| `#/identity` | 身份选择门（用户 / 开发者分流） |
| `#/tutorial`、`#/mX`、`#/mX/mYpZ`、`#/all` | 用户教程：首页 / 模块 / 详情 / 连续阅读 |
| `#/dev`、`#/dev/...` | 开发者工作台与文档 |

当前基线为 R45（20261101）：明暗主题 × 三态外观（中性黑白 / 彩色氛围 / 极简全白）× landing 四套配色主题，Bento Grid 布局，全套动效支持 `prefers-reduced-motion` 降级，禁 JS 不破版。逐轮变更与验收记录见 [AGENTS.md](AGENTS.md)。

## 本地运行

无需安装任何依赖、无需构建：

1. 直接用浏览器打开 `Meow Star Map 官网.html` 即可（`file://` 协议完整可用，这是项目的验收契约之一）。
2. 如需 HTTP 方式访问，在本目录任选一种静态服务器即可，例如：

   ```bash
   python -m http.server 8080
   # 然后浏览器访问 http://localhost:8080/Meow%20Star%20Map%20官网.html
   ```

文件较大（约 34.9 MB），首次打开的解析耗时属正常现象。

## 测试（回归探针）

`tests/` 内是常驻回归探针，Python + Playwright 驱动，`file://` 直开、无端口自起。环境要求：Python ≥ 3.8、Node（探针内用 `node --check` 编译校验 JS 块）。装配：

```bash
pip install playwright html5lib
playwright install chromium
```

> 版本锁定口径：AGENTS.md 记载的 `requirements.txt`（playwright / html5lib 锁定版）位于父仓库工具链，本工作树未纳入；以上两个包即探针的全部第三方依赖。

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

各探针的完整用法与口径见脚本头部注释；未跑项显式记 NOT-RUN，不当作通过。`tests/r37-baseline.json`、`tests/r39-baseline.json` 等基线 JSON 与 `tests/*-shots/` 截图归档是有意纳入版本管理的验收证据，勿删。

> AGENTS.md 中描述的 `npm run setup/doctor/smoke/vreg`、Makefile 入口与 r14–r31 历史探针属于**父仓库工具链**，本工作树不存在这些文件，相应命令在此不可用。

## 技术要点与硬契约

改动本站前请先读 [AGENTS.md](AGENTS.md) 与 [CONTRIBUTING.md](CONTRIBUTING.md)。核心契约：

- **单文件自包含**：不新增外部资源文件与外链资源（`<link>`（非 `data:`）/ `<script src>` / 外链 img / `iframe` / `url(http)` 恒为 0，探针守护）。
- **零外链不变量**：同上；图标 link 恰 2 枚且均 `data:`，`@font-face` 恰 2 处且均 `data:`。
- **两条巨型数据行严禁触碰**：`#tut-data` / `#dev-data` 内嵌教程与开发者文档 JSON，路由内链与数据解耦。
- **注释对回滚机制**：各轮改动以 `RNN:BEGIN/END` 注释对组织，可独立回滚；定位一律用 grep 锚点，行号随轮次漂移。
- **中文字体子集**：内嵌 Noto Sans SC 按站点字符子集化，**新增可见中文文案须再子集化**（流程见 AGENTS.md「R36 勘误」）。
- 主题偏好存于浏览器 `localStorage`（`nikki_theme` / `nikki_look` / `nikki_lp_theme` / `nikki_role`），站点不收集、不上传任何用户数据。

## 目录结构

```
Meow Star Map 官网.html   唯一源文件（全部 HTML / CSS / JS / 数据 / 字体 / 图标）
AGENTS.md                 常驻开发者文档：章节索引、逐轮勘误、开发约定、回滚方式
README.md                 本文件
LICENSE                   授权（MIT）
CONTRIBUTING.md           贡献指引（提炼自 AGENTS.md 既有约定）
SECURITY.md               安全问题披露指引
CODE_OF_CONDUCT.md        行为准则
.github/                  Issue / PR 模板
tests/                    常驻回归探针（r37–r45）+ 基线 JSON + 截图归档 + 校验报告
```

## 第三方资产与授权

站点内嵌了以下第三方资产，**各自保留其原许可证**（依据源文件内注释）：

| 资产 | 来源 | 许可证 |
|------|------|--------|
| GSAP 3.13.0（核心 + ScrollTrigger） | GreenSock | [GreenSock Standard License](https://gsap.com/standard-license) |
| Inter v4.1 可变字体（base64 内嵌） | rsms/inter | SIL OFL 1.1 |
| Noto Sans SC 可变字体子集（base64 内嵌） | google/fonts（ofl/notosanssc） | SIL OFL 1.1 |
| Feather v4.29.2 图标（内联 SVG） | feathericons.com | MIT |
| 网盘图标图形 | [Arcticons](https://github.com/Donnnno/Arcticons) | CC BY-SA 4.0（本表即署名；图形副本以相同许可提供） |
| QQ / 微信 / 抖音图标字形 | [Simple Icons](https://github.com/simple-icons/simple-icons)（tencentqq / wechat / tiktok，路径经逐字比对核实） | CC0 1.0（图标公有领域；品牌商标归原权利方，使用时须尊重） |
| GitHub 图标 | [Octicons](https://github.com/primer/octicons) mark-github-16 | MIT |

本项目自身代码采用 [MIT](LICENSE) 许可证（版权行 QianQianLuLu1，经项目所有者确认）。第三方资产的许可证不受本项目 LICENSE 覆盖；再分发时请保留 Arcticons 图形的署名与 CC BY-SA 4.0 许可声明。

## 贡献与联系

- 改动前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；安全问题见 [SECURITY.md](SECURITY.md)；协作请遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
- 问题反馈：推送至 [本仓库](https://github.com/QianQianLuLu1/MeowStarMap-Official-Website) 后按 `.github/` 内 Issue 模板提交；也可经站内「关于」板块的社交入口（QQ 群 / 微信 / 抖音）联系。
- 维护者：[QianQianLuLu1](https://github.com/QianQianLuLu1)（GitHub 主页）；安全问题请走 [SECURITY.md](SECURITY.md) 的私下披露渠道。