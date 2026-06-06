import { useMemo } from 'react';
import * as THREE from 'three';
import { useVelger } from '../state/store';
import { polyToShape } from '../lib/shapes';
import type { UnitGeo } from '../lib/types';

export const GIPS = '#f3f1ea';
export const GREEN = '#1E3D2B';
export const GREEN_HOVER = '#2e5c44';
export const SOLGT_GRAY = '#b9b6ac';

interface Props { unit: UnitGeo; scale: number; height: number; dimmed: boolean; }

export function UnitMesh({ unit, scale, height, dimmed }: Props) {
  const hovered = useVelger(s => s.hovered === unit.unit);
  const selected = useVelger(s => s.selected === unit.unit);
  const status = useVelger(s => s.status[unit.unit] ?? 'ledig');
  const setHovered = useVelger(s => s.setHovered);
  const select = useVelger(s => s.select);

  const geometry = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(polyToShape(unit.poly, scale), {
      depth: height, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2); // svg plan (x,y) -> (x, -z), extrusion -> +y
    return g;
  }, [unit, scale, height]);

  const color = selected || hovered
    ? (selected ? GREEN : GREEN_HOVER)
    : status === 'solgt' ? SOLGT_GRAY : GIPS;

  return (
    <mesh
      geometry={geometry}
      castShadow
      receiveShadow
      onPointerOver={(e) => { e.stopPropagation(); if (status !== 'solgt') setHovered(unit.unit); }}
      onPointerOut={() => setHovered(null)}
      onClick={(e) => { e.stopPropagation(); if (status !== 'solgt') select(unit.unit); }}
    >
      <meshStandardMaterial
        color={color}
        roughness={0.85}
        metalness={0}
        transparent={dimmed}
        opacity={dimmed ? 0.25 : 1}
        emissive={selected || hovered ? GREEN : '#000000'}
        emissiveIntensity={selected ? 0.35 : hovered ? 0.2 : 0}
      />
    </mesh>
  );
}
