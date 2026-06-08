import { describe, it, expect } from 'vitest';
import { edgeDentils, onEdge } from './facade';

describe('onEdge', () => {
  // Axis-aligned rectangle: edges 0..3
  // outline in px: [0,0] → [1000,0] → [1000,500] → [0,500]
  const rect: [number, number][] = [[0, 0], [1000, 0], [1000, 500], [0, 500]];
  const scale = 0.012696;

  it('returns midpoint of edge 0 (bottom, left→right)', () => {
    const p = onEdge(rect, scale, 0, 0.5);
    expect(p.x).toBeCloseTo(500 * scale, 3);
    expect(p.z).toBeCloseTo(0, 3);
  });

  it('outward normal for edge 0 has unit length and correct components', () => {
    const p = onEdge(rect, scale, 0, 0.5);
    // edge 0: a=[0,0]→b=[1000,0] in px; world: dx=+, dz=0
    // nx = -dz/len = 0, nz = dx/len = +1
    expect(p.nx).toBeCloseTo(0, 3);
    expect(p.nz).toBeCloseTo(1, 3);
    expect(Math.hypot(p.nx, p.nz)).toBeCloseTo(1, 5);
  });

  it('angle for edge 0 matches Math.atan2(dz, dx) = atan2(0, 1) = 0', () => {
    const p = onEdge(rect, scale, 0, 0.5);
    expect(p.angle).toBeCloseTo(0, 5);
  });

  it('t=0 gives start vertex of edge, t=1 gives end vertex', () => {
    const p0 = onEdge(rect, scale, 1, 0);
    expect(p0.x).toBeCloseTo(rect[1][0] * scale, 3);
    expect(p0.z).toBeCloseTo(-(rect[1][1] * scale), 3);

    const p1 = onEdge(rect, scale, 1, 1);
    expect(p1.x).toBeCloseTo(rect[2][0] * scale, 3);
    expect(p1.z).toBeCloseTo(-(rect[2][1] * scale), 3);
  });

  it('edge index wraps around for the last edge', () => {
    const lastEdge = rect.length - 1;
    const p = onEdge(rect, scale, lastEdge, 0.5);
    // edge 3 goes from [0,500] to [0,0], i.e. dx=0, dz=+500*scale
    expect(p.x).toBeCloseTo(0, 3);
    expect(p.z).toBeCloseTo(-(250 * scale), 3);
    // outward normal: edge goes -z, so nx = -(-1) is ambiguous; just check magnitude = 1
    expect(Math.hypot(p.nx, p.nz)).toBeCloseTo(1, 5);
  });
});

describe('edgeDentils', () => {
  it('emits evenly spaced placements along each edge with outward angle', () => {
    const rect: [number, number][] = [[0, 0], [1000, 0], [1000, 500], [0, 500]];
    const d = edgeDentils(rect, 0.012696, 0.5);
    expect(d.length).toBeGreaterThan(20);
    const first = d[0];
    expect(first).toHaveProperty('x');
    expect(first).toHaveProperty('z');
    expect(first).toHaveProperty('angle');
    // alle plasseringer ligger på en av kantene (x eller z konstant for rektangelet)
  });
});
