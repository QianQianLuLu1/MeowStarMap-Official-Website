# 安全政策

## 范围说明

- 本项目是**纯静态单文件站点**：无服务端、无接口、无鉴权、不收集或上传用户数据；浏览器 `localStorage` 仅保存主题/身份等本地偏好。站点本体的安全问题主要是 markup/脚本注入面与外链指向。
- **桌面软件 MeowStarMap 的安全问题不属于本仓库**，请报告至软件仓库：<https://github.com/QianQianLuLu1/MeowStarMap>（渠道见该仓库说明）。
- 站内第三方网盘下载链接指向外部服务，其安全性由对应服务方负责；发现链接指向异常请按下述渠道告知维护者。

## 报告渠道

发现本站安全问题（如注入、外链被篡改、内嵌资源异常）时，请**不要**在公开 Issue 中披露细节，优先使用 GitHub 私密漏洞报告：

- 入口：本仓库 Security 页的「Report a vulnerability」——<https://github.com/QianQianLuLu1/MeowStarMap-Official-Website/security/advisories/new>（需维护者在仓库 Settings → Code security and analysis 启用 Private vulnerability reporting；仓库推送并启用后方可用）。
- 启用前或入口不可用时，可经站内「关于」板块的社交入口（QQ 群 / 微信）先行联系维护者，勿公开细节。

报告时请附：复现步骤、受影响的路由 hash 与浏览器环境、影响评估。维护者收到后会进行审查与处置；本项目不承诺具体响应时限。