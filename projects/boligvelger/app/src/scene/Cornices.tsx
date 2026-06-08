import { useMemo } from 'react';
import * as THREE from 'three';
import { polyToRingShape, insetPolygon } from '../lib/shapes';
import { edgeDentils } from '../lib/facade';
import { useVelger } from '../state/store';
import type { BuildingGeo } from '../lib/types';

const BAND_H = 0.18;   // gesimsbåndets høyde
const BAND_OUT = 0.12; // utkraging utenfor fasadelivet
const DENTIL = { w: 0.18, h: 0.14, d: 0.10, spacing: 0.42 };

/** Hvite etasjegesimser (over 1. og 2. etg) + takfotgesims med tannsnitt.
 *  Statisk i montert visning; skjules i exploded (etasjeplatene er helten). */
export function Cornices({ geo }: { geo: BuildingGeo }) {
  const mode = useVelger((s) => s.mode);

  const bands = useMemo(() => {
    const outline = geo.envelope.poly;
    const outer = insetPolygon(outline, -BAND_OUT / geo.scale);
    const ring = polyToRingShape(outer, outline, geo.scale);
    const mk = (y: number) => {
      // ExtrudeGeometry(depth) + rotateX(-PI/2) spenner y ∈ [0, BAND_H] (samme
      // mønster som FloorPlate slabGeo) — translate med båndets UNDERKANT.
      const g = new THREE.ExtrudeGeometry(ring, { depth: BAND_H, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
      g.translate(0, y, 0);
      return g;
    };
    // y = topp av etasje N (elevation + height) minus båndhøyden
    const tops = geo.floors.filter((f) => f.id === '1' || f.id === '2')
      .map((f) => f.elevation + f.height - BAND_H);
    const eave = geo.roof.elevation - BAND_H; // takfot
    return [...tops, eave].map(mk);
  }, [geo]);

  const dentils = useMemo(
    () => edgeDentils(geo.envelope.poly, geo.scale, DENTIL.spacing),
    [geo],
  );

  if (mode === 'exploded') return null;

  const mats = geo.materials;
  const dentilY = geo.roof.elevation - BAND_H - DENTIL.h / 2;

  return (
    <group>
      {bands.map((g, i) => (
        <mesh key={i} geometry={g} castShadow receiveShadow>
          <meshStandardMaterial color={mats.pussHvit} roughness={0.85} />
        </mesh>
      ))}
      {dentils.map((d, i) => (
        <mesh key={`d${i}`} position={[d.x, dentilY, d.z]} rotation={[0, d.angle, 0]}>
          <boxGeometry args={[DENTIL.w, DENTIL.h, DENTIL.d * 2]} />
          <meshStandardMaterial color={mats.pussHvit} roughness={0.85} />
        </mesh>
      ))}
    </group>
  );
}
