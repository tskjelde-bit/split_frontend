import { useCallback, useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { CameraControls } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import { polyCentroid } from '../lib/shapes';
import { useVelger, type Mode } from '../state/store';
import type { BuildingGeo } from '../lib/types';

// Fixed 3/4 view DIRECTION per mode (the oblique look is intentional). The
// camera DISTANCE and TARGET are solved deterministically by fitting the
// building's world-space AABB inside a padded sub-rectangle of the viewport —
// no aspect-factor or lateral-shift heuristics. Target is the AABB centre,
// which also keeps the building horizontally centred at every azimuth.
//
// CAMERA-POSITION FORMULA (see solveFit): forward = -dir, and
//   camPos = target + forward * (-dist) = target + dir * dist.
// So the camera sits on the SAME-SIGN side as `dir`: a -x component puts the
// lens on the world -x side, a -z component puts it on the world -z side.
//
// World convention: x = px*scale - cx (px 748 = street/SW eave → world -x),
// z = cz - py*scale (py 1700 = SE gable / Ole Fladagers gate → world -z;
// py 375 = NW gable → world +z). The ark + 2 dormers + 5 window axes live on
// the WEST/street slope (world -x), the SE gable on world -z. To face BOTH we
// place the camera in the (-x, -z) quadrant looking back at the centre, i.e.
// dir has NEGATIVE x and NEGATIVE z.
//
// The z magnitude is deliberately SMALL relative to x (~0.28x): the street
// slope is the short, steep one (ridgeOffset 0.4) so a large -z swings the
// lens nearly face-on to the SE gable and you end up looking OVER the ridge
// onto the long back slope (the previous (-1,*,-0.7) "back of building" bug).
// (-1, 0.28, -0.45) keeps the street facade + dormers frontal and dominant
// while the SE gable supplies the 3/4 depth. Verified empirically from
// headless renders, not from sign reasoning alone.
const DIR: Record<Mode, THREE.Vector3> = {
  landing:  new THREE.Vector3(-1,  0.28, -0.45).normalize(),
  orbit:    new THREE.Vector3(-1,  0.28, -0.45).normalize(),
  exploded: new THREE.Vector3(-1,  0.45, -0.45).normalize(),
};

// HUD safe areas, as fractions of the viewport. Reserve space for the title
// block (top), the hint/chips (bottom) and a little air on the sides. The
// building must project entirely inside the remaining rectangle.
const PAD = { top: 0.22, bottom: 0.16, left: 0.06, right: 0.06 };

// Extra height added to the AABB in exploded mode: plates rise by
// index*EXPLODE_GAP (gap 2.2m); the roof sits at the highest index (= number of
// floors), so the top extends by floors*gap. The base (y≈0) is unchanged.
const EXPLODE_GAP = 2.2;

type Fit = { camPos: THREE.Vector3; target: THREE.Vector3; dist: number };

/** Assembled world-space AABB computed analytically from the geometry data.
 *  World mapping (see shapes.polyToShape + Building centering + rotateX(-PI/2)):
 *    worldX = x*scale - cx ,  worldZ = cz - y*scale ,  worldY = elevation .. top
 *  This is race-free (no dependency on the damped explode animation) and covers
 *  the roof overhang because roof volume polys are included. */
function assembledBox(geo: BuildingGeo): THREE.Box3 {
  const [pcx, pcy] = polyCentroid(geo.envelope.poly);
  const cx = pcx * geo.scale;
  const cz = pcy * geo.scale;
  const box = new THREE.Box3();
  box.makeEmpty();
  const v = new THREE.Vector3();
  const addPoly = (poly: [number, number][], yLo: number, yHi: number) => {
    for (const [x, y] of poly) {
      const wx = x * geo.scale - cx;
      const wz = cz - y * geo.scale;
      box.expandByPoint(v.set(wx, yLo, wz));
      box.expandByPoint(v.set(wx, yHi, wz));
    }
  };
  for (const f of geo.floors) {
    const top = f.elevation + f.height;
    addPoly(f.outline, f.elevation, top);
    for (const c of f.common) addPoly(c, f.elevation, top);
    for (const u of f.units) addPoly(u.poly, f.elevation, top);
  }
  // Tightened saltak AABB: include chimney tops, ark/dormer rises, and the
  // horizontal eave overhang so the camera framing never clips the roof.
  const roofElev = geo.roof.elevation;
  const riseTop = roofElev + geo.roof.rise;
  const oh = geo.roof.eaveOverhang ?? 0;

  // Expand the roof rect by the eave overhang in all horizontal directions.
  const roofRect = geo.roof.rect;
  const rxs = roofRect.map((p) => p[0]);
  const rys = roofRect.map((p) => p[1]);
  const rxMin = Math.min(...rxs);
  const rxMax = Math.max(...rxs);
  const ryMin = Math.min(...rys);
  const ryMax = Math.max(...rys);
  // Convert px rect (with overhang) to world AABB corners.
  // cx / cz are already computed above (pcx/pcy * scale).
  const s = geo.scale;
  // world x: px*scale - cx; world z: cz - py*scale.
  const wxL = rxMin * s - cx - oh;  // west eave (overhang expands outward)
  const wxR = rxMax * s - cx + oh;  // east eave
  const wzN = cz - ryMin * s + oh;  // north (NW) gable end
  const wzS = cz - ryMax * s - oh;  // south (SE) gable end
  for (const [wx, wz] of [[wxL, wzN], [wxL, wzS], [wxR, wzN], [wxR, wzS]] as [number, number][]) {
    box.expandByPoint(v.set(wx, roofElev, wz));
    box.expandByPoint(v.set(wx, riseTop,  wz));
  }

  // Recess catslide overhang (NE wing extends past the main rect).
  if (geo.roof.recess) {
    const rp = geo.roof.recess.poly;
    const rpxs = rp.map((p) => p[0]);
    const rpys = rp.map((p) => p[1]);
    const recessTop = roofElev + geo.roof.recess.rise;
    const rwxR = Math.max(...rpxs) * s - cx + oh;
    const rwzS = cz - Math.max(...rpys) * s - oh;
    const rwzN = cz - Math.min(...rpys) * s + oh;
    box.expandByPoint(v.set(rwxR, roofElev, rwzS));
    box.expandByPoint(v.set(rwxR, roofElev, rwzN));
    box.expandByPoint(v.set(rwxR, recessTop, rwzS));
    box.expandByPoint(v.set(rwxR, recessTop, rwzN));
  }

  // Chimneys: boxes above the ridge.
  for (const chim of geo.roof.chimneys ?? []) {
    const chimX = chim.x * s - cx;
    const chimZ = cz - chim.y * s;
    const chimTop = riseTop + chim.above;
    box.expandByPoint(v.set(chimX - chim.w / 2, chimTop, chimZ - chim.d / 2));
    box.expandByPoint(v.set(chimX + chim.w / 2, chimTop, chimZ + chim.d / 2));
  }

  // Ark + dormers: extend bounding box outward (projection) and upward (rise).
  // Derive from envelope so the AABB stays in sync with any envelope edits.
  const streetA = geo.envelope.poly[5] as [number, number];
  const streetB = geo.envelope.poly[0] as [number, number];
  const [axW, azW] = [streetA[0] * s - cx, cz - streetA[1] * s];
  const [bxW, bzW] = [streetB[0] * s - cx, cz - streetB[1] * s];
  const addDormer = (spec: { t: number; projection: number; rise: number }) => {
    const dxW = axW + (bxW - axW) * spec.t;
    const dzW = azW + (bzW - azW) * spec.t;
    // outward normal on the street edge (world -x side).
    // dx/dz along edge = (bxW-axW, bzW-azW); outward normal is (-dz, dx) normalised.
    const edx = bxW - axW; const edz = bzW - azW; const elen = Math.hypot(edx, edz) || 1;
    const nx = -edz / elen; const nz = edx / elen;
    const frontX = dxW + nx * spec.projection;
    const frontZ = dzW + nz * spec.projection;
    const dorTop = roofElev + spec.rise + oh;
    box.expandByPoint(v.set(frontX - spec.projection, roofElev, frontZ));
    box.expandByPoint(v.set(frontX, dorTop, frontZ));
  };
  if (geo.roof.ark) addDormer(geo.roof.ark);
  for (const d of geo.roof.dormers ?? []) addDormer(d);

  if (geo.roof.frontispiece) {
    const f = geo.roof.frontispiece;
    addDormer({ t: f.t, projection: f.projection + 0.2, rise: f.apex });
  }

  return box;
}

/** Solve camera distance + target so every AABB corner projects inside the
 *  padded sub-rectangle. For auto-rotated landing/orbit the building spins, so
 *  the horizontal constraint uses the bounding-sphere radius (worst azimuth)
 *  while the vertical constraint uses the true corner extents. */
function solveFit(
  box: THREE.Box3,
  dir: THREE.Vector3,
  fov: number,
  aspect: number,
  rotates: boolean,
): Fit {
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const radius = size.length() / 2; // bounding-sphere radius

  // Angular limits after reserving the HUD safe areas. The target is anchored
  // at the AABB centre (screen centre), so the usable band is ASYMMETRIC: a
  // point may extend up to (0.5 - PAD.top) of the frustum height above centre
  // and (0.5 - PAD.bottom) below. Horizontal is symmetric.
  const vFov = THREE.MathUtils.degToRad(fov);
  const tanV = Math.tan(vFov / 2); // tan of half *full* vertical fov
  // Convert "fraction of full height from centre" -> tan(angle): a point at
  // fraction f of full height projects at tan = f * 2 * tanV.
  const limUp = (0.5 - PAD.top) * 2 * tanV;
  const limDown = (0.5 - PAD.bottom) * 2 * tanV;
  const usableH = 1 - PAD.left - PAD.right;
  const halfH = tanV * aspect * usableH;

  // Orthonormal view basis: forward = -dir (camera looks toward center along
  // -dir), up world-ish, right = forward × up.
  const forward = dir.clone().negate().normalize();
  const worldUp = new THREE.Vector3(0, 1, 0);
  const right = new THREE.Vector3().crossVectors(forward, worldUp).normalize();
  const up = new THREE.Vector3().crossVectors(right, forward).normalize();

  const corners = [
    new THREE.Vector3(box.min.x, box.min.y, box.min.z),
    new THREE.Vector3(box.min.x, box.min.y, box.max.z),
    new THREE.Vector3(box.min.x, box.max.y, box.min.z),
    new THREE.Vector3(box.min.x, box.max.y, box.max.z),
    new THREE.Vector3(box.max.x, box.min.y, box.min.z),
    new THREE.Vector3(box.max.x, box.min.y, box.max.z),
    new THREE.Vector3(box.max.x, box.max.y, box.min.z),
    new THREE.Vector3(box.max.x, box.max.y, box.max.z),
  ];

  // Required distance so each corner projects inside the limits. depth from the
  // camera = dist + off·forward (camera sits at center - forward*dist). For each
  // corner: |h| <= halfH*depth, v <= limUp*depth, -v <= limDown*depth.
  let dist = 0;
  for (const c of corners) {
    const off = c.clone().sub(center);
    const along = off.dot(forward); // signed depth offset from center
    const h = off.dot(right);
    const v = off.dot(up);
    const dH = Math.abs(h) / halfH - along;
    const dUp = v > 0 ? v / limUp - along : 0;
    const dDown = v < 0 ? -v / limDown - along : 0;
    dist = Math.max(dist, dH, dUp, dDown);
  }

  // Auto-rotate: the silhouette's horizontal extent changes per azimuth. Use
  // the bounding-sphere radius for the horizontal constraint so a full 360°
  // never clips. Vertical is azimuth-invariant (rotation is about world Y).
  if (rotates) {
    const dSphere = radius / halfH;
    dist = Math.max(dist, dSphere);
  }

  // Target is the AABB centre (projects at screen centre). The asymmetric
  // up/down limits above already keep the building clear of the title (top) and
  // chips/hint (bottom) — no lateral or vertical shift hack needed.
  const target = center.clone();
  const camPos = target.clone().add(forward.clone().multiplyScalar(-dist));
  return { camPos, target, dist };
}

interface Props {
  geo: BuildingGeo;
}

export function CameraRig({ geo }: Props) {
  const ref = useRef<CameraControls>(null!);
  const mode = useVelger((s) => s.mode);
  const setMode = useVelger((s) => s.setMode);
  const size = useThree((s) => s.size);
  const camera = useThree((s) => s.camera as THREE.PerspectiveCamera);

  // Assembled world AABB, derived analytically from the geometry (race-free).
  const baseBox = useMemo(() => assembledBox(geo), [geo]);
  // In exploded mode the roof (highest element) rises by floors*GAP; the base
  // (ground floor at y=0) is unchanged.
  const explodeRise = geo.floors.length * EXPLODE_GAP;
  const started = useRef(false);

  const boxForMode = useCallback(
    (m: Mode): THREE.Box3 => {
      const b = baseBox.clone();
      if (m === 'exploded') b.max.y += explodeRise;
      return b;
    },
    [baseBox, explodeRise],
  );

  const applyFit = useCallback(
    (m: Mode, transition: boolean) => {
      if (!ref.current) return;
      const box = boxForMode(m);
      const aspect = size.width / size.height;
      const rotates = m === 'landing';
      const fit = solveFit(box, DIR[m], camera.fov, aspect, rotates);
      ref.current.minDistance = fit.dist * 0.4;
      ref.current.maxDistance = fit.dist * 2.5;
      ref.current.setLookAt(
        fit.camPos.x, fit.camPos.y, fit.camPos.z,
        fit.target.x, fit.target.y, fit.target.z,
        transition,
      );
    },
    [boxForMode, size.width, size.height, camera],
  );

  // Expose a minimal QA camera API on window.__velgerCamera so headless facade
  // comparison scripts can re-frame from a given direction without UI interaction.
  // Harmless in production; guarded so it only attaches when the controls exist.
  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).__velgerCamera = {
      setView: (dirX: number, dirY: number, dirZ: number) => {
        if (!ref.current) return;
        const dir = new THREE.Vector3(dirX, dirY, dirZ).normalize();
        const box = boxForMode('orbit');
        const aspect = size.width / size.height;
        const fit = solveFit(box, dir, camera.fov, aspect, false);
        ref.current.setLookAt(
          fit.camPos.x, fit.camPos.y, fit.camPos.z,
          fit.target.x, fit.target.y, fit.target.z,
          false,
        );
      },
    };
    return () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).__velgerCamera;
    };
  }, [boxForMode, size.width, size.height, camera]);

  // Initial fit on the first frame (camera/controls ready), then auto-rotate.
  useFrame((_, dt) => {
    if (!started.current && ref.current) {
      started.current = true;
      applyFit(useVelger.getState().mode, false);
    }
    if (useVelger.getState().mode === 'landing' && ref.current) {
      ref.current.azimuthAngle += dt * 0.12;
    }
  });

  // Re-frame on mode change (smooth) and on viewport resize (snap).
  useEffect(() => {
    if (started.current) applyFit(mode, true);
  }, [mode, applyFit]);

  useEffect(() => {
    if (started.current) applyFit(useVelger.getState().mode, false);
  }, [size.width, size.height, applyFit]);

  // First user interaction promotes landing -> orbit.
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const onStart = () => {
      if (useVelger.getState().mode === 'landing') setMode('orbit');
    };
    c.addEventListener('controlstart', onStart);
    return () => c.removeEventListener('controlstart', onStart);
  }, [setMode]);

  return (
    <CameraControls
      ref={ref}
      makeDefault
      minDistance={10}
      maxDistance={160}
      maxPolarAngle={Math.PI / 2.05}
      smoothTime={0.45}
    />
  );
}
