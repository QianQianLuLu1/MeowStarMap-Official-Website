# site/ — Meow Star Map 多文件版站点

`perf/tools/build_site.py` 从根目录的 `Meow Star Map 官网.html`（无损 WebP 版）生成。
用于**线上部署**：落地页只加载 1.13 MiB 的 shell，教程图片与开发者文档按需加载。

> 根目录的单文件版仍保留为「离线双击」交付形态；`site/` 是同一份站点的网络优化版。

## 体积

| 文件 | 大小 | 加载时机 |
|---|---|---|
| `index.html` | 1,186,206 B（1.13 MiB） | 首屏，唯一阻塞资源 |
| `data/tutorial.js` | 69,450 B | 教程路由（空闲/悬停时预取） |
| `data/dev-docs.js` | 2,088,814 B | 首次进入 `#/dev` |
| `assets/shots/*.webp`（48 张） | 15,991,294 B | 每页 1–3 张，`loading="lazy"` |
| `assets/about-wx.jpg` | 238,007 B | 打开「关于 → 微信」时懒加载 |

首屏传输（本地 HTTP 实测）：`index.html` + 空闲预取的 `tutorial.js` = **1.20 MiB**；
原单文件版是 **32.95 MiB**（27.5×）。开启 gzip/brotli 后 `index.html` 约 **684 / 644 KB**。

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
  index.html            单页应用 shell（CSS/JS/字体/图标内联）
  data/tutorial.js      window.__TUT__ = {...}   教程数据（图片为相对路径）
  data/dev-docs.js      window.__DEV__  = {...}  开发者文档
  assets/shots/*.webp   48 张 1400×900 截图（无损 WebP，逐像素等同原 PNG）
  assets/about-wx.jpg   关于板块微信二维码
  .nojekyll
```

重新生成：`python perf/tools/build_site.py`（数据、图片、图标均由单文件版重建）。
