#!/usr/bin/env node
// Interaction smoke: (1) REAL mouse clicks — assembled shell must explode the
// building, exploded plates must hover/select units; (2) programmatically
// selects all 16 units and verifies the panel shows correct data.
// Real clicks matter: programmatic select() alone cannot catch raycast/handler
// regressions (the "clicking has no function" bug).
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

const velgerState = () => page.evaluate(() => {
  const s = window.__velger.state();
  return { mode: s.mode, selected: s.selected, hovered: s.hovered, focus: s.focus };
});

let failures = 0;

// --- Real-click smoke 1: assembled shell click must explode ---
await page.goto(BASE + '/?qa=orbit', { waitUntil: 'networkidle0' });
await page.waitForFunction('window.__velger !== undefined');
await new Promise(r => setTimeout(r, 2500)); // camera settle
await page.mouse.click(720, 500); // building center
await new Promise(r => setTimeout(r, 400));
const afterShellClick = await velgerState();
if (afterShellClick.mode !== 'exploded') {
  failures++;
  console.log(`FAIL shell click: expected exploded, got ${JSON.stringify(afterShellClick)}`);
} else {
  console.log(`OK  shell click explodes (focus=${afterShellClick.focus})`);
}

// --- Real-click smoke 2: a unit must be hover/selectable with the mouse ---
await new Promise(r => setTimeout(r, 2500)); // explode animation settle
let realUnitHit = null;
outer: for (let x = 560; x <= 900; x += 85) {
  for (let y = 280; y <= 700; y += 70) {
    await page.mouse.click(x, y);
    await new Promise(r => setTimeout(r, 150));
    const st = await velgerState();
    if (st.selected) { realUnitHit = st.selected; break outer; }
  }
}
if (!realUnitHit) {
  failures++;
  console.log('FAIL exploded real click: no grid point selected a unit');
} else {
  console.log(`OK  exploded real click selects (${realUnitHit})`);
  await page.evaluate(() => window.__velger.select(null));
}

// --- Programmatic panel verification for all 16 units ---
await page.goto(BASE, { waitUntil: 'networkidle0' });
await page.waitForFunction('window.__velger !== undefined');
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
