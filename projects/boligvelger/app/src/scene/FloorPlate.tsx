import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger, focusForFloor, type FloorFocus, type Mode } from '../state/store';
import { polyToShape, polyToRingShape, insetPolygon } from '../lib/shapes';
import { UnitMesh } from './UnitMesh';
import type { FloorGeo, EnvelopeGeo } from '../lib/types';

const GIPS_DARK = '#e5e2d6';
const GIPS_EXT = '#f3f1ea'; // exterior wall shell fallback
const EXPLODE_GAP = 2.2; // extra meters of air per floor index when exploded
const PARAPET = 0.35; // exploded view: wall shell shrinks to this height so unit volumes read from outside

export function explodedY(mode: Mode, elevation: number, index: number): number {
  return mode === 'exploded' ? elevation + index * EXPLODE_GAP : elevation;
}

export function floorIsFocused(focus: FloorFocus, floorId: string): boolean {
  if (focus === 'all') return true;
  if (focus === 'U1') return floorId === 'U' || floorId === '1';
  return focus === floorId;
}

interface Props { floor: FloorGeo; index: number; scale: number; slab: number; envelope: EnvelopeGeo; slabColor?: string; }

export function FloorPlate({ floor, index, scale, slab, envelope, slabColor }: Props) {
  const ref = useRef<THREE.Group>(null!);
  const wallRef = useRef<THREE.Mesh>(null!);
  const mode = useVelger(s => s.mode);
  const focus = useVelger(s => s.focus);
  const explode = useVelger(s => s.explode);
  const dimmed = mode === 'exploded' && !floorIsFocused(focus, floor.id);

  // In assembled view the shell is the only visible surface — clicking a floor's
  // walls/slab explodes the building with that floor focused. In exploded view
  // the shell stays inert so clicks reach the units (r3f raycast propagation).
  const assembled = mode !== 'exploded';
  const shellHandlers = {
    onClick: (e: { stopPropagation: () => void }) => {
      if (!assembled) return;
      e.stopPropagation();
      document.body.style.cursor = 'auto';
      explode(focusForFloor(floor.id));
    },
    onPointerOver: () => { if (assembled) document.body.style.cursor = 'pointer'; },
    onPointerOut: () => { if (assembled) document.body.style.cursor = 'auto'; },
  };

  const slabGeo = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(polyToShape(floor.outline, scale), {
      depth: slab, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2);
    return g;
  }, [floor, scale, slab]);

  // Exterior wall shell: a ring (envelope outline with an inward hole) extruded
  // to the clear wall height. Gives straight facades flush with the slab.
  const wallGeo = useMemo(() => {
    const wallThicknessPx = envelope.wallThickness / scale;
    const inner = insetPolygon(floor.outline, wallThicknessPx);
    const g = new THREE.ExtrudeGeometry(
      polyToRingShape(floor.outline, inner, scale),
      { depth: floor.height - slab, bevelEnabled: false },
    );
    g.rotateX(-Math.PI / 2);
    return g;
  }, [floor, scale, slab, envelope]);

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
    // Exploded: shrink the wall shell to a low parapet so the unit volumes
    // (and their hover/select highlight) are visible from outside the plate.
    const wallTarget = mode === 'exploded' ? PARAPET / (floor.height - slab) : 1;
    wallRef.current.scale.y = THREE.MathUtils.damp(wallRef.current.scale.y, wallTarget, 3.5, dt);
  });

  return (
    <group ref={ref} position-y={floor.elevation}>
      <mesh geometry={slabGeo} castShadow receiveShadow {...shellHandlers}>
        <meshStandardMaterial color={slabColor ?? GIPS_DARK} roughness={0.9} transparent={dimmed} opacity={dimmed ? 0.25 : 1} />
      </mesh>
      <group position-y={slab}>
        <mesh ref={wallRef} geometry={wallGeo} castShadow receiveShadow {...shellHandlers}>
          {/* polygonOffset pulls the wall slightly toward the camera in depth so
              its interior face wins the z-test against common/unit blocks that
              the data authors flush to the inner wall plane (no z-fighting). */}
          <meshStandardMaterial
            color={floor.facade ?? GIPS_EXT}
            roughness={0.85}
            transparent={dimmed}
            opacity={dimmed ? 0.25 : 1}
            polygonOffset
            polygonOffsetFactor={-1}
            polygonOffsetUnits={-1}
          />
        </mesh>
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
