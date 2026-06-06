import * as THREE from 'three';

export function polyToShape(poly: [number, number][], scale: number): THREE.Shape {
  const s = new THREE.Shape();
  poly.forEach(([x, y], i) => {
    if (i === 0) s.moveTo(x * scale, y * scale);
    else s.lineTo(x * scale, y * scale);
  });
  s.closePath();
  return s;
}

export function polyCentroid(poly: [number, number][]): [number, number] {
  const n = poly.length;
  const sx = poly.reduce((a, p) => a + p[0], 0);
  const sy = poly.reduce((a, p) => a + p[1], 0);
  return [sx / n, sy / n];
}

/** Signed shoelace area (positive = CCW in standard math orientation). */
function signedArea(poly: [number, number][]): number {
  let a = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x1, y1] = poly[i];
    const [x2, y2] = poly[(i + 1) % poly.length];
    a += x1 * y2 - x2 * y1;
  }
  return a / 2;
}

/** Intersection point of two infinite lines, each given by a point and a direction.
 *  Returns null when the directions are (near-)parallel. */
function lineIntersect(
  p1: [number, number], d1: [number, number],
  p2: [number, number], d2: [number, number],
): [number, number] | null {
  const denom = d1[0] * d2[1] - d1[1] * d2[0];
  if (Math.abs(denom) < 1e-9) return null;
  const t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / denom;
  return [p1[0] + t * d1[0], p1[1] + t * d1[1]];
}

/** Inset a simple rectilinear polygon inward by distance `d` (same units as poly).
 *  Each edge is offset along its inward normal; consecutive offset lines are
 *  intersected to produce the new vertices. Inward direction is derived from the
 *  winding (shoelace sign), so concave corners (the envelope notch) resolve
 *  correctly via the intersection. */
export function insetPolygon(poly: [number, number][], d: number): [number, number][] {
  const n = poly.length;
  // For CCW (positive area) the inward normal of edge dir (dx,dy) is (-dy,dx).
  // For CW (negative area) it is (dy,-dx). Normalize the sign so the offset
  // always moves toward the interior.
  const s = signedArea(poly) >= 0 ? 1 : -1;

  // Build an offset line (point + direction) for each edge.
  const lines: { p: [number, number]; dir: [number, number] }[] = [];
  for (let i = 0; i < n; i++) {
    const a = poly[i];
    const b = poly[(i + 1) % n];
    const ex = b[0] - a[0];
    const ey = b[1] - a[1];
    const len = Math.hypot(ex, ey) || 1;
    // inward normal
    const nx = (s === 1 ? -ey : ey) / len;
    const ny = (s === 1 ? ex : -ex) / len;
    lines.push({
      p: [a[0] + nx * d, a[1] + ny * d],
      dir: [ex, ey],
    });
  }

  const out: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const prev = lines[(i - 1 + n) % n];
    const cur = lines[i];
    const hit = lineIntersect(prev.p, prev.dir, cur.p, cur.dir);
    // Fallback for parallel/colinear edges: shift the original vertex inward.
    out.push(hit ?? cur.p);
  }
  return out;
}

/** Build a ring (outer contour with an inner hole) as a THREE.Shape.
 *  Outer follows polyToShape (CW in the z-flipped frame, as authored).
 *  Inner is pushed to shape.holes with REVERSED point order so the hole
 *  winding opposes the outer contour. */
export function polyToRingShape(
  outer: [number, number][],
  inner: [number, number][],
  scale: number,
): THREE.Shape {
  const shape = polyToShape(outer, scale);
  const hole = new THREE.Path();
  const rev = [...inner].reverse();
  rev.forEach(([x, y], i) => {
    if (i === 0) hole.moveTo(x * scale, y * scale);
    else hole.lineTo(x * scale, y * scale);
  });
  hole.closePath();
  shape.holes.push(hole);
  return shape;
}
