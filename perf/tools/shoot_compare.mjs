#!/usr/bin/env node
/**
 * 截图对照：原始单文件（PNG）/ 无损单文件 / 多文件 site/。
 * 统一 reducedMotion=reduce 消除动效抖动；需要图片的页面先滚到底再回顶，确保 lazy 图全部加载。
 *
 * 前置：python -m http.server 8811
 * 输出：perf/assets/shots-compare/<target>/<case>.png
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/henji/AppData/Roaming/npm/node_modules/playwright');

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const OUT = path.join(REPO, 'perf/assets/shots-compare');
const CHROME = chromium.executablePath();
const HOST = 'http://127.0.0.1:8811';
const targets = {
  orig: HOST + '/Meow%20Star%20Map%20%E5%AE%98%E7%BD%91.html',
  lossless: HOST + '/perf/dist/Meow%20Star%20Map%20%E5%AE%98%E7%BD%91.lossless.html',
  site: HOST + '/site/index.html',
};

const cases = [
  { name: 'landing-1440', hash: '#/', w: 1440, h: 900, full: true },
  { name: 'landing-390', hash: '#/', w: 390, h: 844, full: true },
  { name: 'landing-dark-1440', hash: '#/', w: 1440, h: 900, full: true, dark: true },
  { name: 'identity-1440', hash: '#/identity', w: 1440, h: 900 },
  { name: 'download-1440', hash: '#/download', w: 1440, h: 900, full: true },
  { name: 'tutorial-1440', hash: '#/tutorial', w: 1440, h: 900, full: true },
  { name: 'page-m1p2-1440', hash: '#/m1/m1p2', w: 1440, h: 900, full: true },
  { name: 'dev-1440', hash: '#/dev', w: 1440, h: 900, full: true },
].filter((c) => !process.env.CASES || process.env.CASES.split(',').includes(c.name));

fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const report = [];

for (const [tname, base] of Object.entries(targets)) {
  if (process.argv[2] && process.argv[2] !== tname) continue;
  fs.mkdirSync(path.join(OUT, tname), { recursive: true });
  for (const c of cases) {
    const ctx = await browser.newContext({
      viewport: { width: c.w, height: c.h },
      reducedMotion: 'reduce',
      deviceScaleFactor: 1,
    });
    if (c.dark) {
      await ctx.addInitScript(() => {
        try { localStorage.setItem('nikki_theme', 'dark'); } catch (e) {}
      });
    }
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', (e) => errs.push(e.message));
    await page.goto(base + c.hash, { waitUntil: 'load', timeout: 180000 });
    await page.waitForTimeout(900);
    await page.evaluate(() => document.fonts && document.fonts.ready);
    if (c.full) {
      // 滚一遍触发 lazy，再回顶
      await page.evaluate(async () => {
        const step = Math.round(window.innerHeight * 0.8);
        for (let y = 0; y < document.body.scrollHeight; y += step) {
          window.scrollTo(0, y);
          await new Promise((r) => setTimeout(r, 60));
        }
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(300);
      await page.waitForFunction(
        () => Array.from(document.images)
          .filter((im) => { const r = im.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
          .every((im) => im.complete && im.naturalWidth > 0),
        null,
        { timeout: 20000 },
      ).catch(() => 0);
      await page.evaluate(async () => {
        // 隐藏的 lazy 图永远不会 decode，必须用超时兜底，否则整页等待会卡死
        await Promise.all(Array.from(document.images).map((im) => Promise.race([
          im.decode ? im.decode().catch(() => 0) : Promise.resolve(0),
          new Promise((r) => setTimeout(r, 1200)),
        ])));
      });
      await page.waitForTimeout(400);
    }
    const file = path.join(OUT, tname, c.name + '.png');
    await page.screenshot({ path: file, fullPage: !!c.full });
    const dims = await page.evaluate(() => ({
      scrollHeight: document.body.scrollHeight,
      viewport: [window.innerWidth, window.innerHeight],
      dark: document.documentElement.getAttribute('data-theme'),
      imgs: document.querySelectorAll('#app img').length,
      broken: Array.from(document.querySelectorAll('#app img')).filter((i) => i.naturalWidth === 0).length,
    }));
    report.push({ target: tname, case: c.name, file: path.relative(REPO, file), ...dims, errors: errs });
    console.log(tname, c.name, dims.scrollHeight, dims.dark, 'broken', dims.broken, errs.length ? errs : '');
    await ctx.close();
  }
}

fs.writeFileSync(path.join(REPO, 'perf/reports/shots-compare.json'), JSON.stringify(report, null, 2));
await browser.close();
