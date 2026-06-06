import { useVelger } from '../state/store';

/** Maps ?qa= URL param to store state, for deterministic QA screenshots. */
export function applyQaParam(param: string | null): void {
  if (!param) return;
  const s = useVelger.getState();
  if (param === 'orbit') s.setMode('orbit');
  else if (param === 'exploded') s.explode('all');
  else if (param === 'floorU1') s.explode('U1');
  else if (param === 'floor2') s.explode('2');
  else if (param === 'floor3') s.explode('3');
  else if (param.startsWith('unit-')) s.select(param.slice(5));
}
