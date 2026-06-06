#!/usr/bin/env node
// Fit-to-bounds QA: shoots LANDING / orbit / exploded at multiple viewports,
// measures the building's pixel bbox (non-cream pixels excluding the HUD text
// region) and reports margins vs the HUD safe areas. Puppeteer + SwiftShader
// (headless Chrome --screenshot can't render WebGL on this machine).
import puppeteer from 'puppeteer-core';
import { mkdirSync, writeFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:4173';
const OUT = process.argv[3] ?? '/tmp/velger-qa';
mkdirSync(OUT, { recursive: true });
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const VIEWPORTS = [
  { w: 2000, h: 1310 },
  { w: 1728, h: 1117 },
  { w: 1440, h: 900 },
  { w: 1280, h: 800 },
  { w: 390, h: 844 },
];

// Cream background is #FBFAF6 (251,250,246). Building gips/green/grey + contact
// shadow are all clearly off-cream. Treat a pixel as "building/shadow" if it
// differs from cream by more than a threshold. Contact shadow is faint grey; to
// avoid counting the wide soft shadow disc we use a firmer threshold and also
// ignore near-cream greys.
// Building bbox is measured IN-PAGE by drawing the WebGL canvas onto a 2D
// canvas and scanning getImageData for off-cream pixels. Cream bg = #FBFAF6.
// Threshold excludes the faint contact-shadow disc but catches building solids.
async function bbox(page) {
  return page.evaluate(() => {
    const gl = document.querySelector('canvas');
    const r = gl.getBoundingClientRect();
    const w = Math.round(r.width), h = Math.round(r.height);
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    ctx.drawImage(gl, 0, 0, w, h);
    const data = ctx.getImageData(0, 0, w, h).data;
    const CREAM = [251, 250, 246];
    let minX = w, minY = h, maxX = -1, maxY = -1;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        const d = Math.abs(data[i] - CREAM[0]) + Math.abs(data[i + 1] - CREAM[1]) + Math.abs(data[i + 2] - CREAM[2]);
        if (d <= 38) continue;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
    return { minX, minY, maxX, maxY, w, h };
  });
}

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--force-device-scale-factor=1'],
});

const SCENES = [
  { name: 'landing', url: `${BASE}/`, delays: [1500, 4500] },
  { name: 'orbit', url: `${BASE}/?qa=orbit`, delays: [1800] },
  { name: 'exploded', url: `${BASE}/?qa=exploded`, delays: [2500] },
];

// Safe-area fractions must match CameraRig PAD.
const PAD = { top: 0.22, bottom: 0.16, left: 0.06, right: 0.06 };
const results = [];

for (const { w, h } of VIEWPORTS) {
  for (const scene of SCENES) {
    let shotIdx = 0;
    for (const delay of scene.delays) {
      const page = await browser.newPage();
      await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
      await page.goto(scene.url, { waitUntil: 'networkidle0', timeout: 30000 });
      await new Promise((r) => setTimeout(r, delay));
      const tag = `${scene.name}${scene.delays.length > 1 ? `-${shotIdx}` : ''}_${w}x${h}`;
      const path = `${OUT}/${tag}.png`;
      const buf = await page.screenshot({ clip: { x: 0, y: 0, width: w, height: h } });
      writeFileSync(path, buf);
      // Measurement shot: hide the HUD so only the building/shadow is on the
      // cream background. Margins are then measured purely against the geometry.
      await page.addStyleTag({ content: '.hud{display:none!important}' });
      await new Promise((r) => setTimeout(r, 60));
      const measBuf = await page.screenshot({ clip: { x: 0, y: 0, width: w, height: h } });
      writeFileSync(`${OUT}/${tag}_nohud.png`, measBuf);
      const bb = await bbox(page);
      await page.close();
      const topSafe = h * PAD.top;
      const botSafe = h * (1 - PAD.bottom);
      const leftSafe = w * PAD.left;
      const rightSafe = w * (1 - PAD.right);
      const r = {
        tag,
        w, h,
        bbox: { minX: bb.minX, minY: bb.minY, maxX: bb.maxX, maxY: bb.maxY },
        // gap between building edge and the safe-area boundary (positive = clear)
        gapTop: Math.round(bb.minY - topSafe),
        gapBottom: Math.round(botSafe - bb.maxY),
        gapLeft: Math.round(bb.minX - leftSafe),
        gapRight: Math.round(rightSafe - bb.maxX),
        // raw margins to viewport edges
        marginLeft: bb.minX,
        marginRight: w - bb.maxX,
        centerSkew: Math.round((bb.minX - (w - bb.maxX))),
        widthPx: bb.maxX - bb.minX,
      };
      results.push(r);
      shotIdx++;
    }
  }
}

await browser.close();
console.log(JSON.stringify(results, null, 2));
writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 2));
