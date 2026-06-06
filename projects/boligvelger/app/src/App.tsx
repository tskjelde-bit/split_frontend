import { useEffect, useState } from 'react';
import { VelgerCanvas } from './scene/VelgerCanvas';
import { Hud } from './ui/Hud';
import { UnitPanel } from './ui/UnitPanel';
import { loadAppData, fetchStatus } from './lib/data';
import { applyQaParam } from './lib/qa';
import { useVelger } from './state/store';
import type { AppData } from './lib/types';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  useEffect(() => { loadAppData().then(setData); }, []);
  useEffect(() => {
    if (data) applyQaParam(new URLSearchParams(location.search).get('qa'));
  }, [data]);
  useEffect(() => {
    fetchStatus().then(s => useVelger.getState().setStatus(s)).catch(() => { /* status er valgfritt */ });
  }, []);
  if (!data) return null;
  return (
    <section className="hero">
      <VelgerCanvas data={data} />
      <Hud data={data} />
      <UnitPanel data={data} />
    </section>
  );
}
