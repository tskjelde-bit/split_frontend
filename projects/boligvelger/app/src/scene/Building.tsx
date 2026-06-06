import { useMemo } from 'react';
import { polyCentroid } from '../lib/shapes';
import { FloorPlate } from './FloorPlate';
import { Roof } from './Roof';
import { Windows } from './Windows';
import { UnitTooltip } from '../ui/UnitTooltip';
import type { AppData } from '../lib/types';

export function Building({ data }: { data: AppData }) {
  const geo = data.geo;
  // center the model on origin using ground floor outline centroid
  const [cx, cz] = useMemo(() => {
    const [px, py] = polyCentroid(geo.floors[0].outline);
    return [px * geo.scale, py * geo.scale];
  }, [geo]);
  return (
    <group position={[-cx, 0, cz]}>
      {geo.floors.map((f, i) => (
        <FloorPlate key={f.id} floor={f} index={i} scale={geo.scale} slab={geo.slabThickness} />
      ))}
      <Roof roof={geo.roof} scale={geo.scale} index={geo.floors.length} />
      <Windows geo={geo} />
      <UnitTooltip data={data} />
    </group>
  );
}
