import * as THREE from 'three';
import type { GableSpec, SkylightSpec } from './types';

/** A 3D point in roof-local space (worldX, localY, worldZ). */
export type V3 = [number, number, number];

/** SVG px (px, py) -> roof-local world XZ. y is supplied separately.
 *  Convention shared with FloorPlate/Windows: x = px*scale, z = -(py*scale). */
export function pxToWorld(px: number, py: number, scale: number): [number, number] {
  return [px * scale, -(py * scale)];
}

function add(geos: THREE.BufferGeometry[], g: THREE.BufferGeometry) {
  geos.push(g);
}

/** Build a flat (zero-thickness) triangulated geometry from a fan of vertices.
 *  Used for the gable infill triangles. Caller supplies vertices already in
 *  world-local space. The polygon is assumed convex (triangle / quad fan). */
export function polygonGeometry(verts: V3[]): THREE.BufferGeometry {
  const g = new THREE.BufferGeometry();
  const pos: number[] = [];
  for (let i = 1; i < verts.length - 1; i++) {
    pos.push(...verts[0], ...verts[i], ...verts[i + 1]);
  }
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}

/** A thin solid slab spanning a quad (a,b,c,d in order around the perimeter),
 *  given a thickness `t` extruded along the quad's normal. Produces a closed
 *  box-like solid: top face, bottom face and four side bands. Robust against
 *  being seen from below (eave underside) and never shows a back-face hole. */
