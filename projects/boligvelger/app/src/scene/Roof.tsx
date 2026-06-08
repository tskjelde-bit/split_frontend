import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger } from '../state/store';
import { explodedY } from './FloorPlate';
import {
  pxToWorld,
  slabFromQuad,
  prismFromTriangle,
  boxGeometry,
  gableProjection,
  skylightOnSlope,
  type V3,
} from '../lib/roofGeometry';
import type { RoofGeo, Materials, EnvelopeGeo } from '../lib/types';

const SLOPE = '#e8e4d8';   // roof planes (slightly darker than the gips walls) — overridden by materials when provided
const GABLE = '#f3f1ea';   // gable infill fallback
const CHIMNEY = '#d8cfc2'; // brick-ish fallback
const WINDOW = '#9c9788';  // recessed roof-window glass fallback
const SLAB_T = 0.14;       // roof plane thickness

/**
 * Parametric saltak (gable roof) for Dybwads gate 8.
 *
 * Built in roof-LOCAL coordinates: the group is positioned at y = roof.elevation
 * (and animated for the explode view), so geometry uses eave at local y=0 and
 * ridge at local y=rise — exactly like the floors extrude from local 0. World XZ
 * follows the shared convention x=px*scale, z=-(py*scale).
 */
export function Roof({ roof, envelope, scale, index, materials }: { roof: RoofGeo; envelope: EnvelopeGeo; scale: number; index: number; materials?: Materials }) {
  const ref = useRef<THREE.Group>(null!);
  const mode = useVelger((s) => s.mode);
  const explode = useVelger((s) => s.explode);

  const parts = useMemo(() => buildRoof(roof, envelope, scale), [roof, envelope, scale]);

  useFrame((_, dt) => {
    const target = explodedY(mode, roof.elevation, index);
    ref.current.position.y = THREE.MathUtils.damp(ref.current.position.y, target, 3.5, dt);
  });

  // Clicking the roof in assembled view opens the building (events bubble up
  // from the part meshes to this group).
  const assembled = mode !== 'exploded';
  return (
    <group
      ref={ref}
      position-y={roof.elevation}
      onClick={(e) => {
        if (!assembled) return;
        e.stopPropagation();
        document.body.style.cursor = 'auto';
        explode('all');
      }}
      onPointerOver={() => { if (assembled) document.body.style.cursor = 'pointer'; }}
      onPointerOut={() => { if (assembled) document.body.style.cursor = 'auto'; }}
    >
      {parts.slopes.map((g, i) => (
        <mesh key={`s${i}`} geometry={g} castShadow receiveShadow>
          <meshStandardMaterial color={materials?.takSort ?? SLOPE} roughness={0.9} />
        </mesh>
      ))}
      {parts.gables.map((g, i) => (
        <mesh key={`g${i}`} geometry={g} castShadow receiveShadow>
          <meshStandardMaterial color={materials?.pussRosa ?? GABLE} roughness={0.9} />
        </mesh>
      ))}
      {parts.windows.map((g, i) => (
        <mesh key={`w${i}`} geometry={g}>
          <meshStandardMaterial color={materials?.glassMork ?? WINDOW} roughness={1} />
        </mesh>
      ))}
      {parts.chimneys.map((g, i) => (
        <mesh key={`c${i}`} geometry={g} castShadow receiveShadow>
          <meshStandardMaterial color={materials?.takSort ?? CHIMNEY} roughness={0.95} />
        </mesh>
      ))}
    </group>
  );
}

interface RoofParts {
  slopes: THREE.BufferGeometry[];
  gables: THREE.BufferGeometry[];
  windows: THREE.BufferGeometry[];
  chimneys: THREE.BufferGeometry[];
}

