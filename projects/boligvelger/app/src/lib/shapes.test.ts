import { describe, it, expect } from 'vitest';
import { polyToShape, polyCentroid, insetPolygon, polyToRingShape } from './shapes';

const square: [number, number][] = [[0, 0], [100, 0], [100, 100], [0, 100]];

// the actual cleaned envelope (rect with NE notch)
const envelope: [number, number][] = [
  [748, 375], [1660, 375], [1660, 640], [2030, 640], [2030, 1700], [748, 1700],
];

function shoelaceArea(poly: [number, number][]): number {
  let a = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x1, y1] = poly[i];
    const [x2, y2] = poly[(i + 1) % poly.length];
    a += x1 * y2 - x2 * y1;
  }
  return Math.abs(a) / 2;
}

function perimeter(poly: [number, number][]): number {
  let p = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x1, y1] = poly[i];
    const [x2, y2] = poly[(i + 1) % poly.length];
    p += Math.hypot(x2 - x1, y2 - y1);
  }
  return p;
}

describe('polyToShape', () => {
  it('scales svg px to meters', () => {
    const shape = polyToShape(square, 0.01);
    const pts = shape.getPoints();
    expect(pts[0].x).toBe(0);
    expect(pts[1].x).toBeCloseTo(1);
    expect(pts[2].y).toBeCloseTo(1);
  });
});

describe('polyCentroid', () => {
  it('finds center of square', () => {
    expect(polyCentroid(square)).toEqual([50, 50]);
  });
});

describe('insetPolygon', () => {
  it('shrinks a 100x100 square by d=10 to an 80x80 square (area 6400)', () => {
    const inner = insetPolygon(square, 10);
    expect(shoelaceArea(inner)).toBeCloseTo(6400, 5);
    // corners at (10,10)..(90,90)
    const xs = inner.map(p => p[0]).sort((a, b) => a - b);
    const ys = inner.map(p => p[1]).sort((a, b) => a - b);
    expect(xs[0]).toBeCloseTo(10);
    expect(xs[3]).toBeCloseTo(90);
    expect(ys[0]).toBeCloseTo(10);
    expect(ys[3]).toBeCloseTo(90);
  });

  it('insets the rect-with-notch envelope by d=24 within ~3% of perimeter*d', () => {
    const d = 24;
    const inner = insetPolygon(envelope, d);
    const ringArea = shoelaceArea(envelope) - shoelaceArea(inner);
    const approx = perimeter(envelope) * d;
    expect(Math.abs(ringArea - approx) / approx).toBeLessThan(0.03);

    // all inset points strictly inside outer bbox
    const minX = Math.min(...envelope.map(p => p[0]));
    const maxX = Math.max(...envelope.map(p => p[0]));
    const minY = Math.min(...envelope.map(p => p[1]));
    const maxY = Math.max(...envelope.map(p => p[1]));
    for (const [x, y] of inner) {
      expect(x).toBeGreaterThan(minX);
      expect(x).toBeLessThan(maxX);
      expect(y).toBeGreaterThan(minY);
      expect(y).toBeLessThan(maxY);
    }
  });
});

describe('polyToRingShape', () => {
  it('produces a shape with one hole and matching point counts', () => {
    const inner = insetPolygon(square, 10);
    const shape = polyToRingShape(square, inner, 0.01);
    expect(shape.holes).toHaveLength(1);
    const ep = shape.extractPoints(1);
    expect(ep.shape.length).toBe(square.length + 1); // closePath adds a point
    expect(ep.holes).toHaveLength(1);
    expect(ep.holes[0].length).toBe(inner.length + 1);
  });
});
