#!/usr/bin/env node
/**
 * 用 Playwright 实测多文件版 site/ 与原始单文件版（file:// & HTTP）。
 * 仅做冒烟：打开、路由、控制台、图片、报表。
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/henji/AppData/Roaming/npm/node_modules/playwright');

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, '../..');
const CHROME = chromium.executablePath();

const url = (rel) => 'file:///' + path.join(REPO, rel).replace(/\\/g, '/');
const targets = {
  original: url('Meow Star Map 官网.html'),
  site: url('site/index.html'),
};

const routes = ['#/', '#/features', '#/download', '#/identity', '#/tutorial', '#/m1', '#/m1/m1p2', '#/all', '#/dev', '#/dev/d-overview'];

async function probe(page, base, hash) {
  await page.goto(base + hash, { waitUntil: 'load', timeout: 120000 });
  await page.waitForTimeout(1200);
  const sig = await page.evaluate(() => {
    const q = (s) => Array.from(document.querySelectorAll(s));
    return {
      view: document.body.dataset.view,
      title: document.title,
      h1: q('h1').map((e) => e.textContent.trim()).slice(0, 4),
      h2: q('h2').map((e) => e.textContent.trim()).slice(0, 6),
      links: q('#app a[href]').length,
      imgs: q('#app img').length,
      brokenImgs: q('#app img').filter((i) => i.complete && i.naturalWidth === 0).length,
      textLen: (document.getElementById('app')?.innerText || '').length,
      sidebar: q('#sidebar a').length,
      errText: document.getElementById('app')?.innerText?.slice(0, 80) || '',
    };
  });
  return sig;
}

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
page.on('requestfailed', (r) => errors.push('requestfailed: ' + r.url() + ' ' + (r.failure()?.errorText || '')));

for (const [name, base] of Object.entries(targets)) {
  console.log('\n===== ' + name + ' =====');
  for (const r of routes) {
    try {
      const sig = await probe(page, base, r);
      console.log(r, JSON.stringify(sig));
    } catch (e) {
      console.log(r, 'ERROR', e.message.split('\n')[0]);
    }
  }
}
console.log('\nERRORS', errors.length ? errors : 'none');
await browser.close();
