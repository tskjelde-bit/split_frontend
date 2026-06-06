import { describe, it, expect } from 'vitest';
import { polyToShape, polyCentroid } from './shapes';

const square: [number, number][] = [[0, 0], [100, 0], [100, 100], [0, 100]];

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
