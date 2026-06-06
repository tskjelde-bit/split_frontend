#!/usr/bin/env node
/**
 * Facade comparison QA.
 *
 * Renders the 3D model from two orthogonal directions and rasterises the
 * reference facade PDFs alongside for a side-by-side review.
 *
 * Usage:
 *   node tools/velger-qa/facade.mjs [base-url] [out-dir]
 *
 * Requires:
 *   - puppeteer-core (already in velger-qa/node_modules)
 *   - pdftocairo (part of poppler-utils, brew install poppler)
 */
import puppeteer from 'puppeteer-core';
import { mkdirSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../..');

const BASE = process.argv[2] ?? 'http://localhost:4173';
const OUT  = process.argv[3] ?? '/tmp/velger-facade';
mkdirSync(OUT, { recursive: true });

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const FACADE_DIR = path.join(REPO_ROOT, 'eiendommer/dybwads gate 8/fasader');

// Two named views:
//   sorvest: straight onto the street facade (world -x face, slight elevation)
//   soroest: straight onto the SE gable end  (world -z face, slight elevation)
const VIEWS = [
  { name: 'sorvest', dir: [-1, 0.15, 0],  ref: 'Fasade Sørvest.pdf',  refPfx: 'ref-sorvest' },
  { name: 'soroest', dir: [0,  0.15, -1], ref: 'Fasade Sørøst.pdf',   refPfx: 'ref-soroest' },
];

// --- Rasterise reference PDFs -------------------------------------------
for (const v of VIEWS) {
  const pdf = path.join(FACADE_DIR, v.ref);
  if (!existsSync(pdf)) {
    console.warn(`WARN: reference PDF not found: ${pdf}`);
    continue;
  }
  const pfx = path.join(OUT, v.refPfx);
  const cmd = `pdftocairo -png -r 100 "${pdf}" "${pfx}"`;
  console.log(`Rasterising: ${cmd}`);
  try {
    execSync(cmd, { stdio: 'inherit' });
  } catch (e) {
    console.warn(`WARN: pdftocairo failed for ${v.ref} — is poppler installed? (brew install poppler)`);
  }
}

// --- Launch headless browser and capture 3D renders ----------------------
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--force-device-scale-factor=1'],
});

// Load the app once in orbit mode (UI frozen, no auto-rotate) and reuse the
// page for both shots so we pay the model-load cost only once.
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 });
await page.goto(`${BASE}/?qa=orbit`, { waitUntil: 'networkidle0', timeout: 30000 });
// Wait for Three.js to render at least one frame.
await new Promise((r) => setTimeout(r, 1500));

for (const v of VIEWS) {
  const [dx, dy, dz] = v.dir;

  // Drive the camera API exposed by CameraRig.
  await page.evaluate((dx, dy, dz) => {
    // eslint-disable-next-line no-undef
    const cam = window.__velgerCamera;
    if (!cam) throw new Error('__velgerCamera not available — is CameraRig mounted?');
    cam.setView(dx, dy, dz);
  }, dx, dy, dz);

  // Allow one render tick for the camera to settle (setView is immediate/no-tween).
  await new Promise((r) => setTimeout(r, 300));

  const outPath = path.join(OUT, `${v.name}.png`);
  await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width: 1600, height: 1000 } });
  console.log(`Saved: ${outPath}`);
}

await browser.close();
console.log('\nFacade renders saved to', OUT);
console.log('Reference rasters saved alongside (ref-sorvest-1.png / ref-soroest-1.png).');
console.log('\nReview checklist:');
console.log('  sorvest: 5 window axes per storey, sokkel windows small+high, ark centred');
console.log('           with window, 2 dormers flanking, chimneys at both ends,');
console.log('           steep slope toward street, straight walls, no floating niches.');
console.log('  soroest: gable triangle correct, lower NE wing step visible, asymmetric');
console.log('           ridge (short steep slope toward street side), catslide over wing,');
console.log('           window/door openings on gable per reference.');
