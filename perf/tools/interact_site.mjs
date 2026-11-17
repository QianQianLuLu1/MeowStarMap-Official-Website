#!/usr/bin/env node
/** site/ 交互与移动端冒烟：真实点击 + 路由 + 弹层 + 溢出。 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/henji/AppData/Roaming/npm/node_modules/playwright');
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const HOST = 'http://127.0.0.1:8811';
const SITE = HOST + '/site/index.html';

const browser = await chromium.launch({ executablePath: chromium.executablePath(), headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

const step = async (name, fn) => {
  try {
    await fn();
    console.log('ok  ', name);
  } catch (e) {
    console.log('FAIL', name, e.message.split('\n')[0]);
    errors.push(name + ': ' + e.message);
  }
};

await page.goto(SITE + '#/', { waitUntil: 'load' });
await page.waitForTimeout(600);

await step('落地页 hero CTA 进入身份门', async () => {
  await page.getByRole('link', { name: /选择身份进入|进入/ }).first().click();
  await page.waitForTimeout(500);
  const v = await page.evaluate(() => document.body.dataset.view);
  if (v !== 'identity') throw new Error('view=' + v);
});

await step('身份门点「我是用户」→ 教程首页（数据加载 + 封面）', async () => {
  await page.locator('.gate-role').first().click();
  await page.waitForTimeout(1200);
  const v = await page.evaluate(() => document.body.dataset.view);
  if (v !== 'home') throw new Error('view=' + v);
  const covers = await page.evaluate(() => Array.from(document.querySelectorAll('.ms-cover img')).filter((i) => i.naturalWidth > 0).length);
  if (covers < 6) throw new Error('covers=' + covers);
});

await step('点模块卡进入模块页', async () => {
  await page.locator('.ms-card').first().click();
  await page.waitForTimeout(700);
  const v = await page.evaluate(() => document.body.dataset.view);
  if (v !== 'module') throw new Error('view=' + v);
});

await step('点页面卡进入详情页（截图懒加载）', async () => {
  const target = page.locator('a.pagecard[href="#/m1/m1p2"], a.pagecard').nth(1);
  await target.click();
  await page.waitForTimeout(1500);
  const v = await page.evaluate(() => document.body.dataset.view);
  if (v !== 'page') throw new Error('view=' + v);
  const im = await page.evaluate(() => {
    const i = document.querySelector('.page-body img');
    return i ? { c: i.complete, nw: i.naturalWidth, src: i.getAttribute('src') } : null;
  });
  if (!im || !im.c || im.nw === 0) throw new Error(JSON.stringify(im));
});

await step('搜索「下载」触发数据与结果', async () => {
  await page.fill('#searchbox', '下载');
  await page.waitForTimeout(800);
  const n = await page.evaluate(() => document.querySelectorAll('#searchdrop a.sr').length);
  if (n < 1) throw new Error('results=' + n);
  await page.fill('#searchbox', '');
});

await step('返回落地页并打开资源下载面板', async () => {
  await page.goto(SITE + '#/', { waitUntil: 'load' });
  await page.waitForTimeout(700);
  const btn = page.locator('#lp-dl-btn');
  await btn.click();
  await page.waitForTimeout(500);
  const vis = await page.evaluate(() => {
    const m = document.getElementById('lp-dl-menu');
    return m && getComputedStyle(m).display !== 'none';
  });
  if (!vis) throw new Error('menu hidden');
  await page.keyboard.press('Escape');
});

await step('主题切换（明↔暗，刷新后持久化）', async () => {
  const btn = page.locator('#lp-nav .lp-themebtn');
  await btn.click(); // 跟随系统 -> 显式 light
  await page.waitForTimeout(500);
  const ls1 = await page.evaluate(() => localStorage.getItem('nikki_theme'));
  if (ls1 !== 'light') throw new Error('第一次点击 nikki_theme=' + ls1);
  await btn.click(); // light -> dark
  await page.waitForTimeout(600);
  const dark = await page.evaluate(() => ({
    theme: document.documentElement.getAttribute('data-theme'),
    bg: getComputedStyle(document.documentElement).backgroundColor,
  }));
  if (dark.theme !== 'dark') throw new Error('点击后 data-theme=' + dark.theme);
  if (dark.bg === 'rgb(245, 245, 247)') throw new Error('背景未变深');
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(700);
  const persisted = await page.evaluate(() => ({
    theme: document.documentElement.getAttribute('data-theme'),
    ls: localStorage.getItem('nikki_theme'),
  }));
  if (persisted.theme !== 'dark' || persisted.ls !== 'dark') throw new Error('刷新未持久化 ' + JSON.stringify(persisted));
});

await step('关于 · 微信弹层 → 二维码懒加载', async () => {
  await page.evaluate(() => { location.hash = '#/'; });
  await page.waitForTimeout(400);
  const btn = page.locator('.about-soc-btn').nth(1);
  await btn.click().catch(() => 0);
  await page.waitForTimeout(1200);
  const info = await page.evaluate(() => {
    const im = document.querySelector('.about-wx-img');
    if (!im) return null;
    return { nw: im.naturalWidth, c: im.complete, hidden: !!im.closest('[hidden]') };
  });
  if (!info || info.nw === 0) throw new Error(JSON.stringify(info));
});

// 移动端溢出：所有主要路由
const routes = ['#/', '#/identity', '#/tutorial', '#/m1', '#/m1/m1p2', '#/all', '#/dev'];
for (const r of routes) {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(SITE + r, { waitUntil: 'load' });
  await page.waitForTimeout(900);
  const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  console.log(`${over <= 1 ? 'ok  ' : 'FAIL'} 390 溢出 ${r}: ${over}px`);
  if (over > 1) errors.push('overflow ' + r + ' ' + over);
}

console.log('\nERRORS', errors.length ? errors : 'none');
await browser.close();
process.exit(errors.length ? 1 : 0);
