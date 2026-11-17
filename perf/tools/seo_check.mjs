#!/usr/bin/env node
/** site/ SEO 自检：静态可读内容、head 标签、结构化数据、robots/站点地图、单语口径。 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/henji/AppData/Roaming/npm/node_modules/playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const SITE = path.join(ROOT, 'site');
const INDEX = path.join(SITE, 'index.html');
const URL = pathToFileURL(INDEX).href + '#/';

const checks = [];
const add = (name, ok, detail = '') => {
  checks.push({ name, ok: !!ok, detail: String(detail).slice(0, 200) });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
};

const browser = await chromium.launch({ executablePath: chromium.executablePath(), headless: true });

// ── 无 JS：静态内容必须可读 ──
{
  const ctx = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'load' });
  const s = await page.evaluate(() => {
    const app = document.getElementById('app');
    const ids = [...document.querySelectorAll('[id]')].map((e) => e.id);
    const dup = ids.filter((id, i) => ids.indexOf(id) !== i);
    return {
      view: document.body.dataset.view,
      appTextLen: (app?.innerText || '').length,
      h1: [...document.querySelectorAll('h1')].map((e) => e.textContent.trim()),
      hasGame: (app?.innerText || '').includes('无限暖暖'),
      hasDownload: (app?.innerText || '').includes('资源下载') || (app?.innerText || '').includes('下载'),
      dups: [...new Set(dup)],
      title: document.title,
      lang: document.documentElement.lang,
    };
  });
  add('无 JS：落地页静态内容 > 500 字', s.appTextLen > 500, s.appTextLen);
  add('无 JS：有且仅有 1 个 h1', s.h1.length === 1, JSON.stringify(s.h1));
  add('无 JS：包含「无限暖暖」与下载入口', s.hasGame && s.hasDownload, `game=${s.hasGame} dl=${s.hasDownload}`);
  add('无 JS：body data-view = landing', s.view === 'landing', s.view);
  add('无 JS：无重复 id', s.dups.length === 0, s.dups.slice(0, 5).join(','));
  add('html lang = zh-CN', s.lang === 'zh-CN', s.lang);
  await ctx.close();
}

// ── 有 JS：运行时 title / meta / 结构化数据 / 控制台 ──
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForTimeout(900);
  const s = await page.evaluate(() => {
    const meta = (n) => document.querySelector(`meta[name="${n}"]`)?.content || '';
    const og = (p) => document.querySelector(`meta[property="${p}"]`)?.content || '';
    const ld = [...document.querySelectorAll('script[type="application/ld+json"]')].map((e) => {
      try { return JSON.parse(e.textContent); } catch (e) { return null; }
    });
    const canon = document.querySelector('link[rel="canonical"]');
    return {
      title: document.title,
      desc: meta('description'),
      robots: meta('robots'),
      ogTitle: og('og:title'),
      ogType: og('og:type'),
      ogLocale: og('og:locale'),
      canonical: canon ? canon.getAttribute('href') : null,
      ldTypes: ld.filter(Boolean).flatMap((x) => (x['@graph'] || [x]).map((n) => n['@type'])),
      h1: [...document.querySelectorAll('h1')].map((e) => e.textContent.trim()),
      hreflang: document.querySelectorAll('link[rel="alternate"][hreflang]').length,
      root: !!document.querySelector('#app .lp-root'),
      appTextLen: (document.getElementById('app')?.innerText || '').length,
    };
  });
  add('有 JS：landing 运行时标题 = SEO 标题', s.title.includes('无限暖暖桌面相册工具') && s.title.includes('喵星图'), s.title);
  add('有 JS：description 非空且含产品词', s.desc.includes('无限暖暖') && s.desc.length >= 50, `${s.desc.length} 字`);
  add('有 JS：robots 允许索引', s.robots.includes('index') && s.robots.includes('follow'), s.robots);
  add('有 JS：OG 基础标签齐全', !!s.ogTitle && s.ogType === 'website' && s.ogLocale === 'zh_CN', `${s.ogTitle} / ${s.ogLocale}`);
  add('有 JS：canonical 使用相对口径', s.canonical === './' || /^https?:/.test(s.canonical || ''), s.canonical);
  add('有 JS：JSON-LD 含 WebSite + SoftwareApplication', s.ldTypes.includes('WebSite') && s.ldTypes.includes('SoftwareApplication'), s.ldTypes.join(','));
  add('有 JS：单语站点，无 hreflang（预期 0）', s.hreflang === 0, s.hreflang);
  add('有 JS：landing 正常渲染', s.root && s.appTextLen > 500, `${s.appTextLen} 字`);
  add('有 JS：控制台零报错', errors.length === 0, errors.slice(0, 3).join(' | '));
  await ctx.close();
}

// ── 文件级 ──
{
  const robots = fs.readFileSync(path.join(SITE, 'robots.txt'), 'utf8');
  add('robots.txt：允许全站抓取', /User-agent:\s*\*\s*[\r\n]+Allow:\s*\//.test(robots), robots.split('\n')[0]);
  const origin = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'perf/reports/seo.json'), 'utf8')).origin; } catch { return null; } })();
  const sm = path.join(SITE, 'sitemap.xml');
  add('sitemap：仅配置 SITE_ORIGIN 时生成', origin ? fs.existsSync(sm) : !fs.existsSync(sm), origin ? 'exists' : 'not configured');
  add('OG 分享图存在（1200×630）', fs.existsSync(path.join(SITE, 'assets/og-cover.jpg')), fs.statSync(path.join(SITE, 'assets/og-cover.jpg')).size + ' B');
}

fs.mkdirSync(path.join(ROOT, 'perf/reports'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'perf/reports/seo-check.json'), JSON.stringify(checks, null, 2));
const failed = checks.filter((c) => !c.ok);
console.log(`\n${checks.length - failed.length}/${checks.length} PASS`);
await browser.close();
process.exit(failed.length ? 1 : 0);
