export type FloorId = 'U' | '1' | '2' | '3';
export type UnitStatus = 'ledig' | 'reservert' | 'solgt';

export interface Materials {
  pussRosa: string; pussHvit: string; takSort: string;
  karmSort: string; glassMork: string; hekkGronn: string;
}

export interface UnitGeo { id: string; unit: string; poly: [number, number][]; }
export interface FloorGeo {
  id: FloorId; label: string; elevation: number; height: number;
  facade?: string;
  outline: [number, number][]; units: UnitGeo[]; common: [number, number][][];
}
export interface EnvelopeGeo { poly: [number, number][]; wallThickness: number; envelopeDoc?: string; }

export interface RoofWindow { width: number; sill: number; height: number; }
export interface GableSpec { edge: number; t: number; width: number; projection: number; rise: number; window?: RoofWindow; }
export interface ChimneySpec { x: number; y: number; w: number; d: number; above: number; }
export interface SkylightSpec { t: number; up: number; width: number; height: number; }
export interface FrontispieceSpec {
  edge: number; t: number; width: number; projection: number; depth: number;
  gableBase: number; apex: number; trim: number;
  window?: { width: number; sill: number; height: number; peak: number };
}
export interface RoofGeo {
  elevation: number; type: 'saltak';
  rect: [number, number][]; ridgeAxis: 'x' | 'y'; ridgeOffset: number; rise: number;
  eaveOverhang: number;
  recess?: { poly: [number, number][]; rise: number; recessDoc?: string };
  ark?: GableSpec; dormers?: GableSpec[]; chimneys?: ChimneySpec[];
  skylights?: SkylightSpec[];
  frontispiece?: FrontispieceSpec;
  heis?: unknown;
  // documentation-only fields carried through from the data file
  ridgeOffsetDoc?: string;
  [key: string]: unknown;
}
export interface WindowGeo { floor: FloorId; edge: number; t: number; width: number; sill: number; height: number; kind?: 'window' | 'blind'; }
export interface EntranceSpec { edge: number; t: number; width: number; height: number; overlys: boolean; steps: number; doc?: string; }
export interface BalconySpec { edge: number; t: number; floor: FloorId; width: number; depth: number; doc?: string; }
export interface SiteGeo {
  groundMargin: { sw: number; se: number; ne: number; nw: number };
  groundY: { nw: number; se: number };
  hedgeEdges: number[]; fenceEdges: number[]; doc?: string;
}
export interface BuildingGeo {
  scale: number; slabThickness: number; envelope: EnvelopeGeo; floors: FloorGeo[]; roof: RoofGeo; windows: WindowGeo[];
  materials: Materials;
  entrances: EntranceSpec[];
  balconies: BalconySpec[];
  site?: SiteGeo;
}

export interface Rom { name: string; area: number; }
export interface UnitInfo {
  id: string; navn: string; type: string; etasje: number; duplex: boolean;
  braI: number; braU: number | null; braArkitekt: number; hemsCa: number | null;
  rom: Rom[]; pris: number; kvmPris: number; kvmPrisU: number | null;
}

export interface SiteConfig {
  tittel: string; undertittel: string; ingress: string;
  kontakt: { navn: string; tittel: string; telefon: string; epost: string };
}

export interface AppData { geo: BuildingGeo; units: Record<string, UnitInfo>; site: SiteConfig; }
