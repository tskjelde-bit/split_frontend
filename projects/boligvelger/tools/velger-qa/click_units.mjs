#!/usr/bin/env node
// Programmatically selects all 16 units and verifies the panel shows correct data.
import puppeteer from 'puppeteer-core';
import { readFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:4173';
const units = JSON.parse(readFileSync(new URL('../../app/public/data/dybwads-gate-8/units.json', import.meta.url)));

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
await page.goto(BASE, { waitUntil: 'networkidle0' });
await page.waitForFunction('window.__velger !== undefined');

let failures = 0;
for (const [id, u] of Object.entries(units)) {
  await page.evaluate(i => window.__velger.select(i), id);
  await page.waitForSelector('[data-testid="unit-panel"]');
  const shownId = await page.$eval('[data-testid="panel-id"]', el => el.textContent);
  const shownPris = await page.$eval('[data-testid="panel-pris"]', el => el.textContent);
  const expectedPris = u.pris.toLocaleString('nb-NO').replace(/[  ]/g, ' ') + ',—';
  const ok = shownId === id && shownPris === expectedPris;
  if (!ok) failures++;
  console.log(`${ok ? 'OK ' : 'FAIL'} ${id}: panel=${shownId} pris=${shownPris}`);
}
await browser.close();
if (failures) { console.error(`${failures} failures`); process.exit(1); }
console.log('All 16 units verified.');
