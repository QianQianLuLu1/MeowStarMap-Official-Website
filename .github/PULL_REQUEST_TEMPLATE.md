## 改动说明

<!-- 本轮做了什么、为什么；轮次编号（沿用 RNN 递增习惯，当前基线 R55） -->

## 契约检查单

- [ ] 新改动按注释对（`RNN:BEGIN/END`）组织，可独立回滚；非纯追加项已在 AGENTS.md 登记逐字还原方法
- [ ] 两条巨型数据行（`#tut-data` / `#dev-data`）未触碰
- [ ] 零外链不变量保持（非 data: 的 link / script src / 外链 img / iframe / url(http) 恒 0；图标 link 恰 2、@font-face{ 恰 2）
- [ ] 跨轮次选择器串（R21 SEL / R31A TILT / GSAP 串）未改名；HTML 注释无连续双连字符
- [ ] 新增可见中文文案已核验 Noto 子集覆盖（或全部逐字取自站内既有句子）；新增西文/西里尔/阿拉伯文已注明字体回落影响
- [ ] 若新增可见文案：`locales/` 相应译文已补齐（或已确认属 BI 前缀、只做中英）；`build_i18n.py --check` 通过
- [ ] 相关常驻探针已跑并附结果（r37 / r38 / r39 / r41 / r42 / r43 / r45 / r51 / r54 中受影响者；NOT-RUN 项注明原因）
- [ ] 基线 JSON 如需推进：旧基线已留存为 `*.pre-rNN.json` 并附差异签认记录
- [ ] AGENTS.md 已同步当前状态、变更摘要、验证结果、已知限制与回滚方式
- [ ] 若改动 `site/`：已重跑 `python perf/tools/build_site.py` 并同步 `site/README.md` 的体积数字

## 验证记录

<!-- 探针 PASS/FAIL/NOT-RUN 汇总、截图路径（tests/rNN-shots/） -->

## 已知限制与回滚方式

<!-- 按 AGENTS.md 当前回滚表填写 -->
