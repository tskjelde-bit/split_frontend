
import { DistrictData, DistrictInfo, BoligType, Standard } from './types';

const PÅ_BYDELER = ['Grünerløkka', 'Frogner', 'Sagene', 'St. Hanshaugen'];

export const getPreposisjon = (name: string | undefined): string => {
  if (!name) return 'i';
  return PÅ_BYDELER.includes(name) ? 'på' : 'i';
};

export const BOLIGTYPE_FACTORS: Record<BoligType, number> = {
  [BoligType.LEILIGHET]: 1.00,
  [BoligType.REKKEHUS]: 0.92,
  [BoligType.TOMANNSBOLIG]: 0.88,
  [BoligType.ENEBOLIG]: 0.85
};

export const STANDARD_FACTORS: Record<Standard, number> = {
  [Standard.STANDARD]: 0.00,
  [Standard.OPPGRADERT]: 0.08,
  [Standard.RENOVERINGSBEHOV]: -0.10
};

// Legacy district data for SVG map (deprecated)
export const DISTRICTS: DistrictData[] = [
  {
    id: 'vestre-aker',
    name: 'Vestre Aker',
    priceTrend: 3.2,
    avgSqmPrice: 115000,
    medianPrice: 12.5,
    daysOnMarket: 18,
    description: 'Sterkere prisvekst enn byen for øvrig. Høyt prisnivå.',
    path: ''
  },
  {
    id: 'nordre-aker',
    name: 'Nordre Aker',
    priceTrend: 2.8,
    avgSqmPrice: 104000,
    medianPrice: 9.8,
    daysOnMarket: 21,
    description: 'Stabil vekst i et populært boligområde for barnefamilier.',
    path: ''
  },
  {
    id: 'bjerke',
    name: 'Bjerke',
    priceTrend: 2.2,
    avgSqmPrice: 72000,
    medianPrice: 5.9,
    daysOnMarket: 24,
    description: 'Område i vekst med mange nye boligprosjekter.',
    path: ''
  },
  {
    id: 'grorud',
    name: 'Grorud',
    priceTrend: 1.8,
    avgSqmPrice: 65000,
    medianPrice: 4.2,
    daysOnMarket: 25,
    description: 'Bydel med god tilgang på rimeligere familieboliger.',
    path: ''
  },
  {
    id: 'stovner',
    name: 'Stovner',
    priceTrend: 1.4,
    avgSqmPrice: 62000,
    medianPrice: 3.6,
    daysOnMarket: 30,
    description: 'Oslos rimeligste bydel med mange grønne lunger.',
    path: ''
  },
  {
    id: 'ullern',
    name: 'Ullern',
    priceTrend: 3.5,
    avgSqmPrice: 108000,
    medianPrice: 11.2,
    daysOnMarket: 19,
    description: 'Attraktivt område med nærhet til både sjø og skog.',
    path: ''
  },
  {
    id: 'frogner',
    name: 'Frogner',
    priceTrend: 4.1,
    avgSqmPrice: 128000,
    medianPrice: 8.5,
    daysOnMarket: 22,
    description: 'Høyest kvadratmeterpris i Oslo. Vedvarende høy etterspørsel.',
    path: ''
  },
  {
    id: 'st-hanshaugen',
    name: 'St. Hanshaugen',
    priceTrend: 2.4,
    avgSqmPrice: 98000,
    medianPrice: 6.2,
    daysOnMarket: 17,
    description: 'Sentralt og urbant område med mange mindre leiligheter.',
    path: ''
  },
  {
    id: 'sagene',
    name: 'Sagene',
    priceTrend: 2.5,
    avgSqmPrice: 95000,
    medianPrice: 5.8,
    daysOnMarket: 18,
    description: 'Populært og sjarmerende område langs Akerselva.',
    path: ''
  },
  {
    id: 'grunerlokka',
    name: 'Grünerløkka',
    priceTrend: 2.1,
    avgSqmPrice: 92000,
    medianPrice: 5.4,
    daysOnMarket: 16,
    description: 'Høy likviditet og mange salg. Populært blant unge voksne.',
    path: ''
  },
  {
    id: 'gamle-oslo',
    name: 'Gamle Oslo',
    priceTrend: 3.8,
    avgSqmPrice: 88000,
    medianPrice: 5.8,
    daysOnMarket: 20,
    description: 'Størst utvikling i Bjørvika og Sørenga drar opp snittet.',
    path: ''
  },
  {
    id: 'alna',
    name: 'Alna',
    priceTrend: 1.5,
    avgSqmPrice: 62000,
    medianPrice: 4.5,
    daysOnMarket: 28,
    description: 'Moderat prisvekst. Godt tilbud av større familieboliger.',
    path: ''
  },
  {
    id: 'oestensjoe',
    name: 'Østensjø',
    priceTrend: 2.0,
    avgSqmPrice: 78000,
    medianPrice: 5.2,
    daysOnMarket: 22,
    description: 'Veletablert boligområde med mange rekkehus og eneboliger.',
    path: ''
  },
  {
    id: 'nordstrand',
    name: 'Nordstrand',
    priceTrend: 2.9,
    avgSqmPrice: 88000,
    medianPrice: 7.5,
    daysOnMarket: 20,
    description: 'Kjent for flott utsikt og attraktive eneboliger.',
    path: ''
  },
  {
    id: 'soendre-nordstrand',
    name: 'Søndre Nordstrand',
    priceTrend: 1.2,
    avgSqmPrice: 58000,
    medianPrice: 3.8,
    daysOnMarket: 32,
    description: 'Nyere bydel med god plass og rimelige priser.',
    path: ''
  }
];

