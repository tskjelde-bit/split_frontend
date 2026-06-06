import type { RoofGeo } from '../lib/types';

// TODO(step-C): Replace this stub with the parametric saltak builder
// (two roof slopes, gable triangles, catslide over the recess, ark + dormers,
// chimneys). For now it accepts the new RoofGeo spec and renders nothing so the
// build stays green while the wall shell work lands. No roof is expected in QA
// screenshots until step C ships.
export function Roof(_props: { roof: RoofGeo; scale: number; index: number }) {
  return null;
}
