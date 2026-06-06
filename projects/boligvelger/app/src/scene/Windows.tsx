import { useMemo } from 'react';
import type { BuildingGeo, WindowGeo } from '../lib/types';
import { useVelger } from '../state/store';

const NICHE = '#cfcbbd';
const DEPTH = 0.12;
// Pull the niche slightly into the wall so it reads as an inset opening and
// never z-fights with the facade plane.
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
        return {
          x: x - nx * INSET,
          z: z - nz * INSET,
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
