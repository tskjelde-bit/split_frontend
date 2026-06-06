#!/usr/bin/env node
// Headless screenshots of all key states via Puppeteer (supports WebGL via SwiftShader).
// Usage: node shots.mjs [base-url] [outdir]
import puppeteer from 'puppeteer-core';
import { mkdirSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:4173';
const OUT  = process.argv[3] ?? '/tmp/velger-qa';
mkdirSync(OUT, { recursive: true });

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const SHOTS = [
  { name: 'landing',     url: `${BASE}/`,                  w: 1440, h: 900 },
  { name: 'orbit',       url: `${BASE}/?qa=orbit`,         w: 1440, h: 900 },
  { name: 'exploded',    url: `${BASE}/?qa=exploded`,      w: 1440, h: 900 },
  { name: 'floor2',      url: `${BASE}/?qa=floor2`,        w: 1440, h: 900 },
  { name: 'panel',       url: `${BASE}/?qa=unit-H0204`,    w: 1440, h: 900 },
  { name: 'mobil',       url: `${BASE}/?qa=exploded`,      w: 390,  h: 844 },
  { name: 'mobil-panel', url: `${BASE}/?qa=unit-H0204`,    w: 390,  h: 844 },
];

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--force-device-scale-factor=1'],
});

for (const { name, url, w, h } of SHOTS) {
  const page = await browser.newPage();
  await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
  const path = `${OUT}/${name}.png`;
  await page.screenshot({ path, clip: { x: 0, y: 0, width: w, height: h } });
  await page.close();
  console.log(path);
}

await browser.close();