// MapComponent district data (from meglerinnsikt_v3 - matches GeoJSON)
export const OSLO_DISTRICTS: DistrictInfo[] = [
  {
    id: 'oslo',
    name: 'Oslo (Totalt)',
    priceChange: 2.4,
    avgDaysOnMarket: 19,
    pricePerSqm: 94500,
    medianPrice: 5850000,
    description: 'Boligmarkedet i Oslo viser stabil vekst over hele linjen, med fortsatt høy etterspørsel i sentrale strøk.',
    lat: 59.9139,
    lng: 10.7522
  },
  {
    id: 'gamle-oslo',
    name: 'Gamle Oslo',
    priceChange: 2.6,
    avgDaysOnMarket: 17,
    pricePerSqm: 102000,
    medianPrice: 5200000,
    description: 'Bydelen preges av massiv utvikling og stor tiltrekningskraft for unge voksne.',
    lat: 59.9077,
    lng: 10.7788
  },
  {
    id: 'grunerlokka',
    name: 'Grünerløkka',
    priceChange: 1.8,
    avgDaysOnMarket: 14,
    pricePerSqm: 105000,
    medianPrice: 4950000,
    description: 'Høy omløpshastighet preger det urbane markedet her. Populært for førstegangskjøpere.',
    lat: 59.9242,
    lng: 10.7584
  },
  {
    id: 'sagene',
    name: 'Sagene',
    priceChange: 2.1,
    avgDaysOnMarket: 16,
    pricePerSqm: 98000,
    medianPrice: 4800000,
    description: 'Stabilt marked med sjarmerende bebyggelse langs Akerselva.',
    lat: 59.9378,
    lng: 10.7584
  },
  {
    id: 'st-hanshaugen',
    name: 'St. Hanshaugen',
    priceChange: 2.9,
    avgDaysOnMarket: 18,
    pricePerSqm: 112000,
    medianPrice: 6100000,
    description: 'Sentral beliggenhet med mange klassiske bygårder og parker.',
    lat: 59.9268,
    lng: 10.7401
  },
  {
    id: 'sentrum',
    name: 'Sentrum',
    priceChange: 3.5,
    avgDaysOnMarket: 15,
    pricePerSqm: 135000,
    medianPrice: 5500000,
    description: 'Oslos sentrale kjerneområde med høy etterspørsel og kompakte leiligheter.',
    lat: 59.9127,
    lng: 10.7461
  },
  {
    id: 'frogner',
    name: 'Frogner',
    priceChange: 3.2,
    avgDaysOnMarket: 22,
    pricePerSqm: 145000,
    medianPrice: 8900000,
    description: 'Landets mest eksklusive bydel med stabilt høye kvadratmeterpriser.',
    lat: 59.9171,
    lng: 10.7061
  },
  {
    id: 'ullern',
    name: 'Ullern',
    priceChange: 2.5,
    avgDaysOnMarket: 25,
    pricePerSqm: 125000,
    medianPrice: 9500000,
    description: 'Attraktiv bydel i vest med mange eneboliger og nyere leilighetsprosjekter.',
    lat: 59.9248,
    lng: 10.6521
  },
  {
    id: 'vestre-aker',
    name: 'Vestre Aker',
    priceChange: 2.2,
    avgDaysOnMarket: 28,
    pricePerSqm: 118000,
    medianPrice: 11200000,
    description: 'Preget av villabebyggelse og nærhet til Marka. Stabilt marked.',
    lat: 59.9547,
    lng: 10.6725
  },
  {
    id: 'nordre-aker',
    name: 'Nordre Aker',
    priceChange: 2.8,
    avgDaysOnMarket: 20,
    pricePerSqm: 108000,
    medianPrice: 8200000,
    description: 'Svært populært område for barnefamilier med gode skoler og grøntarealer.',
    lat: 59.9622,
    lng: 10.7538
  },
  {
    id: 'bjerke',
    name: 'Bjerke',
    priceChange: 1.9,
    avgDaysOnMarket: 22,
    pricePerSqm: 82000,
    medianPrice: 4600000,
    description: 'Voksende bydel med mye nybygging og god kommunikasjon.',
    lat: 59.9404,
    lng: 10.8172
  },
  {
    id: 'grorud',
    name: 'Grorud',
    priceChange: 1.5,
    avgDaysOnMarket: 26,
    pricePerSqm: 68000,
    medianPrice: 3800000,
    description: 'Rimeligere inngangsbillett til markedet med gode turmuligheter.',
    lat: 59.9589,
    lng: 10.8845
  },
  {
    id: 'stovner',
    name: 'Stovner',
    priceChange: 1.4,
    avgDaysOnMarket: 30,
    pricePerSqm: 62000,
    medianPrice: 3650000,
    description: 'Mye for pengene og barnevennlige omgivelser i Groruddalen.',
    lat: 59.9733,
    lng: 10.9239
  },
  {
    id: 'alna',
    name: 'Alna',
    priceChange: 1.6,
    avgDaysOnMarket: 24,
    pricePerSqm: 72000,
    medianPrice: 4100000,
    description: 'Bydel med variert boligmasse og gode handelsfasiliteter.',
    lat: 59.9324,
    lng: 10.8524
  },
  {
    id: 'ostensjo',
    name: 'Østensjø',
    priceChange: 2.3,
    avgDaysOnMarket: 19,
    pricePerSqm: 88000,
    medianPrice: 5300000,
    description: 'Etablert bydel med sterkt lokalmiljø og nærhet til Østensjøvannet.',
    lat: 59.8894,
    lng: 10.8306
  },
  {
    id: 'nordstrand',
    name: 'Nordstrand',
    priceChange: 3.0,
    avgDaysOnMarket: 21,
    pricePerSqm: 104000,
    medianPrice: 8500000,
    description: 'Attraktiv bydel med flott utsikt og nærhet til fjorden.',
    lat: 59.8624,
    lng: 10.7958
  },
  {
    id: 'sondre-nordstrand',
    name: 'Søndre Nordstrand',
    priceChange: 1.7,
    avgDaysOnMarket: 29,
    pricePerSqm: 58000,
    medianPrice: 3400000,
    description: 'Oslos sørligste bydel med mange rekkehus og grønne lunger.',
    lat: 59.8335,
    lng: 10.8256
  }
];

export const CITY_AVERAGE = {
  priceTrend: 2.4,
  daysOnMarket: 19,
  medianPrice: 5.8,
  avgSqmPrice: 94500
};
