import { useMemo } from 'react';
import { polyCentroid } from '../lib/shapes';
import { FloorPlate } from './FloorPlate';
import { Roof } from './Roof';
import { UnitTooltip } from '../ui/UnitTooltip';
import type { AppData } from '../lib/types';

export function Building({ data }: { data: AppData }) {
  const geo = data.geo;
  // center the model on origin using the canonical envelope centroid
  const [cx, cz] = useMemo(() => {
    const [px, py] = polyCentroid(geo.envelope.poly);
    return [px * geo.scale, py * geo.scale];
  }, [geo]);
  return (
    <group position={[-cx, 0, cz]}>
      {geo.floors.map((f, i) => (
        <FloorPlate
          key={f.id}
          floor={f}
          index={i}
          scale={geo.scale}
          slab={geo.slabThickness}
          envelope={geo.envelope}
          slabColor={geo.materials?.pussHvit}
          windows={geo.windows.filter((w) => w.floor === f.id)}
          materials={geo.materials}
        />
      ))}
      <Roof roof={geo.roof} envelope={geo.envelope} scale={geo.scale} index={geo.floors.length} materials={geo.materials} />
      <UnitTooltip data={data} />
    </group>
  );
}
