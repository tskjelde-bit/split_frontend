
"use client";

import React from 'react';
import { DistrictData } from '@/types';

interface MapProps {
  districts: DistrictData[];
  selectedDistrict?: string | null;
  onSelect?: (district: DistrictData) => void;
  onDistrictClick?: (districtId: string) => void;
}

const MOCK_DISTRICTS = [
  { id: 'vestre-aker', name: 'Vestre Aker' },
  { id: 'nordre-aker', name: 'Nordre Aker' },
  { id: 'bjerke', name: 'Bjerke' },
  { id: 'grorud', name: 'Grorud' },
  { id: 'stovner', name: 'Stovner' },
  { id: 'ullern', name: 'Ullern' },
  { id: 'frogner', name: 'Frogner' },
  { id: 'st-hanshaugen', name: 'St. Hanshaugen' },
  { id: 'sagene', name: 'Sagene' },
  { id: 'gruenerloekka', name: 'Grünerløkka' },
  { id: 'gamle-oslo', name: 'Gamle Oslo' },
  { id: 'alna', name: 'Alna' },
  { id: 'oestensjoe', name: 'Østensjø' },
  { id: 'nordstrand', name: 'Nordstrand' },
  { id: 'soendre-nordstrand', name: 'Søndre Nordstrand' },
];

const getSlugId = (name: string) => {
  if (name === 'Grünerløkka') return 'grunerlokka';
  return name.toLowerCase()
    .replace(/ /g, '-')
    .replace(/æ/g, 'ae')
    .replace(/ø/g, 'oe')
    .replace(/å/g, 'aa')
    .replace(/ü/g, 'u')
    .replace(/\./g, '');
};

const getDistrictColor = (id: string, districts: DistrictData[], isSelected: boolean) => {
  if (isSelected) return '#2563eb'; // Deep blue for selected
  
  const district = districts.find(d => d.id === id);
  if (!district) return '#bfdbfe';

  const price = district.avgSqmPrice;
  // Mobilvennlige farger for å etterligne mock-up's blå grid
  if (price > 110000) return '#60a5fa'; 
  if (price > 90000) return '#93c5fd';  
  if (price > 75000) return '#bfdbfe';  
  return '#dbeafe'; 
};

const Map: React.FC<MapProps> = ({ districts, selectedDistrict, onSelect, onDistrictClick }) => {
  const gridWidth = 1000;
  const gridHeight = 700; 
  const cols = 5;
  const rows = 3;
  const padding = 12; 
  
  const cellWidth = (gridWidth - (cols + 1) * padding) / cols;
  const cellHeight = (gridHeight - (rows + 1) * padding) / rows;

  const handleClick = (id: string) => {
    if (onDistrictClick) {
      onDistrictClick(id);
    }
    const foundDistrict = districts.find(d => d.id === id);
    if (foundDistrict && onSelect) {
      onSelect(foundDistrict);
    }
  };

  return (
    <div className="w-full h-full md:bg-[#f1f5f9] bg-white relative overflow-hidden flex items-center justify-center p-0 md:p-8">
      {/* Bakgrunnsmønster kun for desktop */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none hidden md:block" 
           style={{ backgroundImage: 'radial-gradient(#1e293b 1px, transparent 1px)', backgroundSize: '24px 24px' }} />

      <svg 
        viewBox={`0 0 ${gridWidth} ${gridHeight}`} 
        className="w-full h-full max-w-5xl transition-all duration-700 ease-in-out"
      >
        <defs>
          <filter id="tileShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.05" />
          </filter>
        </defs>

        {MOCK_DISTRICTS.map((district, index) => {
          const slugId = getSlugId(district.name);
          const col = index % cols;
          const row = Math.floor(index / cols);
          const x = padding + col * (cellWidth + padding);
          const y = padding + row * (cellHeight + padding);
          const isSelected = selectedDistrict === slugId;
          const fillColor = getDistrictColor(slugId, districts, isSelected);

          return (
            <g 
              key={slugId} 
              onClick={() => handleClick(slugId)}
              className="cursor-pointer group"
            >
              {/* Tile Background */}
              <rect
                x={x}
                y={y}
                width={cellWidth}
                height={cellHeight}
                rx={4} 
                fill={fillColor}
                stroke={isSelected ? "#2563eb" : "#ffffff"}
                strokeWidth={isSelected ? 4 : 1}
                filter={isSelected ? "none" : "url(#tileShadow)"}
                className="transition-all duration-300 ease-out group-hover:brightness-95"
              />
              
              {/* Label Text - Sentrert mørk tekst */}
              <text
                x={x + cellWidth / 2}
                y={y + cellHeight / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={isSelected ? '#ffffff' : '#1e293b'}
                className={`text-[8px] md:text-[10px] font-black uppercase tracking-tight select-none pointer-events-none transition-colors duration-300 ${isSelected ? '' : 'opacity-40'}`}
                style={{ fontSize: '14px' }}
              >
                {district.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default Map;
