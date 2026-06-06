import { Html } from '@react-three/drei';
import { useVelger } from '../state/store';
import { formatNOK } from '../lib/format';
import { polyCentroid } from '../lib/shapes';
import { explodedY } from '../scene/FloorPlate';
import type { AppData, FloorGeo } from '../lib/types';

export function UnitTooltip({ data }: { data: AppData }) {
  const hovered = useVelger(s => s.hovered);
  const mode = useVelger(s => s.mode);
  if (!hovered) return null;
  const info = data.units[hovered];

  // For duplex units (H0101, H0103) prefer the main floor (id !== 'U').
  // Fall back to U only if not found on any other floor.
  const floors = data.geo.floors;
  let floor: FloorGeo | undefined;
  let floorIndex = -1;

  // First pass: non-basement floors
  for (let i = 0; i < floors.length; i++) {
    const f = floors[i];
    if (f.id !== 'U' && f.units.some(u => u.unit === hovered)) {
      floor = f;
      floorIndex = i;
      break;
    }
  }
  // Fallback: basement floor
  if (!floor) {
    for (let i = 0; i < floors.length; i++) {
      const f = floors[i];
      if (f.units.some(u => u.unit === hovered)) {
        floor = f;
        floorIndex = i;
        break;
      }
    }
  }

  if (!info || !floor) return null;
  const unitGeo = floor.units.find(u => u.unit === hovered)!;
  const [cx, cy] = polyCentroid(unitGeo.poly);

  // World x/z matching scene convention (Windows.tsx): x = px*scale, z = -(py*scale)
  const wx = cx * data.geo.scale;
  const wz = -(cy * data.geo.scale);

  // Y: use explodedY to match the animated plate position, then add floor height + gap
  const wy = explodedY(mode, floor.elevation, floorIndex) + floor.height + 0.4;

  return (
    <Html position={[wx, wy, wz]} center distanceFactor={18} style={{ pointerEvents: 'none' }}>
      <div className="tooltip">
        <strong>{info.id} · {info.braI} m²</strong>
        <span>{formatNOK(info.pris)}</span>
      </div>
    </Html>
  );
}