export function slabFromQuad(a: V3, b: V3, c: V3, d: V3, t: number): THREE.BufferGeometry {
  const va = new THREE.Vector3(...a);
  const vb = new THREE.Vector3(...b);
  const vc = new THREE.Vector3(...c);
  const vd = new THREE.Vector3(...d);
  // normal from the first triangle (a,b,c)
  const n = new THREE.Vector3()
    .subVectors(vb, va)
    .cross(new THREE.Vector3().subVectors(vc, va))
    .normalize()
    .multiplyScalar(t);
  const top = [va, vb, vc, vd];
  const bot = top.map(p => p.clone().sub(n));

  const g = new THREE.BufferGeometry();
  const pos: number[] = [];
  const quad = (p0: THREE.Vector3, p1: THREE.Vector3, p2: THREE.Vector3, p3: THREE.Vector3) => {
    pos.push(p0.x, p0.y, p0.z, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
    pos.push(p0.x, p0.y, p0.z, p2.x, p2.y, p2.z, p3.x, p3.y, p3.z);
  };
  // top (outward) face
  quad(top[0], top[1], top[2], top[3]);
  // bottom face (reverse winding)
  quad(bot[3], bot[2], bot[1], bot[0]);
  // four sides
  for (let i = 0; i < 4; i++) {
    const j = (i + 1) % 4;
    quad(top[i], top[j], bot[j], bot[i]);
  }
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}

/** A solid prism between a top triangle and a bottom triangle (vertical offset
 *  by `t` downward in y). Used for gable infill so the triangle reads solid. */
export function prismFromTriangle(a: V3, b: V3, c: V3, t: number): THREE.BufferGeometry {
  const g = new THREE.BufferGeometry();
  const top: V3[] = [a, b, c];
  const bot: V3[] = top.map(([x, y, z]) => [x, y - t, z]);
  const pos: number[] = [];
  const tri = (p: V3, q: V3, r: V3) => pos.push(...p, ...q, ...r);
  tri(top[0], top[1], top[2]);
  tri(bot[2], bot[1], bot[0]);
  for (let i = 0; i < 3; i++) {
    const j = (i + 1) % 3;
    tri(top[i], top[j], bot[j]);
    tri(top[i], bot[j], bot[i]);
  }
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}

/** A simple axis-aligned box solid centred at (cx, cy, cz). */
export function boxGeometry(
  cx: number, cy: number, cz: number, w: number, h: number, d: number,
): THREE.BufferGeometry {
  const g = new THREE.BoxGeometry(w, h, d);
  g.translate(cx, cy, cz);
  return g;
}

export interface GableProjectionResult {
  /** Box walls (two sides + front face) of the projecting dormer body. */
  body: THREE.BufferGeometry;
  /** The little gable roof (two slopes) capping the projection. */
  roof: THREE.BufferGeometry;
  /** The triangular gable infill above the window, facing the street. */
  gableFace: THREE.BufferGeometry;
  /** Window inset box, or null when the spec carries no window. */
  window: { geom: THREE.BufferGeometry } | null;
}

/**
 * Build a gable-fronted projection (ark / dormer) sitting on a roof slope.
 *
 * @param spec      GableSpec (edge + t locate it along an envelope edge).
 * @param edgeA     start vertex of the envelope edge in px [px,py].
 * @param edgeB     end vertex of the envelope edge in px [px,py].
 * @param scale     px->m scale.
 * @param baseY     local y of the projection's eave (its floor on the slope).
 * @param slopeYAt  fn returning the main-slope local y at a given world x, used
 *                  so the back of the projection meets the slope.
 */
export function gableProjection(
  spec: GableSpec,
  edgeA: [number, number],
  edgeB: [number, number],
  scale: number,
  baseY: number,
): GableProjectionResult {
  const [ax, az] = pxToWorld(edgeA[0], edgeA[1], scale);
  const [bx, bz] = pxToWorld(edgeB[0], edgeB[1], scale);
  // position along the edge
  const px = ax + (bx - ax) * spec.t;
  const pz = az + (bz - az) * spec.t;
  // edge direction (tangent) and outward normal. The envelope winds clockwise
  // in this z-flipped frame, so the outward normal is to the LEFT of the edge
  // direction (matches Windows.tsx).
  const dx = bx - ax;
  const dz = bz - az;
  const dlen = Math.hypot(dx, dz) || 1;
  const tx = dx / dlen;
  const tz = dz / dlen;
  const nx = -dz / dlen; // outward
  const nz = dx / dlen;

  const halfW = spec.width / 2;
  const proj = spec.projection;
  const rise = spec.rise;

  // Four base corners at baseY: left/right at the wall plane and at the
  // projected front. l/r are along the tangent; front is along the normal.
  const at = (along: number, out: number, y: number): V3 => [
    px + tx * along + nx * out,
    y,
    pz + tz * along + nz * out,
  ];
  const eaveL = at(-halfW, 0, baseY);
  const eaveR = at(halfW, 0, baseY);
  const frontL = at(-halfW, proj, baseY);
  const frontR = at(halfW, proj, baseY);
  // ridge of the little gable runs along the projection axis at mid width,
  // peaking `rise` above the eave, set back a touch from the very front.
  const apexBack: V3 = at(0, 0, baseY + rise);
  const apexFront: V3 = at(0, proj, baseY + rise);

  // Body: two side quads + front quad (between eave line and the gable face).
  // The gable face triangle sits above the front opening.
  const bodyGeos: THREE.BufferGeometry[] = [];
  // left side wall (trapezoid eaveL->frontL->apexFront-ish). Build as quad up to
  // ridge height at front and back.
  add(bodyGeos, polygonGeometry([eaveL, frontL, apexFront, apexBack]));
  add(bodyGeos, polygonGeometry([frontR, eaveR, apexBack, apexFront]));
  // front wall below the window opening: full rectangle from eave to ridge base.
  // We keep it solid; the window box is inset on top of it.
  const frontTopL: V3 = at(-halfW, proj, baseY + rise * 0.55);
  const frontTopR: V3 = at(halfW, proj, baseY + rise * 0.55);
  add(bodyGeos, polygonGeometry([frontL, frontR, frontTopR, frontTopL]));

  // Gable face: triangle from the two front-top corners up to the front apex.
  const gableFace = polygonGeometry([frontTopL, frontTopR, apexFront]);

  // Roof: two slopes from the ridge (apexBack..apexFront) down to the eaves.
  const roofGeos: THREE.BufferGeometry[] = [];
  const oh = 0.12; // small rake/eave overhang on the projection roof
  const eaveLo = at(-halfW - oh, -oh, baseY + 0.02);
  const eaveRo = at(halfW + oh, -oh, baseY + 0.02);
  const frontLo = at(-halfW - oh, proj + oh, baseY + 0.02);
  const frontRo = at(halfW + oh, proj + oh, baseY + 0.02);
  const ridgeBack: V3 = at(0, -oh, baseY + rise);
  const ridgeFront: V3 = at(0, proj + oh, baseY + rise);
  add(roofGeos, slabFromQuad(ridgeBack, ridgeFront, frontLo, eaveLo, 0.08));
  add(roofGeos, slabFromQuad(ridgeFront, ridgeBack, eaveRo, frontRo, 0.08));

  // Window inset box on the front gable face.
  let windowGeom: { geom: THREE.BufferGeometry } | null = null;
  if (spec.window) {
    const w = spec.window;
    const wy = baseY + w.sill + w.height / 2;
    const cx = px + nx * (proj - 0.04);
    const cz = pz + nz * (proj - 0.04);
    const box = new THREE.BoxGeometry(w.width, w.height, 0.12);
    // orient the box so its width runs along the tangent and depth along normal
    const angle = Math.atan2(tz, tx);
    box.rotateY(-angle);
    box.translate(cx, wy, cz);
    windowGeom = { geom: box };
  }

  return {
    body: mergeGeometries(bodyGeos),
    roof: mergeGeometries(roofGeos),
    gableFace,
    window: windowGeom,
  };
}

/** Flat dark box lying ON the west slope plane. `up` = 0 (eave) .. 1 (ridge).
 *  edgeA/edgeB = street edge in px; wxEave/wxRidge = world-x of eave and ridge. */
export function skylightOnSlope(
  spec: SkylightSpec,
  edgeA: [number, number], edgeB: [number, number],
  wxEave: number, wxRidge: number, rise: number, scale: number,
): THREE.BufferGeometry {
  const [, az] = pxToWorld(edgeA[0], edgeA[1], scale);
  const [, bz] = pxToWorld(edgeB[0], edgeB[1], scale);
  const z = az + (bz - az) * spec.t;
  const run = wxRidge - wxEave;                  // > 0: slope rises toward +x
  const theta = Math.atan2(rise, run);           // slope angle from horizontal
  const wx = wxEave + spec.up * run;
  const wy = spec.up * rise;
  const g = new THREE.BoxGeometry(spec.height, 0.06, spec.width); // length up-slope along x
  g.rotateZ(theta);                              // tilt onto the plane
  g.translate(wx, wy + 0.10, z);                 // 10 cm proud of the slope slab
  return g;
}

/** Merge a list of position-only BufferGeometries into one (no indices). */
export function mergeGeometries(geos: THREE.BufferGeometry[]): THREE.BufferGeometry {
  const pos: number[] = [];
  for (const g of geos) {
    const p = g.getAttribute('position');
    for (let i = 0; i < p.count; i++) pos.push(p.getX(i), p.getY(i), p.getZ(i));
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  out.computeVertexNormals();
  return out;
}
