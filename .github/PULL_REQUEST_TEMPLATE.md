## 改动说明

<!-- 本轮做了什么、为什么；轮次编号（沿用 RNN 递增习惯） -->

## 契约检查单

- [ ] 新改动按注释对（`RNN:BEGIN/END`）组织，可独立回滚；非纯追加项已在 AGENTS.md 登记逐字还原方法
- [ ] 两条巨型数据行（`#tut-data` / `#dev-data`）未触碰
- [ ] 零外链不变量保持（非 data: 的 link / script src / 外链 img / iframe / url(http) 恒 0；图标 link 恰 2、@font-face 恰 2）
- [ ] 跨轮次选择器串（R21 SEL / R31A TILT / GSAP 串）未改名；HTML 注释无连续双连字符
- [ ] 新增可见中文文案已核验 Noto 子集覆盖（或全部逐字取自站内既有句子）
- [ ] 相关常驻探针已跑并附结果（r37 / r38 / r39 / r41 / r42 / r43 / r45 中受影响者；NOT-RUN 项注明原因）
- [ ] 基线 JSON 如需推进：旧基线已留存为 `*.pre-rNN.json` 并附差异签认记录
- [ ] AGENTS.md 已追记本轮勘误（范围 / 验证 / 已知限制 / 回滚方式）

## 验证记录

<!-- 探针 PASS/FAIL/NOT-RUN 汇总、截图路径（tests/rNN-shots/） -->

## 已知限制与回滚方式

<!-- 照 AGENTS.md 既有格式填写 -->