import { useVelger, type FloorFocus } from '../state/store';

const CHIPS: { id: FloorFocus | 'assemble'; label: string }[] = [
  { id: 'U1', label: '1. etg' },
  { id: '2', label: '2. etg' },
  { id: '3', label: '3. etg' },
  { id: 'all', label: 'Alle 16' },
  { id: 'assemble', label: 'Samle bygget' },
];

export function FloorChips() {
  const mode = useVelger(s => s.mode);
  const focus = useVelger(s => s.focus);
  const explode = useVelger(s => s.explode);
  const assemble = useVelger(s => s.assemble);
  return (
    <nav className="chips">
      {CHIPS.map(c => {
        if (c.id === 'assemble') {
          if (mode !== 'exploded') return null;
          return <button key={c.id} className="chip" onClick={assemble}>{c.label}</button>;
        }
        const active = mode === 'exploded' && focus === c.id;
        return (
          <button key={c.id} className={`chip${active ? ' active' : ''}`}
            onClick={() => explode(c.id as FloorFocus)}>{c.label}</button>
        );
      })}
    </nav>
  );
}
