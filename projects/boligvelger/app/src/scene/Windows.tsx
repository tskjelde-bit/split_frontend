import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { FloorGeo, Materials, WindowGeo } from '../lib/types';
import { useVelger } from '../state/store';

const SURROUND_M = 0.14; // hvit omramming utenfor karmen
const FRAME_M = 0.07;    // sort karm synlig rundt glasset
const PROUD = 0.03;      // omramming står 3 cm proud av fasadelivet

interface Placement {
  x: number; z: number; angle: number; y: number; w: number; h: number; kind: string;
}

/** Vinduer for ÉN etasje, montert inne i FloorPlate-gruppen slik at de følger
 *  eksplosjons-animasjonen. Fades ut i eksplodert visning (veggen krymper til
 *  parapet). Hvert vindu = hvit omramming + sort karm m/midtpost + mørkt glass;
 *  kind=blind = kun hvitt panel. */
export function FloorWindows({ floor, windows, scale, materials }: {
  floor: FloorGeo; windows: WindowGeo[]; scale: number; materials: Materials;
}) {
  const mode = useVelger((s) => s.mode);
  const group = useRef<THREE.Group>(null!);
  const placements: Placement[] = useMemo(() => windows.map((w) => {
    const o = floor.outline;
    const a = o[w.edge], b = o[(w.edge + 1) % o.length];
    const ax = a[0] * scale, az = -(a[1] * scale);
    const bx = b[0] * scale, bz = -(b[1] * scale);
    const x = ax + (bx - ax) * w.t, z = az + (bz - az) * w.t;
    const dx = bx - ax, dz = bz - az;
    const len = Math.hypot(dx, dz) || 1;
    const nx = -dz / len, nz = dx / len; // utover
    return {
      x: x + nx * PROUD, z: z + nz * PROUD,
      angle: Math.atan2(bz - az, bx - ax),
      y: w.sill + w.height / 2, // lokal y — gruppen ligger på slab-nivå i FloorPlate
      w: w.width, h: w.height, kind: w.kind ?? 'window',
    };
  }), [floor, windows, scale]);

  useFrame((_, dt) => {
    const target = mode === 'exploded' ? 0 : 1;
    group.current.children.forEach((c) => {
      c.traverse((m) => {
        const mat = (m as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
        if (mat) {
          mat.opacity = THREE.MathUtils.damp(mat.opacity, target, 6, dt);
          mat.transparent = true;
          m.visible = mat.opacity > 0.02;
        }
      });
    });
  });

  return (
    <group ref={group}>
      {placements.map((p, i) => (
        <group key={i} position={[p.x, p.y, p.z]} rotation={[0, p.angle, 0]}>
          {/* hvit omramming (bakerst, størst) */}
          <mesh>
            <boxGeometry args={[p.w + 2 * SURROUND_M, p.h + 2 * SURROUND_M, 0.06]} />
            <meshStandardMaterial color={materials.pussHvit} roughness={0.85} />
          </mesh>
          {p.kind === 'window' && (
            <>
              <mesh position={[0, 0, 0.02]}>
                <boxGeometry args={[p.w, p.h, 0.05]} />
                <meshStandardMaterial color={materials.karmSort} roughness={0.7} />
              </mesh>
              <mesh position={[-p.w / 4 + FRAME_M / 4, 0, 0.045]}>
                <boxGeometry args={[p.w / 2 - 1.5 * FRAME_M, p.h - 2 * FRAME_M, 0.02]} />
                <meshStandardMaterial color={materials.glassMork} roughness={0.25} metalness={0.1} />
              </mesh>
              <mesh position={[p.w / 4 - FRAME_M / 4, 0, 0.045]}>
                <boxGeometry args={[p.w / 2 - 1.5 * FRAME_M, p.h - 2 * FRAME_M, 0.02]} />
                <meshStandardMaterial color={materials.glassMork} roughness={0.25} metalness={0.1} />
              </mesh>
            </>
          )}
        </group>
      ))}
    </group>
  );
}
