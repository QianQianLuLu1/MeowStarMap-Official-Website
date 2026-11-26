# locales/ — 六语 i18n 译文

本目录是**译文的唯一编辑入口**。站点仍是单文件 `Meow Star Map 官网.html`，译文由
`perf/tools/build_i18n.py --write` 单向注入其中的 `#i18n-*` 数据块，注入是幂等且可校验的。

## 语种与范围（两条线，不是一刀切）

| 侧 | 覆盖 | 语种 | 文件 |
|---|---|---|---|
| 营销侧 | 落地页、5 个二级页、页脚、关于、`#lp-nav`、下载面板、配色/外观/主题、卡片详情 | zh en fr es ru ar | `ui.{en,fr,es,ru,ar}.json`（zh 是源码里的 inline default） |
| 工作区侧 | 身份门、教程族（首页/9 模块/36 页/侧栏/面包屑/翻页/搜索）、开发者工作台页框 | zh + en | 仅 `ui.en.json` |
| 开发者文档库正文 | 104 篇技术文档（12 个板块） | **永久不译** | — |

**开发者文档库永久只提供中文原文**，这是既定产品边界：它的读者是开发者，
总量 823,995 字（站点数据块自报统计）技术文档逐语维护的成本与失真风险都不可接受。
工作区侧在 fr/es/ru/ar 下经 `fallbackLng` 回落英文，并由 `ui.notice.bi` 那行英文通告说明这一点。

## 编辑流程（单向）

```bash
# 1) 改译文
vi locales/ui.fr.json
# 2) 校验：分层 parity / 空值 / 非法字符 / 教程占位 / 零外链 / build_site 锚点
python perf/tools/build_i18n.py --check
# 3) 注入单文件 HTML
python perf/tools/build_i18n.py --write
# 4) 再生多文件站点
python perf/tools/build_site.py
```

若改了源码里的 `T('key','中文默认值')`，先跑 `python perf/tools/build_i18n.py --extract`
刷新 `ui.zh.json`（它是**从源码抽出的键表快照**，勿手改），再按 `--check` 的缺口补译文。

## 键的两个归属（重要）

键表共 **359 键**，按前缀分两层：

| 层 | 前缀 | 键数 | 要求 |
|---|---|---|---|
| **MKT**（营销侧，6 语必填） | `about` `adv` `dl` `dt` `feat` `foot` `hero` `lang` `look` `nav` `palette` `pg` `stats` `theme` `title` `toast` | 272 | `ui.{en,fr,es,ru,ar}.json` 五个文件**键集合必须一致**；缺一即 `--check` 判 FAIL |
| **BI**（工作区侧，只做中英） | `dev` `doc` `gate` `notice` `search` `top` `tut` | 87 | 这 7 个前缀的键**不允许**出现在 `ui.{fr,es,ru,ar}.json`，出现即判 FAIL，避免出现「半译」状态 |

> 注：`cta.*` 不在当前键表中，相关文案归入 `pg.*` / `dt.*`；
> `title.*` 是 MKT 前缀，容易被误当成 BI，请勿混淆。

## 写法约定

- 插值统一 `{{name}}` / `{{n}}` / `{{m}}` / `{{v}}` / `{{at}}` / `{{cat}}` / `{{label}}` / `{{next}}`，
  由 i18next 的 `interpolation` 处理；`escapeValue:false`，译文按原样进 HTML（因此译文里可以带 `<li>` 等标签，
  但**不得**出现 `</script`、U+2028/2029、NUL）。
- 方向符号写进译文，不靠 CSS 翻转：阿拉伯语里「下一个」用 `←`、「返回」用 `→`。
- 品牌名：`喵星图` → `Meow Star Map`；`《无限暖暖》` → `Infinity Nikki`；作者名 `纤璐不会玩摄影` → `Xianlu`。
- 数字与单位：`{{n}} 页` 这类中文量词在英文写成 `{{n}} pages`；阿拉伯语统一用复数形式（已知近似）。

## 教程英文包（tutorial.en.json）

- 结构与 `#tut-data` **同构但键名不同**：译文包用 `home` + **`mods`** + `pages`；
  而单文件里的 `#tut-data` 用 `home` + **`modules`** + `pages`。
  `build_i18n.py` 负责这层映射（`base["modules"]` ↔ `tut["mods"]`），手改任一侧都会导致占位校验失败。
  规模：`mods` 9 条（dict）、`pages` 36 条。
- **图片一律写占位** `{{imgN}}…{{imgM}}`，运行时按 DOM 顺序把原 `<img>` 回填进去；
  绝不复制 48 张内联 WebP（会显著增加数据行并破坏当前长度断言）。
  占位数量必须与中文原文逐页相等，总数 = 48，`--check` 会校验。
- `home` 必须保留 9 张 `.mod-card` 且每张含 `.mc-emoji/.mc-name/.mc-desc/.mc-count`，
  否则 `buildHomeGrid()` 抛错并回退中文首页。
- `pages[].text` 是搜索语料（英文），非中英语种的搜索会同时匹配英文与中文语料。

## 已知限制（有意取舍）

1. 内联 Inter 子集只覆盖站内既有西文（当前 381 码位）。法语/西语的重音字符、俄文西里尔、阿拉伯文
   由系统字体按字形兜底（`html[data-lang]` 上配了分语种字体栈），字形与 Inter 可能有细微差异。
2. 阿拉伯语的数字量词统一取复数形式；不追求阿拉伯语六种数的语法完备。
3. 工作区侧的界面在 fr/es/ru/ar 下是英文（含教程正文），语言菜单仍展示 6 项。
4. 界面语言落点为 `html[lang]` / `html[data-lang]` / `html[dir="rtl"]`，偏好存 `localStorage.nikki_lang`；
   `?lang=` 查询参数优先级高于本地偏好，`__i18nPin` 仅供探针钉住语言，不面向用户。
