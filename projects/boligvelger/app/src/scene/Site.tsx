import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger } from '../state/store';
import { slabFromQuad, type V3 } from '../lib/roofGeometry';
import { insetPolygon } from '../lib/shapes';
import { edgeDentils } from '../lib/facade';
import type { BuildingGeo } from '../lib/types';

const GROUND = '#D9D5CC';

/** Tomt: skrånende bakkeplate + hekk + mur/smijernsgjerde. Fades i exploded. */
export function Site({ geo }: { geo: BuildingGeo }) {
  const mode = useVelger((s) => s.mode);
  const group = useRef<THREE.Group>(null!);
  const site = geo.site;

  const parts = useMemo(() => {
    if (!site) return null;
    const s = geo.scale;
    const xs = geo.envelope.poly.map((p) => p[0] * s);
    const ys = geo.envelope.poly.map((p) => p[1] * s);
    // px-rom: x øker mot NE-siden, y øker mot SE (Ole Fladagers gate).
    // world: x = px·s, z = −py·s. SW-kant (gata) = min(x)-siden (edge 5).
    const xMin = Math.min(...xs) - site.groundMargin.sw;
    const xMax = Math.max(...xs) + site.groundMargin.ne;
    const yMin = Math.min(...ys) - site.groundMargin.nw; // NV-ende (py lav)
    const yMax = Math.max(...ys) + site.groundMargin.se; // SE-ende (py høy)
    const yAt = (py: number) => {
      const t = (py - Math.min(...ys)) / (Math.max(...ys) - Math.min(...ys));
      return site.groundY.nw + t * (site.groundY.se - site.groundY.nw);
    };
    // Fire hjørner (world): z = −py·s, fall langs py-aksen.
    const c = (x: number, py: number): V3 => [x, yAt(py), -py];
    const ground = slabFromQuad(c(xMin, yMin), c(xMax, yMin), c(xMax, yMax), c(xMin, yMax), 0.25);

    // Hekk + gjerde: plasseringer langs outset-kopier av envelope.
    const hedgeLine = insetPolygon(geo.envelope.poly, -1.1 / s);
    const fenceLine = insetPolygon(geo.envelope.poly, -1.9 / s);
    const hedgeRuns = site.hedgeEdges.map((e) => ({
      a: hedgeLine[e] as [number, number],
      b: hedgeLine[(e + 1) % hedgeLine.length] as [number, number],
    }));
    const fencePosts = site.fenceEdges.flatMap((e) => {
      const sub: [number, number][] = [fenceLine[e] as [number, number], fenceLine[(e + 1) % fenceLine.length] as [number, number]];
      return edgeDentils([sub[0], sub[1], sub[1], sub[0]], s, 0.14)
        .filter((_, i, arr) => i < arr.length / 2); // én retning av det degenererte "polygonet"
    });
    const fenceRuns = site.fenceEdges.map((e) => ({
      a: fenceLine[e] as [number, number],
      b: fenceLine[(e + 1) % fenceLine.length] as [number, number],
    }));
    return { ground, hedgeRuns, fenceRuns, fencePosts, yAt, s };
  }, [geo, site]);

  useFrame((_, dt) => {
    if (!group.current) return;
    const target = mode === 'exploded' ? 0 : 1;
    group.current.traverse((m) => {
      const mat = (m as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
      if (mat) {
        mat.opacity = THREE.MathUtils.damp(mat.opacity, target, 5, dt);
        mat.transparent = true;
        (m as THREE.Mesh).visible = mat.opacity > 0.02;
      }
    });
  });

  if (!site || !parts) return null;
  const m = geo.materials;
  const runMesh = (a: [number, number], b: [number, number], h: number, d: number, color: string, lift: number) => {
    const ax = a[0] * parts.s, az = -(a[1] * parts.s);
    const bx = b[0] * parts.s, bz = -(b[1] * parts.s);
    const len = Math.hypot(bx - ax, bz - az);
    const y = parts.yAt(((a[1] + b[1]) / 2) * parts.s) + lift + h / 2;
    return (
      <mesh position={[(ax + bx) / 2, y, (az + bz) / 2]} rotation={[0, Math.atan2(bz - az, bx - ax), 0]}>
        <boxGeometry args={[len - 2, h, d]} />
        <meshStandardMaterial color={color} roughness={1} />
      </mesh>
    );
  };
  return (
    <group ref={group}>
      <mesh geometry={parts.ground} receiveShadow>
        <meshStandardMaterial color={GROUND} roughness={1} />
      </mesh>
      {parts.hedgeRuns.map((r, i) => (
        <group key={`h${i}`}>{runMesh(r.a, r.b, 1.1, 0.7, m.hekkGronn, 0)}</group>
      ))}
      {parts.fenceRuns.map((r, i) => (
        <group key={`f${i}`}>
          {runMesh(r.a, r.b, 0.4, 0.18, m.pussHvit, 0)}
          {runMesh(r.a, r.b, 0.04, 0.04, m.karmSort, 0.9)}
        </group>
      ))}
      {parts.fencePosts.map((p, i) => (
        <mesh key={`p${i}`} position={[p.x, parts.yAt(-p.z) + 0.65, p.z]}>
          <boxGeometry args={[0.02, 0.5, 0.02]} />
          <meshStandardMaterial color={m.karmSort} roughness={0.6} />
        </mesh>
      ))}
    </group>
  );
}
