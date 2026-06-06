import { useEffect, useState } from 'react';
import { VelgerCanvas } from './scene/VelgerCanvas';
import { Hud } from './ui/Hud';
import { UnitPanel } from './ui/UnitPanel';
import { FallbackList } from './ui/FallbackList';
import { InfoSections } from './ui/InfoSections';
import { loadAppData, fetchStatus } from './lib/data';
import { detectWebGL } from './lib/webgl';
import { applyQaParam } from './lib/qa';
import { useVelger } from './state/store';
import type { AppData } from './lib/types';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [webgl] = useState(detectWebGL);
  useEffect(() => { loadAppData().then(setData); }, []);
  useEffect(() => {
    fetchStatus().then(s => useVelger.getState().setStatus(s)).catch(() => { /* valgfritt */ });
  }, []);
  useEffect(() => {
    if (data) applyQaParam(new URLSearchParams(location.search).get('qa'));
  }, [data]);
  if (!data) return null;
  if (!webgl) return <FallbackList data={data} />;
  return (
    <>
      <section className="hero">
        <VelgerCanvas data={data} />
        <Hud data={data} />
        <UnitPanel data={data} />
      </section>
      <InfoSections site={data.site} />
    </>
  );
}
