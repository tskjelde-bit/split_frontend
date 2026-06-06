import type { AppData, UnitStatus } from './types';

const BASE = '/data/dybwads-gate-8';

export async function loadAppData(): Promise<AppData> {
  const [geo, units, site] = await Promise.all([
    fetch(`${BASE}/geometri.json`).then(r => r.json()),
    fetch(`${BASE}/units.json`).then(r => r.json()),
    fetch(`${BASE}/site.json`).then(r => r.json()),
  ]);
  return { geo, units, site };
}

export function planSvgUrl(unitId: string): string { return `${BASE}/plan/${unitId}-plan.svg`; }
export function hemsSvgUrl(unitId: string): string { return `${BASE}/plan/${unitId}-hems.svg`; }
export function pdfUrl(unitId: string): string { return `${BASE}/pdf/${unitId}.pdf`; }

export async function fetchStatus(): Promise<Record<string, UnitStatus>> {
  const r = await fetch('/api/status');
  if (!r.ok) throw new Error(`status ${r.status}`);
  return r.json();
}
