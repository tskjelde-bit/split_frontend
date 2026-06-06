import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger, type FloorFocus, type Mode } from '../state/store';
import { polyToShape } from '../lib/shapes';
import { UnitMesh } from './UnitMesh';
import type { FloorGeo } from '../lib/types';

const GIPS_DARK = '#e5e2d6';
const EXPLODE_GAP = 2.2; // extra meters of air per floor index when exploded

export function explodedY(mode: Mode, elevation: number, index: number): number {
  return mode === 'exploded' ? elevation + index * EXPLODE_GAP : elevation;
}

export function floorIsFocused(focus: FloorFocus, floorId: string): boolean {
  if (focus === 'all') return true;
  if (focus === 'U1') return floorId === 'U' || floorId === '1';
  return focus === floorId;
}

interface Props { floor: FloorGeo; index: number; scale: number; slab: number; }

export function FloorPlate({ floor, index, scale, slab }: Props) {
  const ref = useRef<THREE.Group>(null!);
  const mode = useVelger(s => s.mode);
  const focus = useVelger(s => s.focus);
  const dimmed = mode === 'exploded' && !floorIsFocused(focus, floor.id);

  const slabGeo = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(polyToShape(floor.outline, scale), {
      depth: slab, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2);
    return g;
  }, [floor, scale, slab]);

  const commonGeos = useMemo(() => floor.common.map(poly => {
    const g = new THREE.ExtrudeGeometry(polyToShape(poly, scale), {
      depth: floor.height - slab, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2);
    return g;
  }), [floor, scale, slab]);

  useFrame((_, dt) => {
    const target = explodedY(mode, floor.elevation, index);
    ref.current.position.y = THREE.MathUtils.damp(ref.current.position.y, target, 3.5, dt);
  });

  return (
    <group ref={ref} position-y={floor.elevation}>
      <mesh geometry={slabGeo} castShadow receiveShadow>
        <meshStandardMaterial color={GIPS_DARK} roughness={0.9} transparent={dimmed} opacity={dimmed ? 0.25 : 1} />
      </mesh>
      <group position-y={slab}>
        {commonGeos.map((g, i) => (
          <mesh key={i} geometry={g} receiveShadow>
            <meshStandardMaterial color={GIPS_DARK} roughness={0.9} transparent={dimmed} opacity={dimmed ? 0.2 : 0.6} />
          </mesh>
        ))}
        {floor.units.map(u => (
          <UnitMesh key={u.id} unit={u} scale={scale} height={floor.height - slab} dimmed={dimmed} />
        ))}
      </group>
    </group>
  );
}
