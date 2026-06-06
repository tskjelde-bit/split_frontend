import { useVelger } from '../state/store';
import { FloorChips } from './FloorChips';
import type { AppData } from '../lib/types';

export function Hud({ data }: { data: AppData }) {
  const mode = useVelger(s => s.mode);
  return (
    <div className="hud">
      <header className={`hud-title${mode === 'landing' ? '' : ' compact'}`}>
        <h1>{data.site.tittel}</h1>
        <p>{data.site.undertittel}</p>
      </header>
      {mode === 'landing' && <p className="hint">Dra for å utforske</p>}
      <FloorChips />
    </div>
  );
}
