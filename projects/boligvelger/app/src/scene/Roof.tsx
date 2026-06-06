import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger } from '../state/store';
import { polyToShape } from '../lib/shapes';
import { explodedY } from './FloorPlate';
import type { RoofGeo } from '../lib/types';

export function Roof({ roof, scale, index }: { roof: RoofGeo; scale: number; index: number }) {
  const ref = useRef<THREE.Group>(null!);
  const mode = useVelger(s => s.mode);
  const geos = useMemo(() => roof.volumes.map(v => {
    const g = new THREE.ExtrudeGeometry(polyToShape(v.poly, scale), { depth: v.height, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    return g;
  }), [roof, scale]);
  useFrame((_, dt) => {
    const target = explodedY(mode, roof.elevation, index);
    ref.current.position.y = THREE.MathUtils.damp(ref.current.position.y, target, 3.5, dt);
  });
  return (
    <group ref={ref} position-y={roof.elevation}>
      {geos.map((g, i) => (
        <mesh key={i} geometry={g} castShadow>
          <meshStandardMaterial color="#efece1" roughness={0.9} />
        </mesh>
      ))}
    </group>
  );
}