function buildRoof(roof: RoofGeo, envelope: EnvelopeGeo, scale: number): RoofParts {
  const slopes: THREE.BufferGeometry[] = [];
  const gables: THREE.BufferGeometry[] = [];
  const windows: THREE.BufferGeometry[] = [];
  const chimneys: THREE.BufferGeometry[] = [];

  const rise = roof.rise;
  const oh = roof.eaveOverhang; // metres

  // --- Main saltak over the rect ----------------------------------------
  // rect = [[748,375],[1660,375],[1660,1700],[748,1700]]. ridgeAxis 'y' means the
  // ridge runs along the py axis at px = west + ridgeOffset*(east-west).
  const xs = roof.rect.map((p) => p[0]);
  const ys = roof.rect.map((p) => p[1]);
  const xWest = Math.min(...xs);
  const xEast = Math.max(...xs);
  const yLo = Math.min(...ys); // py=375 (NW gable end)
  const yHi = Math.max(...ys); // py=1700 (SE gable end)
  const xRidge = xWest + roof.ridgeOffset * (xEast - xWest);

  const [wxWest] = pxToWorld(xWest, 0, scale);
  const [wxEast] = pxToWorld(xEast, 0, scale);
  const [wxRidge] = pxToWorld(xRidge, 0, scale);
  const [, wzLo] = pxToWorld(0, yLo, scale);
  const [, wzHi] = pxToWorld(0, yHi, scale);

  // Eave world X with horizontal overhang on the two eave sides.
  const wxWestE = wxWest - oh;
  const wxEastE = wxEast + oh;
  // Rake overhang on the two gable ends (extend along z). py-low maps to higher
  // (less negative) z, so the outward overhang there is +z; at py-high it is -z.
  const wzLoE = wzLo + oh;
  const wzHiE = wzHi - oh;

  // Ridge + eave lines (eave at local y=0, ridge at local y=rise).
  const ridgeA: V3 = [wxRidge, rise, wzLoE];
  const ridgeB: V3 = [wxRidge, rise, wzHiE];
  const wEaveA: V3 = [wxWestE, 0, wzLoE]; // west (street) eave
  const wEaveB: V3 = [wxWestE, 0, wzHiE];
  const eEaveA: V3 = [wxEastE, 0, wzLoE]; // east (NE) eave
  const eEaveB: V3 = [wxEastE, 0, wzHiE];

  // Two slope planes as thin slabs (winding chosen so the outward face is up).
  slopes.push(slabFromQuad(ridgeA, ridgeB, wEaveB, wEaveA, SLAB_T)); // west slope
  slopes.push(slabFromQuad(ridgeB, ridgeA, eEaveA, eEaveB, SLAB_T)); // east slope

  // Gable infill triangles at both ends (px-true, no overhang), solid.
  const gableTri = (wz: number) => {
    const a: V3 = [wxWest, 0, wz];
    const b: V3 = [wxEast, 0, wz];
    const apex: V3 = [wxRidge, rise, wz];
    gables.push(prismFromTriangle(a, b, apex, 0.18));
  };
  gableTri(wzLo);
  gableTri(wzHi);

  // Local-y of the west slope at a given world x, used to seat ark/dormers ON
  // the slope. West slope rises from eave (wxWest, 0) to ridge (wxRidge, rise).
  const westSlopeYAt = (wx: number) => {
    const t = (wx - wxWest) / (wxRidge - wxWest);
    return THREE.MathUtils.clamp(t, 0, 1) * rise;
  };

  // --- Recess catslide over the NE wing ---------------------------------
  if (roof.recess) {
    const rxs = roof.recess.poly.map((p) => p[0]);
    const rys = roof.recess.poly.map((p) => p[1]);
    const rxWest = Math.min(...rxs); // 1660 (shared edge with the main mass)
    const rxEast = Math.max(...rxs); // 2030
    const ryLo = Math.min(...rys);   // 640
    const ryHi = Math.max(...rys);   // 1700
    const rRise = roof.recess.rise;

    const [wRxWest] = pxToWorld(rxWest, 0, scale);
    const [wRxEastRaw] = pxToWorld(rxEast, 0, scale);
    const wRxEast = wRxEastRaw + oh;
    const [, wRyLo] = pxToWorld(0, ryLo, scale);
    const [, wRyHiRaw] = pxToWorld(0, ryHi, scale);
    const wRyLoE = wRyLo + oh;
    const wRyHi = wRyHiRaw - oh;

    // Catslide: high at the shared edge (y=rRise) sloping down to 0 at the east
    // eave. It shares the x=1660 line with the main mass east eave plane.
    const hiA: V3 = [wRxWest, rRise, wRyLoE];
    const hiB: V3 = [wRxWest, rRise, wRyHi];
    const loA: V3 = [wRxEast, 0, wRyLoE];
    const loB: V3 = [wRxEast, 0, wRyHi];
    slopes.push(slabFromQuad(hiA, hiB, loB, loA, SLAB_T));

    // Vertical face where the catslide meets the main eave at x=1660 (0->rRise),
    // so there is no gap below the step. Two thin triangular prisms form the rect.
    const vA: V3 = [wRxWest, 0, wRyLoE];
    const vB: V3 = [wRxWest, 0, wRyHi];
    gables.push(prismFromTriangle(vA, vB, hiB, 0.001));
    gables.push(prismFromTriangle(vA, hiB, hiA, 0.001));

    // Triangular gable infills at the two wing ends so the wing reads as a
    // closed lean-to from the SE.
    const wingEnd = (wz: number) => {
      const lo: V3 = [wRxEast, 0, wz];
      const hi: V3 = [wRxWest, rRise, wz];
      const base: V3 = [wRxWest, 0, wz];
      gables.push(prismFromTriangle(base, lo, hi, 0.16));
    };
    wingEnd(wRyLo);
    wingEnd(wRyHi);
  }

  // --- Ark + dormers (edge 5 = SW street edge) --------------------------
  // Derive street edge from envelope so this stays in sync with any future
  // envelope edit instead of duplicating the coordinates here.
  const streetA = envelope.poly[5] as [number, number];
  const streetB = envelope.poly[0] as [number, number];
  const projectionWx = (t: number) =>
    pxToWorld(streetA[0] + (streetB[0] - streetA[0]) * t, 0, scale)[0];

  if (roof.ark) {
    const baseY = westSlopeYAt(projectionWx(roof.ark.t)) + 0.25;
    const a = gableProjection(roof.ark, streetA, streetB, scale, baseY);
    slopes.push(a.roof);
    gables.push(a.body, a.gableFace);
    if (a.window) windows.push(a.window.geom);
  }

  for (const d of roof.dormers ?? []) {
    const baseY = westSlopeYAt(projectionWx(d.t)) + 0.2;
    const g = gableProjection(d, streetA, streetB, scale, baseY);
    slopes.push(g.roof);
    gables.push(g.body, g.gableFace);
    if (g.window) windows.push(g.window.geom);
  }

  // --- Chimneys (boxes at the ridge, projecting above) ------------------
  for (const c of roof.chimneys ?? []) {
    const [cx, cz] = pxToWorld(c.x, c.y, scale);
    const top = rise + c.above;
    const baseLocal = rise - 0.3;
    const h = top - baseLocal;
    chimneys.push(boxGeometry(cx, baseLocal + h / 2, cz, c.w, h, c.d));
  }

  // --- Skylights (flat boxes lying on the west slope) -------------------
  for (const sk of roof.skylights ?? []) {
    windows.push(skylightOnSlope(sk, streetA, streetB, wxWest, wxRidge, rise, scale));
  }

  return { slopes, gables, windows, chimneys };
}
