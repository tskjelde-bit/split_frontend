import { create } from 'zustand';
import type { UnitStatus } from '../lib/types';

export type Mode = 'landing' | 'orbit' | 'exploded';
export type FloorFocus = 'all' | 'U1' | '2' | '3';

/** Which focus a click on a floor plate's shell should explode into.
 *  Basement follows floor 1 (duplex units span both). */
export function focusForFloor(floorId: string): FloorFocus {
  if (floorId === 'U' || floorId === '1') return 'U1';
  if (floorId === '2' || floorId === '3') return floorId;
  return 'all';
}

interface VelgerState {
  mode: Mode;
  focus: FloorFocus;
  hovered: string | null;
  selected: string | null;
  status: Record<string, UnitStatus>;
  setMode: (m: Mode) => void;
  explode: (f: FloorFocus) => void;
  assemble: () => void;
  setHovered: (id: string | null) => void;
  select: (id: string | null) => void;
  setStatus: (s: Record<string, UnitStatus>) => void;
  reset: () => void;
}

const initial = {
  mode: 'landing' as Mode,
  focus: 'all' as FloorFocus,
  hovered: null,
  selected: null,
  status: {},
};

export const useVelger = create<VelgerState>((set, get) => ({
  ...initial,
  setMode: (mode) => set({ mode }),
  explode: (focus) => set({ mode: 'exploded', focus }),
  assemble: () => set({ mode: 'orbit', focus: 'all', selected: null }),
  setHovered: (hovered) => set({ hovered }),
  select: (selected) => {
    if (selected && get().mode !== 'exploded') set({ mode: 'exploded' });
    set({ selected });
  },
  setStatus: (status) => set({ status }),
  reset: () => set(initial),
}));
