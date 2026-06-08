import { useVelger } from '../state/store';
import type { BuildingGeo, EntranceSpec, BalconySpec } from '../lib/types';

/** Posisjon/utovernormal på en envelope-kant — samme konvensjon som FloorWindows. */
function onEdge(geo: BuildingGeo, edge: number, t: number) {
  const o = geo.envelope.poly;
  const a = o[edge], b = o[(edge + 1) % o.length];
  const ax = a[0] * geo.scale, az = -(a[1] * geo.scale);
  const bx = b[0] * geo.scale, bz = -(b[1] * geo.scale);
  const dx = bx - ax, dz = bz - az;
  const len = Math.hypot(dx, dz) || 1;
  return {
    x: ax + dx * t, z: az + dz * t,
    nx: -dz / len, nz: dx / len,
    angle: Math.atan2(nx, nz),
  };
}

export function Entrances({ geo }: { geo: BuildingGeo }) {
  const mode = useVelger((s) => s.mode);
  if (mode === 'exploded') return null;
  const m = geo.materials;
  const ground = geo.floors.find((f) => f.id === '1')!.elevation;
  return (
    <group>
      {geo.entrances.map((e: EntranceSpec, i: number) => {
        const p = onEdge(geo, e.edge, e.t);
        const lysH = e.overlys ? 0.4 : 0;
        return (
          <group key={i} position={[p.x, ground, p.z]} rotation={[0, p.angle, 0]}>
            <mesh position={[0, (e.height + lysH) / 2 + 0.06, 0.05]}>
              <boxGeometry args={[e.width + 0.24, e.height + lysH + 0.12, 0.06]} />
              <meshStandardMaterial color={m.pussHvit} roughness={0.85} />
            </mesh>
            <mesh position={[0, e.height / 2, 0.09]}>
              <boxGeometry args={[e.width, e.height, 0.08]} />
              <meshStandardMaterial color={m.karmSort} roughness={0.6} />
            </mesh>
            {e.overlys && (
              <mesh position={[0, e.height + lysH / 2, 0.09]}>
                <boxGeometry args={[e.width, lysH, 0.04]} />
                <meshStandardMaterial color={m.glassMork} roughness={0.25} />
              </mesh>
            )}
            {Array.from({ length: e.steps }, (_, k) => (
              <mesh key={k} position={[0, -0.08 - 0.16 * k, 0.15 + 0.3 * k]}>
                <boxGeometry args={[e.width + 0.4, 0.16, 0.3]} />
                <meshStandardMaterial color={m.pussHvit} roughness={0.9} />
              </mesh>
            ))}
          </group>
        );
      })}
      {geo.balconies.map((b: BalconySpec, i: number) => {
        const p = onEdge(geo, b.edge, b.t);
        const fl = geo.floors.find((f) => f.id === b.floor)!;
        const bars = Math.floor(b.width / 0.12);
        return (
          <group key={`b${i}`} position={[p.x, fl.elevation + 1.0, p.z]} rotation={[0, p.angle, 0]}>
            <mesh position={[0, 0, b.depth / 2]}>
              <boxGeometry args={[b.width, 0.08, b.depth]} />
              <meshStandardMaterial color={m.pussHvit} roughness={0.9} />
            </mesh>
            <mesh position={[0, 0.5, b.depth]}>
              <boxGeometry args={[b.width, 0.04, 0.04]} />
              <meshStandardMaterial color={m.karmSort} roughness={0.6} />
            </mesh>
            {Array.from({ length: bars }, (_, k) => (
              <mesh key={k} position={[-b.width / 2 + (k + 0.5) * 0.12, 0.27, b.depth]}>
                <boxGeometry args={[0.025, 0.5, 0.025]} />
                <meshStandardMaterial color={m.karmSort} roughness={0.6} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}
