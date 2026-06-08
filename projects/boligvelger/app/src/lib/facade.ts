export interface DentilPlacement { x: number; z: number; angle: number; }

export interface EdgePoint {
  x: number; z: number;
  /** outward-facing normal x-component */
  nx: number;
  /** outward-facing normal z-component */
  nz: number;
  /** edge direction angle for rotateY */
  angle: number;
}

/**
 * World-space position + outward normal at a parametric point on a polygon edge.
 * outline is in pixel coordinates; scale converts px → metres (world units).
 * t ∈ [0,1] along edge `edge`.
 */
export function onEdge(
  outline: [number, number][],
  scale: number,
  edge: number,
  t: number,
): EdgePoint {
  const a = outline[edge], b = outline[(edge + 1) % outline.length];
  const ax = a[0] * scale, az = -(a[1] * scale);
  const bx = b[0] * scale, bz = -(b[1] * scale);
  const dx = bx - ax, dz = bz - az;
  const len = Math.hypot(dx, dz) || 1;
  const nx = -dz / len;
  const nz = dx / len;
  return {
    x: ax + dx * t,
    z: az + dz * t,
    nx,
    nz,
    angle: Math.atan2(dz, dx),
  };
}

/** Jevnt fordelte plasseringer langs alle kanter av outline (px), i world-koord.
 *  spacing i meter. angle = kantens retning (for rotateY). */
export function edgeDentils(
  outline: [number, number][], scale: number, spacing: number,
): DentilPlacement[] {
  const out: DentilPlacement[] = [];
  const n = outline.length;
  for (let i = 0; i < n; i++) {
    const a = outline[i], b = outline[(i + 1) % n];
    const ax = a[0] * scale, az = -(a[1] * scale);
    const bx = b[0] * scale, bz = -(b[1] * scale);
    const len = Math.hypot(bx - ax, bz - az);
    const count = Math.floor(len / spacing);
    const angle = Math.atan2(bz - az, bx - ax);
    for (let k = 1; k < count; k++) {
      const t = k / count;
      out.push({ x: ax + (bx - ax) * t, z: az + (bz - az) * t, angle });
    }
  }
  return out;
}
