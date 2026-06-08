export interface DentilPlacement { x: number; z: number; angle: number; }

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
