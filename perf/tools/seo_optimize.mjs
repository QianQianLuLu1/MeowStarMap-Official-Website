#!/usr/bin/env node
/**
 * site/ 的 SEO 后处理：
 *   1. 无 JS 也能读到的落地页静态内容（Playwright 渲染 #app 后回填）；
 *   2. title / description / robots / canonical / Open Graph / Twitter / JSON-LD；
 *   3. robots.txt；配置了 SITE_ORIGIN 时再生成 sitemap.xml、绝对 canonical/OG URL。
 *
 * 用法：
 *   node perf/tools/seo_optimize.mjs
 *   SITE_ORIGIN=https://meow.example node perf/tools/seo_optimize.mjs
 *
 * 依赖：Node 18+、Playwright（与 tests 同一套；本机为全局安装）。
 */

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(ROOT, '../..');
const SITE = path.join(REPO, 'site');
const INDEX = path.join(SITE, 'index.html');

function loadPlaywright() {
  const candidates = [
    'playwright',
    path.join(process.env.APPDATA || '', 'npm', 'node_modules', 'playwright'),
    path.join(process.env.USERPROFILE || '', 'AppData', 'Roaming', 'npm', 'node_modules', 'playwright'),
  ];
  for (const c of candidates) {
    try { return require(c).chromium; } catch (e) { /* try next */ }
  }
  throw new Error('找不到 playwright：请先 npm i -g playwright && playwright install chromium');
}

const argv = process.argv.slice(2);
const originArg = argv.includes('--origin') ? argv[argv.indexOf('--origin') + 1] : '';
let origin = (originArg || process.env.SITE_ORIGIN || '').trim();
if (origin) {
  origin = origin.replace(/\/+$/, '');
  if (!/^https?:\/\//i.test(origin)) throw new Error('SITE_ORIGIN 必须是 http(s) 绝对地址');
}

const NEW_TITLE = '喵星图 Meow Star Map 官网｜无限暖暖桌面相册工具';
const DESC = '喵星图（Meow Star Map）是面向《无限暖暖》玩家的 Windows 桌面相册工具：自动扫描游戏截图与录屏，本地浏览、整理、编辑与分享，数据只保存在本机。';
const GITHUB = 'https://github.com/QianQianLuLu1/MeowStarMap';

const canonical = origin ? `${origin}/` : './';
const ogImage = origin ? `${origin}/assets/og-cover.jpg` : '';

function headBlock() {
  const og = [
    '<meta property="og:type" content="website">',
    '<meta property="og:site_name" content="喵星图 Meow Star Map">',
    `<meta property="og:title" content="${NEW_TITLE}">`,
    `<meta property="og:description" content="${DESC}">`,
    '<meta property="og:locale" content="zh_CN">',
  ];
  if (origin) {
    og.push(`<meta property="og:url" content="${canonical}">`);
    og.push(`<meta property="og:image" content="${ogImage}">`);
    og.push('<meta property="og:image:width" content="1200">');
    og.push('<meta property="og:image:height" content="630">');
    og.push('<meta property="og:image:alt" content="喵星图 Meow Star Map — 无限暖暖桌面相册工具">');
  }
  const tw = [
    `<meta name="twitter:card" content="${origin ? 'summary_large_image' : 'summary'}">`,
    `<meta name="twitter:title" content="${NEW_TITLE}">`,
    `<meta name="twitter:description" content="${DESC}">`,
  ];
  if (origin) tw.push(`<meta name="twitter:image" content="${ogImage}">`);

  const jsonld = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebSite',
        ...(origin ? { '@id': `${origin}/#website`, url: `${origin}/` } : {}),
        name: '喵星图 Meow Star Map',
        alternateName: 'Meow Star Map',
        inLanguage: 'zh-CN',
        description: DESC,
        publisher: { '@type': 'Organization', name: '喵星图 Meow Star Map' },
      },
      {
        '@type': 'SoftwareApplication',
        name: '喵星图',
        alternateName: 'Meow Star Map',
        applicationCategory: 'MultimediaApplication',
        operatingSystem: 'Windows 10, Windows 11',
        softwareVersion: '2.5.6-beta',
        inLanguage: 'zh-CN',
        description: DESC,
        sameAs: [GITHUB],
        downloadUrl: 'https://github.com/QianQianLuLu1/MeowStarMap/releases',
        publisher: { '@type': 'Organization', name: '喵星图 Meow Star Map' },
        ...(origin ? { url: `${origin}/` } : {}),
      },
    ],
  };

  return [
    '<!-- SEO:BEGIN（由 perf/tools/seo_optimize.mjs 生成；重跑会整块替换） -->',
    `<title>${NEW_TITLE}</title>`,
    `<meta name="description" content="${DESC}">`,
    '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">',
    `<link rel="canonical" href="${canonical}">`,
    '<meta name="theme-color" content="#F5F5F7" media="(prefers-color-scheme: light)">',
    '<meta name="theme-color" content="#1D1D1F" media="(prefers-color-scheme: dark)">',
    ...og,
    ...tw,
    `<script type="application/ld+json">${JSON.stringify(jsonld)}</script>`,
    '<!-- SEO:END -->',
  ].join('\n');
}

