import { useMemo } from 'react';
import type { BuildingGeo, WindowGeo } from '../lib/types';
import { useVelger } from '../state/store';

const NICHE = '#cfcbbd';
// Reveal depth: the wall is now wallThickness (0.30) thick. Make the niche deep
// enough to read as a sunk opening, but keep its back face short of the inner
// wall plane (0.30) so it never z-fights the wall ring's interior face:
//   front face at INSET (0.05), back face at INSET+DEPTH (0.23) < 0.30.
const DEPTH = 0.18;
// Sit the niche front face INSET behind the outer wall plane so it reads as an
// inset opening from outside without z-fighting the facade. The box extends
// inward by DEPTH/2 from its center, so center it at (INSET + DEPTH/2).
const INSET = 0.05;

/** Window niches: thin boxes along outline edges, inset into the facade so
 *  they read as openings on the gips model. Hidden in exploded mode.
 *  Mounted INSIDE Building's centering group; world z = -(py*scale) to match
 *  the extruded geometry (which went through rotateX(-PI/2)). */
export function Windows({ geo }: { geo: BuildingGeo }) {
  const mode = useVelger((s) => s.mode);
  const boxes = useMemo(
    () =>
      geo.windows.map((w: WindowGeo) => {
        const floor = geo.floors.find((f) => f.id === w.floor)!;
        const o = floor.outline;
        const a = o[w.edge];
        const b = o[(w.edge + 1) % o.length];
        const ax = a[0] * geo.scale;
        const az = -(a[1] * geo.scale);
        const bx = b[0] * geo.scale;
        const bz = -(b[1] * geo.scale);
        const x = ax + (bx - ax) * w.t;
        const z = az + (bz - az) * w.t;
        const angle = Math.atan2(bz - az, bx - ax);
        // Outward facade normal (outline winds clockwise in this z-flipped
        // frame, so the outward normal is to the left of the edge direction).
        const dx = bx - ax;
        const dz = bz - az;
        const len = Math.hypot(dx, dz) || 1;
        const nx = -dz / len;
        const nz = dx / len;
        // Center the box so its outward face sits INSET behind the outer wall
        // plane; the box then reveals DEPTH into the thick wall.
        const offset = INSET + DEPTH / 2;
        return {
          x: x - nx * offset,
          z: z - nz * offset,
          angle,
          y: floor.elevation + w.sill + w.height / 2,
          w: w.width,
          h: w.height,
        };
      }),
    [geo],
  );
  if (mode === 'exploded') return null;
  return (
    <group>
      {boxes.map((b, i) => (
        <mesh key={i} position={[b.x, b.y, b.z]} rotation={[0, b.angle, 0]}>
          <boxGeometry args={[b.w, b.h, DEPTH]} />
          <meshStandardMaterial color={NICHE} roughness={1} />
        </mesh>
      ))}
    </group>
  );
}
