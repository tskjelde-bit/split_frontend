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
