import { formatNOK } from '../lib/format';
import { planSvgUrl, pdfUrl } from '../lib/data';
import { useVelger } from '../state/store';
import type { AppData } from '../lib/types';

export function FallbackList({ data }: { data: AppData }) {
  const status = useVelger(s => s.status);
  const byFloor = [1, 2, 3].map(e => ({
    etasje: e,
    units: Object.values(data.units).filter(u => u.etasje === e),
  }));
  return (
    <main className="fallback">
      <h1>{data.site.tittel}</h1>
      <p>{data.site.undertittel}</p>
      {byFloor.map(f => (
        <section key={f.etasje}>
          <h2>{f.etasje}. etasje</h2>
          {f.units.map(u => (
            <article key={u.id} className="f-unit">
              <img src={planSvgUrl(u.id)} alt={`Plantegning ${u.id}`} loading="lazy" />
              <div>
                <h3>{u.id} · {u.braI} m²</h3>
                <p>{formatNOK(u.pris)} · {status[u.id] ?? 'ledig'}</p>
                <a href={pdfUrl(u.id)} download>Plantegning PDF</a>
              </div>
            </article>
          ))}
        </section>
      ))}
    </main>
  );
}
