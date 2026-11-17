# site/ — Meow Star Map 多文件版站点

`perf/tools/build_site.py` 从根目录的 `Meow Star Map 官网.html`（无损 WebP 版）生成。
用于**线上部署**：落地页只加载 1.16 MiB 的 shell，教程图片与开发者文档按需加载。

> 根目录的单文件版仍保留为「离线双击」交付形态；`site/` 是同一份站点的网络优化版。

## 体积

| 文件 | 大小 | 加载时机 |
|---|---|---|
| `index.html` | 1,215,628 B（1.16 MiB） | 首屏，唯一阻塞资源 |
| `data/tutorial.js` | 69,450 B | 教程路由（空闲/悬停时预取） |
| `data/dev-docs.js` | 2,088,814 B | 首次进入 `#/dev` |
| `assets/shots/*.webp`（48 张） | 15,991,294 B | 每页 1–3 张，`loading="lazy"` |
| `assets/about-wx.jpg` | 238,007 B | 打开「关于 → 微信」时懒加载 |

首屏传输（本地 HTTP 实测）：`index.html` + 空闲预取的 `tutorial.js` = **1.23 MiB**；
`main` 原版单文件是 **32.95 MiB**（27.1×），本分支单文件版是 23.82 MiB（19.4×）。
开启 gzip/brotli 后 `index.html` 约 **694 / 647 KB**。

## SEO

- 落地页内容已**静态写入** `index.html`（构建时 Playwright 渲染一次），无 JS 也能读到 719 字正文；有 JS 时 SPA 接管，视觉逐像素不变。
- head 已含：`title`（31 字）、`description`（81 字）、`robots`、`canonical`、Open Graph、Twitter、JSON-LD（WebSite + SoftwareApplication）。
- `robots.txt` 允许全站抓取；`assets/og-cover.jpg` 是 1200×630 分享图。
- 配好正式域名后重建，会写绝对 canonical / `og:url` / `og:image` 并生成 `sitemap.xml`：
  `SITE_ORIGIN=https://your.domain python perf/tools/build_site.py`
  未配置时 canonical 用相对 `./`，不生成 sitemap / `og:url` / `og:image`（宁缺毋滥）。
- 自检：`node perf/tools/seo_check.mjs`（18 项）。

### 国际化（hreflang）判断

当前只有简体中文，`<html lang="zh-CN">`、`og:locale=zh_CN`，**不加 hreflang**——没有其他语言版本时加 hreflang 是空标注。
以后要做英文 / 繁体：每种语言用独立路径（如 `/en/`、`/zh-TW/`）、翻译后的 title/description，互相 `hreflang` + `x-default`，sitemap 分语言列出。hash 路由不适合承载多语言，需要静态页或服务端路由。

### SEO 的边界

已静态化的是 `#/` 落地页；`#/features`、`#/download` 等 hash 路由在搜索引擎眼里仍是同一个 URL，不会被分别索引。要覆盖这些页面，需要为它们生成独立静态页（未做）。

## 运行

HTTP（推荐，方便开压缩与缓存）：

```bash
cd site
python -m http.server 8080
# http://localhost:8080/
```

`file://` 也可直接双击 `index.html`：字体与图标内联，教程/开发者数据用 classic script
加载，不触发 CORS。

## 部署建议

- 开 gzip 或 brotli（`index.html` 1.19 MB → 0.64 MB；`dev-docs.js` 2.09 MB → 0.33 MB）。
- 缓存：`assets/*` 内容随图片更新才变，建议 `Cache-Control: public, max-age=604800`；
  `index.html` 与 `data/*` 建议较短缓存或 `no-cache`（文件名未带内容哈希）。
- 服务器需要能返回 `.woff2`、`.webp` 的正确 MIME（`font/woff2`、`image/webp`）；
  字体与图标其实是内联的，正常静态服务器无需额外配置。
- `.nojekyll` 已放置：GitHub Pages 部署时不会走 Jekyll 处理。

## 结构

```
site/
  index.html            单页应用 shell（CSS/JS/字体/图标内联；落地页静态内容 + SEO head）
  data/tutorial.js      window.__TUT__ = {...}   教程数据（图片为相对路径）
  data/dev-docs.js      window.__DEV__  = {...}  开发者文档
  assets/shots/*.webp   48 张 1400×900 截图（无损 WebP，逐像素等同原 PNG）
  assets/about-wx.jpg   关于板块微信二维码
  assets/og-cover.jpg   1200×630 Open Graph 分享图
  robots.txt            允许全站抓取（配置 SITE_ORIGIN 后附 Sitemap 行）
  sitemap.xml           仅配置 SITE_ORIGIN 时生成
  .nojekyll
```

重新生成：`python perf/tools/build_site.py`（数据、图片、图标、SEO 均由单文件版重建）。
有正式域名：`SITE_ORIGIN=https://your.domain python perf/tools/build_site.py`。
