import { useVelger } from '../state/store';
import { formatNOK } from '../lib/format';
import { planSvgUrl, hemsSvgUrl, pdfUrl } from '../lib/data';
import type { AppData } from '../lib/types';

const STATUS_LABEL = { ledig: 'Ledig', reservert: 'Reservert', solgt: 'Solgt' } as const;

export function UnitPanel({ data }: { data: AppData }) {
  const selected = useVelger(s => s.selected);
  const status = useVelger(s => (selected ? s.status[selected] ?? 'ledig' : 'ledig'));
  const select = useVelger(s => s.select);
  if (!selected) return null;
  const u = data.units[selected];
  if (!u) return null;
  const k = data.site.kontakt;
  return (
    <aside className="panel" data-testid="unit-panel">
      <header className="panel-head">
        <div>
          <h2 data-testid="panel-id">{u.id}</h2>
          <p>{u.type} · {u.etasje}. etasje · <span className={`badge ${status}`}>{STATUS_LABEL[status]}</span></p>
        </div>
        <button className="close" onClick={() => select(null)} aria-label="Lukk">×</button>
      </header>
      <div className="panel-body">
        <a href={planSvgUrl(u.id)} target="_blank" rel="noreferrer" title="Åpne i full størrelse">
          <img className="plan" src={planSvgUrl(u.id)} alt={`Plantegning ${u.id}`} />
        </a>
        {u.hemsCa != null && <img className="plan hems" src={hemsSvgUrl(u.id)} alt={`Hems ${u.id}`} />}
        <dl>
          <dt>BRA-i</dt><dd>{u.braI} m²{u.braU ? ` + ${u.braU} m² (U)` : ''}</dd>
          {u.hemsCa != null && <><dt>Hems (ikke målbart)</dt><dd>ca {u.hemsCa} m²</dd></>}
          <dt>Pris</dt><dd data-testid="panel-pris">{formatNOK(u.pris)}</dd>
          <dt>Pris/m²</dt><dd>{formatNOK(u.kvmPris)}</dd>
        </dl>
        {u.duplex && <p className="duplex-note">Duplex: egen del i underetasjen med uteplass og parkering.</p>}
      </div>
      <footer className="panel-foot">
        <a className="cta" href={`mailto:${k.epost}?subject=${encodeURIComponent(`Dybwads gate 8 – ${u.id}`)}`}>Kontakt megler</a>
        <a className="cta ghost" href={pdfUrl(u.id)} download>Plantegning PDF</a>
        <p className="kontakt">{k.navn} · {k.telefon}</p>
      </footer>
    </aside>
  );
}
