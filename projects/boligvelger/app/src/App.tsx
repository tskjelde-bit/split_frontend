import { useEffect, useState } from 'react';
import { VelgerCanvas } from './scene/VelgerCanvas';
import { loadAppData } from './lib/data';
import { applyQaParam } from './lib/qa';
import type { AppData } from './lib/types';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  useEffect(() => { loadAppData().then(setData); }, []);
  useEffect(() => {
    if (data) applyQaParam(new URLSearchParams(location.search).get('qa'));
  }, [data]);
  if (!data) return null;
  return (
    <section className="hero">
      <VelgerCanvas data={data} />
    </section>
  );
}
