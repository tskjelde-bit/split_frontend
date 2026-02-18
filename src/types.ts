
export enum BoligType {
  LEILIGHET = 'Leilighet',
  REKKEHUS = 'Rekkehus',
  TOMANNSBOLIG = 'Tomannsbolig',
  ENEBOLIG = 'Enebolig'
}

export enum Standard {
  RENOVERINGSBEHOV = 'Renoveringsbehov',
  STANDARD = 'Standard',
  OPPGRADERT = 'Oppgradert'
}

// Legacy type for SVG map (deprecated)
export interface DistrictData {
  id: string;
  name: string;
  priceTrend: number; // Percentage
  avgSqmPrice: number;
  medianPrice: number; // In millions
  daysOnMarket: number;
  description: string;
  path: string; // SVG path data
}

// MapComponent type (from meglerinnsikt_v3)
export interface DistrictInfo {
  id: string;
  name: string;
  priceChange: number;
  avgDaysOnMarket: number;
  pricePerSqm: number;
  medianPrice: number;
  description: string;
  lat: number;
  lng: number;
}

// Property type for MapComponent
export interface Property {
  id: string;
  // Add other property fields as needed
}

export interface CalculatorState {
  districtId: string;
  type: BoligType;
  area: number;
  standard: Standard;
}
