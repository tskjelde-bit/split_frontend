#!/usr/bin/env node
// Measures building pixel bbox in the saved QA PNGs and reports gaps vs the HUD
// safe areas. Run after fit-check.mjs has produced the screenshots.
import { readdirSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire('/Users/torbjorntest/projects/boligvelger/app/');
const { PNG } = require('pngjs');

const DIR = process.argv[2] ?? '/tmp/velger-qa';
const PAD = { top: 0.22, bottom: 0.16, left: 0.06, right: 0.06 };
const CREAM = [251, 250, 246];

function bbox(png) {
  const { width: w, height: h, data } = png;
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
  return { minX, minY, maxX, maxY };
}

const files = readdirSync(DIR).filter((f) => f.endsWith('_nohud.png')).sort();
const rows = [];
for (const f of files) {
  const png = PNG.sync.read(readFileSync(`${DIR}/${f}`));
  const w = png.width, h = png.height;
  const bb = bbox(png);
  if (bb.maxX < 0) { rows.push({ f, note: 'no content' }); continue; }
  const topSafe = h * PAD.top, botSafe = h * (1 - PAD.bottom);
  const leftSafe = w * PAD.left, rightSafe = w * (1 - PAD.right);
  rows.push({
    f,
    gapTop: Math.round(bb.minY - topSafe),
    gapBottom: Math.round(botSafe - bb.maxY),
    gapLeft: Math.round(bb.minX - leftSafe),
    gapRight: Math.round(rightSafe - bb.maxX),
    mL: bb.minX,
    mR: w - bb.maxX,
    skew: bb.minX - (w - bb.maxX),
    bw: bb.maxX - bb.minX,
  });
}

const pad = (s, n) => String(s).padStart(n);
console.log('file'.padEnd(26), 'gT', 'gB', 'gL', 'gR', '  mL', '  mR', 'skew', '  bw', ' PASS');
for (const r of rows) {
  if (r.note) { console.log(r.f.padEnd(26), r.note); continue; }
  const pass = r.gapTop >= 0 && r.gapBottom >= 0 && r.gapLeft >= 0 && r.gapRight >= 0
    && Math.abs(r.skew) <= 0.15 * (r.mL + r.mR + r.bw);
  console.log(
    r.f.padEnd(26),
    pad(r.gapTop, 4), pad(r.gapBottom, 4), pad(r.gapLeft, 4), pad(r.gapRight, 4),
    pad(r.mL, 5), pad(r.mR, 5), pad(r.skew, 5), pad(r.bw, 5), pass ? ' OK' : ' FAIL',
  );
}