async function prerender() {
  const chromium = loadPlaywright();
  const browser = await chromium.launch({ executablePath: chromium.executablePath(), headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    reducedMotion: 'reduce',
  });
  const page = await ctx.newPage();
  const url = 'file:///' + INDEX.replace(/\\/g, '/') + '#/';
  await page.goto(url, { waitUntil: 'load', timeout: 120000 });
  await page.waitForSelector('#app .lp-root', { timeout: 20000 });
  await page.waitForTimeout(600);
  await page.evaluate(async () => {
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    const step = Math.round(window.innerHeight * 0.8);
    for (let y = 0; y < document.body.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 50));
    }
    window.scrollTo(0, 0);
    // 即使 reduced-motion 没生效，也把 .lp-fade 全部置为可见，保证无 JS 时内容可读
    document.querySelectorAll('#app .lp-fade').forEach((el) => el.classList.add('is-in'));
  });
  await page.waitForTimeout(400);
  const data = await page.evaluate(() => ({
    html: document.getElementById('app').innerHTML,
    view: document.body.dataset.view,
    title: document.title,
    notIn: document.querySelectorAll('#app .lp-fade:not(.is-in)').length,
    inlineStyles: document.querySelectorAll('#app [style]').length,
  }));
  await browser.close();
  return data;
}

const prerendered = await prerender();
if (prerendered.notIn) console.warn('WARN 仍有 .lp-fade 未 is-in:', prerendered.notIn);
if (prerendered.inlineStyles) console.warn('WARN #app 内联 style 数:', prerendered.inlineStyles);

let html = fs.readFileSync(INDEX, 'utf8');

// 先清掉上一次的 SEO 块、旧 title 与上一次的静态内容
html = html.replace(/<!-- SEO:BEGIN[\s\S]*?<!-- SEO:END -->\s*/g, '');
html = html.replace(/<title>[^<]*<\/title>\s*/g, '');
html = html.replace(/<!-- SEO-PRERENDER:BEGIN -->[\s\S]*?<!-- SEO-PRERENDER:END -->/g, '');
if (!html.includes('<!-- THEME:END -->')) throw new Error('找不到 THEME:END 锚点');
html = html.replace('<!-- THEME:END -->', '<!-- THEME:END -->\n' + headBlock());

// 静态内容：无 JS 时也能读到落地页
const appStart = html.indexOf('<main id="app">');
if (appStart < 0) throw new Error('找不到 <main id="app">');
const appEnd = html.indexOf('</main>', appStart);
if (appEnd < 0) throw new Error('找不到 </main>');
html = html.slice(0, appStart)
  + '<main id="app"><!-- SEO-PRERENDER:BEGIN -->' + prerendered.html + '<!-- SEO-PRERENDER:END --></main>'
  + html.slice(appEnd + '</main>'.length);

// 静态首屏是落地页（无 JS 时 data-view 决定主题/布局）
html = html.replace('<body data-view="home">', '<body data-view="landing">');

// 运行时 landing 标题与静态 title 对齐（重跑时已是新标题，需幂等）
const oldExpr = "document.title=landingPage?(lpTitles[landingPage]+' · 喵星图'):'Meow Star Map · 喵星图';";
const newExpr = "document.title=landingPage?(lpTitles[landingPage]+' · 喵星图'):'" + NEW_TITLE + "';";
if (html.includes(oldExpr)) html = html.replace(oldExpr, newExpr);
else if (!html.includes(newExpr)) throw new Error('找不到 landing title 赋值');

// noscript 文案：静态内容已可读
html = html.replace(
  '<noscript>此页面需要启用 JavaScript 才能显示三级导航与交互功能。</noscript>',
  '<noscript>静态内容可直接阅读；完整导航、搜索与交互功能需启用 JavaScript。</noscript>',
);

fs.writeFileSync(INDEX, html);
fs.writeFileSync(path.join(SITE, 'robots.txt'),
  'User-agent: *\nAllow: /\n\n'
  + '# Single-language site (zh-CN); no multilingual versions, so no hreflang / per-language sitemap.\n'
  + (origin ? `Sitemap: ${origin}/sitemap.xml\n` : ''));

const sitemap = path.join(SITE, 'sitemap.xml');
if (origin) {
  const today = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(sitemap,
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + `  <url><loc>${origin}/</loc><lastmod>${today}</lastmod><changefreq>monthly</changefreq><priority>1.0</priority></url>\n`
    + '</urlset>\n');
} else if (fs.existsSync(sitemap)) {
  fs.unlinkSync(sitemap);
}

const report = {
  generated_at: new Date().toISOString(),
  origin: origin || null,
  title: NEW_TITLE,
  title_len_chars: [...NEW_TITLE].length,
  description_len_chars: [...DESC].length,
  canonical,
  prerendered_chars: prerendered.html.length,
  prerendered_view: prerendered.view,
  prerender_inline_styles: prerendered.inlineStyles,
  og_image: ogImage || null,
  sitemap: origin ? 'sitemap.xml' : null,
  html_bytes: fs.statSync(INDEX).size,
};
fs.mkdirSync(path.join(REPO, 'perf', 'reports'), { recursive: true });
fs.writeFileSync(path.join(REPO, 'perf', 'reports', 'seo.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
