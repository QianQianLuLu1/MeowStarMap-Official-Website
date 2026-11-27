# site/ — Meow Star Map 多文件版站点

`perf/tools/build_site.py` 从根目录的 `Meow Star Map 官网.html`（无损 WebP + 六语词典版）生成。
用于**线上部署**：落地页只加载 `index.html`（522 KiB）+ `assets/site.css`（863 KiB）两件 shell 资源，
教程图片与开发者文档按需加载。

> 根目录的单文件版仍保留为「离线双击」交付形态；`site/` 是同一份站点的网络优化版。
>
> `build_site.py` 是约 400 行的**单文件转换脚本**，不是构建框架：没有打包器、插件、增量构建或监听热更新，
> 11 步里多数是对源文件做字符串锚点替换，源文件结构一变它就会报 `FAIL: xxx 未匹配`。
> 因此**不要手改本目录的产物**——改内容改源文件，改生成逻辑改脚本，然后重跑。

## 体积（20261126 实测）

| 文件 | 原始 | gzip -9 | brotli q11 | 加载时机 |
|---|---|---|---|---|
| `index.html` | 535,326 B（522.8 KiB） | 185,744 | 160,663 | 首屏阻塞 |
| `assets/site.css` | 884,392 B（863.7 KiB） | 563,141 | 539,499 | 首屏阻塞（与 index 并行，可独立缓存） |
| `data/tutorial.js` | 69,450 B | 17,069 | 14,434 | 教程路由（空闲/悬停时预取） |
| `data/dev-docs.js` | 2,088,814 B | 479,752 | 330,422 | 首次进入 `#/dev` |
| `assets/shots/*.webp`（48 张） | 15,991,294 B | — | — | 每页 1–3 张，`loading="lazy"` |
| `assets/about-wx.jpg` | 238,007 B | 199,337 | 194,831 | 打开「关于 → 微信」时懒加载 |

首屏传输（本地 HTTP、无压缩）：`index.html` + `site.css` + 空闲预取的 `tutorial.js` = **1,489,168 B（1.42 MiB）、3 个请求**；
原单文件版是 **25,213,498 B（24.04 MiB）**，相差约 **17×**。若只算首屏阻塞资源，则为 1,419,718 B（1.35 MiB）。
单文件版压缩后 gzip-9 为 17,619,708 B、brotli q11 为 17,176,886 B（base64 + WebP 熵高，收益有限）。

### 为什么把 CSS 拆出去（R56）

拆之前 `index.html` 是 1,418,846 B（1.35 MiB），其中内联 `<style>` 占 883,647 B（**62%**）。
拆成 `assets/site.css` 之后：

- HTML 从 1.35 MiB 降到 522 KiB，浏览器可以边下 HTML 边解析，首字节到 DOMContentLoaded 的窗口更短；
- 样式表成为独立可缓存资源（多处/多次访问只重新校验 HTML）；
- 字体（Inter 子集 + Noto Sans SC 子集）与图标仍以 `data:` 内联在 CSS 里，**部署依旧零外部域名依赖**，`file://` 双击照样可用；
- 代价是多 1 个阻塞请求（与 `index.html` 并行下载，HTTP/2 下基本可忽略）。

CSS 里的 `url(#lg-refract)` 是对当前文档的片段引用，迁入外部样式表后按规范仍解析到同一文档
（Chrome/Firefox 实测：改前/改后 3 条路由 × 8 个节点的计算样式与几何逐位一致）。

## 运行

HTTP（推荐，方便开压缩与缓存）：

```bash
cd site
python -m http.server 8080
# http://localhost:8080/
```

`file://` 也可直接双击 `index.html`：字体与图标内联在 CSS 中，`site.css` 走相对路径，
教程/开发者数据用 classic script 加载，不触发 CORS。

## 部署建议

- 开 gzip 或 brotli（`index.html`+`site.css` 1.35 MiB → 0.68–0.70 MiB；`dev-docs.js` 2.09 MB → 0.32–0.45 MB）。
- 缓存：`assets/*` 内容随图片更新才变，建议 `Cache-Control: public, max-age=604800`；
  `index.html`、`assets/site.css` 与 `data/*` 文件名**未带内容哈希**，建议短缓存或 `no-cache` 走校验。
  若想让 `site.css` 长缓存，需在构建时把内容哈希写进文件名（当前未做）。
- 服务器需要能返回 `.woff2`、`.webp` 的正确 MIME（`font/woff2`、`image/webp`）；
  字体与图标其实是内联的，正常静态服务器无需额外配置。
- `.nojekyll` 已放置：GitHub Pages 部署时不会走 Jekyll 处理。

## 结构

```
site/
  index.html           单页应用 shell（JS/六语词典内联；样式表外链）
  assets/site.css      全站样式（字体、图标仍以 data: 内联在此文件）
  data/tutorial.js     window.__TUT__ = {...}   教程数据（图片为相对路径）
  data/dev-docs.js     window.__DEV__  = {...}  开发者文档
  assets/shots/*.webp  48 张 1400×900 截图（无损 WebP，逐像素等同原 PNG）
  assets/about-wx.jpg  关于板块微信二维码
  .nojekyll
```

重新生成：`python perf/tools/build_site.py`（数据、图片、CSS、图标、词典均由单文件版重建）。
若改动了译文，**先**跑 `python perf/tools/build_i18n.py --write` 注入单文件，**再**跑本脚本，否则 `site/` 会缺词典。
