#!/usr/bin/env node
/**
 * 实测：原始单文件 vs 多文件 site/ 的网络传输与关键渲染指标（HTTP 本地服务器）。
 * 运行前先起：python -m http.server 8811
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/henji/AppData/Roaming/npm/node_modules/playwright');

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const CHROME = chromium.executablePath();
const HOST = 'http://127.0.0.1:8811';
const ORIG = HOST + '/Meow%20Star%20Map%20%E5%AE%98%E7%BD%91.html';
const SITE = HOST + '/site/index.html';

const browser = await chromium.launch({ executablePath: CHROME, headless: true });

async function measure(url, label) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  const reqs = [];
  const seen = new Set();
  page.on('response', async (r) => {
    if (seen.has(r.url())) return;
    seen.add(r.url());
    const h = r.headers();
    reqs.push({ url: r.url(), status: r.status(), len: Number(h['content-length'] || 0) });
  });
  const t0 = Date.now();
  await page.goto(url, { waitUntil: 'load', timeout: 180000 });
  const loadMs = Date.now() - t0;
  await page.waitForTimeout(2000);
  const perf = await page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0] || {};
    const paint = {};
    for (const p of performance.getEntriesByType('paint')) paint[p.name] = Math.round(p.startTime);
    return {
      domContentLoaded: Math.round(nav.domContentLoadedEventEnd || 0),
      loadEvent: Math.round(nav.loadEventEnd || 0),
      fcp: paint['first-contentful-paint'] || null,
      transfer: performance.getEntriesByType('resource').reduce((a, e) => a + (e.transferSize || 0), 0),
      resources: performance.getEntriesByType('resource').length,
      imgs: document.querySelectorAll('#app img').length,
    };
  });
  const total = reqs.reduce((a, r) => a + r.len, 0);
  const shots = reqs.filter((r) => r.url.includes('/assets/shots/'));
  await ctx.close();
  return { label, loadMs, total, reqs, shots, perf };
}

const cases = [
  [ORIG + '#/', '原始单文件 · 落地页'],
  [SITE + '#/', '多文件版 · 落地页'],
  [ORIG + '#/m1/m1p2', '原始单文件 · 教程正文页'],
  [SITE + '#/m1/m1p2', '多文件版 · 教程正文页'],
  [SITE + '#/all', '多文件版 · 连续阅读 #/all'],
  [SITE + '#/dev', '多文件版 · 开发者工作台'],
];

const results = [];
for (const [url, label] of cases) {
  const r = await measure(url, label);
  results.push(r);
  const mb = (r.total / 1048576).toFixed(2);
  console.log(`\n${label}`);
  console.log(`  传输 ${r.total.toLocaleString()} B (${mb} MiB) · 请求 ${r.reqs.length} · 截图请求 ${r.shots.length}`);
  console.log(`  FCP ${r.perf.fcp} ms · DCL ${r.perf.domContentLoaded} ms · load ${r.perf.loadEvent} ms (goto ${r.loadMs} ms)`);
  const top = [...r.reqs].sort((a, b) => b.len - a.len).slice(0, 5);
  for (const t of top) console.log(`    ${(t.len / 1024).toFixed(0)} KB  ${t.url.replace(HOST, '')}`);
}

console.log('\nSUMMARY');
console.log(JSON.stringify(results.map((r) => ({
  label: r.label, total: r.total, requests: r.reqs.length, shotRequests: r.shots.length,
  fcp: r.perf.fcp, load: r.perf.loadEvent,
})), null, 2));

await browser.close();
