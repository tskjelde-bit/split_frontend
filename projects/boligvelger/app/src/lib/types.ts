export type FloorId = 'U' | '1' | '2' | '3';
export type UnitStatus = 'ledig' | 'reservert' | 'solgt';

export interface UnitGeo { id: string; unit: string; poly: [number, number][]; }
export interface FloorGeo {
  id: FloorId; label: string; elevation: number; height: number;
  outline: [number, number][]; units: UnitGeo[]; common: [number, number][][];
}
export interface RoofGeo { elevation: number; volumes: { poly: [number, number][]; height: number }[]; }
export interface WindowGeo { floor: FloorId; edge: number; t: number; width: number; sill: number; height: number; }
export interface BuildingGeo {
  scale: number; slabThickness: number; floors: FloorGeo[]; roof: RoofGeo; windows: WindowGeo[];
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
