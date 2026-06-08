import { describe, it, expect } from 'vitest';
import {
  pxToWorld,
  slabFromQuad,
  prismFromTriangle,
  boxGeometry,
  gableProjection,
  skylightOnSlope,
  buildFrontispiece,
  type V3,
} from './roofGeometry';
import type { GableSpec } from './types';

const scale = 0.012696;

function bbox(g: { getAttribute: (n: string) => { count: number; getX: (i: number) => number; getY: (i: number) => number; getZ: (i: number) => number } }) {
  const p = g.getAttribute('position');
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  for (let i = 0; i < p.count; i++) {
    minX = Math.min(minX, p.getX(i)); maxX = Math.max(maxX, p.getX(i));
    minY = Math.min(minY, p.getY(i)); maxY = Math.max(maxY, p.getY(i));
    minZ = Math.min(minZ, p.getZ(i)); maxZ = Math.max(maxZ, p.getZ(i));
  }
  return { minX, minY, minZ, maxX, maxY, maxZ };
}

describe('pxToWorld', () => {
  it('maps px to world XZ with z flipped', () => {
    expect(pxToWorld(748, 375, scale)).toEqual([748 * scale, -(375 * scale)]);
  });
});

describe('slabFromQuad', () => {
  it('produces a closed solid with non-zero thickness', () => {
    const a: V3 = [0, 1, 0];
    const b: V3 = [0, 1, 2];
    const c: V3 = [2, 0, 2];
    const d: V3 = [2, 0, 0];
    const g = slabFromQuad(a, b, c, d, 0.2);
    const bb = bbox(g);
    // 12 triangles * 3 verts (top+bottom+4 sides)
    expect(g.getAttribute('position').count).toBe(36);
    expect(bb.maxY - bb.minY).toBeGreaterThan(0.9); // spans the slope height
    expect(g.getAttribute('normal')).toBeTruthy();
  });
});

describe('prismFromTriangle', () => {
  it('extrudes a triangle downward by t', () => {
    const g = prismFromTriangle([0, 2, 0], [2, 0, 0], [0, 0, 0], 0.1);
    const bb = bbox(g);
    expect(bb.minY).toBeCloseTo(-0.1);
    expect(bb.maxY).toBeCloseTo(2);
  });
});

describe('boxGeometry', () => {
  it('centres a box at the requested point', () => {
    const g = boxGeometry(5, 3, -2, 0.6, 1.2, 0.6);
    const bb = bbox(g);
    expect((bb.minX + bb.maxX) / 2).toBeCloseTo(5);
    expect((bb.minY + bb.maxY) / 2).toBeCloseTo(3);
    expect((bb.minZ + bb.maxZ) / 2).toBeCloseTo(-2);
    expect(bb.maxY - bb.minY).toBeCloseTo(1.2);
  });
});

describe('skylightOnSlope', () => {
  it('sits flush on the west slope between eave and ridge', () => {
    // west slope: eave x=748px y=0, ridge x=748+0.4*(1660-748) px y=rise
    const g = skylightOnSlope(
      { t: 0.28, up: 0.55, width: 0.9, height: 1.2 },
      [748, 1700], [748, 375], 748 * scale, (748 + 0.4 * 912) * scale, 5.0, scale,
    );
    const bb = bbox(g);
    expect(bb.maxY).toBeGreaterThan(0.55 * 5.0 - 1.2); // liegt rundt up*rise
    expect(bb.maxY).toBeLessThan(5.0);                  // under mønet
    expect(bb.maxX - bb.minX).toBeLessThan(1.2);        // tiltet — x-utstrekning < height
  });
});

describe('gableProjection', () => {
  const spec: GableSpec = {
    edge: 5, t: 0.5, width: 3.2, projection: 0.8, rise: 1.4,
    window: { width: 1.1, sill: 0.4, height: 1.6 },
  };
  it('builds body, roof, gable face and a window box', () => {
    const r = gableProjection(spec, [748, 1700], [748, 375], scale, 1.0);
    expect(r.body.getAttribute('position').count).toBeGreaterThan(0);
    expect(r.roof.getAttribute('position').count).toBeGreaterThan(0);
    expect(r.gableFace.getAttribute('position').count).toBeGreaterThan(0);
    expect(r.window).not.toBeNull();
    // the projection peaks rise above its base
    const bb = bbox(r.roof);
    expect(bb.maxY).toBeGreaterThan(1.0 + spec.rise - 0.2);
  });
  it('omits the window when the spec has none', () => {
    const { window: _w, ...noWin } = spec;
    void _w;
    const r = gableProjection(noWin as GableSpec, [748, 1700], [748, 375], scale, 1.0);
    expect(r.window).toBeNull();
  });
});

describe('buildFrontispiece', () => {
  const spec = {
    edge: 5, t: 0.5, width: 3.6, projection: 0.35, depth: 1.8,
    gableBase: 3.2, apex: 5.8, trim: 0.22,
    window: { width: 1.0, sill: 0.7, height: 2.2, peak: 0.5 },
  };
  it('peaks above the main ridge and stays centred on the street edge', () => {
    const r = buildFrontispiece(spec, [748, 1700], [748, 375], 0.012696);
    expect(bbox(r.body).maxY).toBeCloseTo(spec.gableBase, 1);
    expect(bbox(r.gable).maxY).toBeCloseTo(spec.apex, 1);
    expect(r.window).not.toBeNull();
    const wb = bbox(r.window!.glass);
    expect(wb.minY).toBeCloseTo(spec.window.sill, 1);
    // sentrert: midt på street-edge i z
    const mid = -((1700 + 375) / 2) * 0.012696;
    const gb = bbox(r.body);
    expect((gb.minZ + gb.maxZ) / 2).toBeCloseTo(mid, 1);
  });
  it('builds white trim and a black roof cap', () => {
    const r = buildFrontispiece(spec, [748, 1700], [748, 375], 0.012696);
    expect(r.trim.getAttribute('position').count).toBeGreaterThan(0);
    expect(bbox(r.roofCap).maxY).toBeGreaterThan(spec.apex - 0.1);
  });
});
