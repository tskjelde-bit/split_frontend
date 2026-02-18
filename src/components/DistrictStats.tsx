
"use client";

import React from 'react';
import { DistrictInfo } from '@/types';
import { CITY_AVERAGE, getPreposisjon } from '@/constants';
import { TrendingUp, Clock, BarChart3, Coins } from 'lucide-react';

interface DistrictStatsProps {
  district: DistrictInfo | null;
  isExpanded: boolean;
  onOpenCalculator: () => void;
}

// Hjelpefunksjon for å sikre stor forbokstav
const capitalizeFirst = (str: string) => {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
};

// Fargekoding: grønn/gul basert på markedsdata
const GREEN = 'text-positive';
const YELLOW = 'text-warning';
const RED = 'text-negative';

const getTrendColor = (val: number) => val >= 2.5 ? GREEN : val >= 1.5 ? YELLOW : RED;
const getDaysColor = (val: number) => val <= 18 ? GREEN : val <= 24 ? YELLOW : RED;
const getSqmColor = (val: number) => val >= 110000 ? GREEN : val >= 75000 ? YELLOW : RED;
const getMedianColor = (val: number) => val >= 7000000 ? GREEN : val >= 4500000 ? YELLOW : RED;

// Logikk for generering av sammenligningstekster
const getComparisonTexts = (district: DistrictInfo) => {
  // Prisutvikling (prosentpoeng)
  const trendDiff = Number((district.priceChange - CITY_AVERAGE.priceTrend).toFixed(1));
  const trendAbsDiff = Math.abs(trendDiff);
  const trendPrep = trendDiff > 0.1 ? "over" : trendDiff < -0.1 ? "under" : "på linje med";
  const trendInterp = trendDiff > 0.1
    ? "Sterkere prisvekst enn byen for øvrig."
    : trendDiff < -0.1
    ? "Svakere prisvekst enn byen for øvrig."
    : "Normal prisvekst.";
  const trendDesktop = trendAbsDiff > 0.1
    ? `${trendDiff > 0 ? '+' : ''}${trendDiff} prosentpoeng ${trendPrep} Oslo-snittet (${CITY_AVERAGE.priceTrend}%). ${trendInterp}`
    : `På linje med Oslo-snittet (${CITY_AVERAGE.priceTrend}%). ${trendInterp}`;
  const trendMobile = trendAbsDiff > 0.1
    ? `${trendDiff > 0 ? '+' : ''}${trendDiff}pp ${trendPrep} snittet (${CITY_AVERAGE.priceTrend}%). ${trendDiff > 0.1 ? 'Sterkere vekst.' : 'Svakere vekst.'}`
    : `På linje med snittet (${CITY_AVERAGE.priceTrend}%). Normal vekst.`;

  // Liggetid (dager)
  const daysDiff = district.avgDaysOnMarket - CITY_AVERAGE.daysOnMarket;
  const daysAbsDiff = Math.abs(daysDiff);
  const daysPrep = daysDiff < -2 ? "raskere enn" : daysDiff > 2 ? "tregere enn" : "på nivå med";
  const daysInterp = daysDiff < -2
    ? "Svært likvid marked."
    : daysDiff > 2
    ? "Lavere etterspørsel."
    : "Normal etterspørsel.";
  const daysDesktop = daysAbsDiff > 2
    ? `${daysAbsDiff} dager ${daysPrep} Oslo-snittet (${CITY_AVERAGE.daysOnMarket} dager). ${daysInterp}`
    : `På nivå med Oslo-snittet (${CITY_AVERAGE.daysOnMarket} dager). ${daysInterp}`;
  const daysMobile = daysAbsDiff > 2
    ? `${daysAbsDiff} dager ${daysPrep} snittet (${CITY_AVERAGE.daysOnMarket}). ${daysDiff < -2 ? 'Likvid marked.' : 'Lavere etterspørsel.'}`
    : `På nivå med snittet (${CITY_AVERAGE.daysOnMarket}). Normal etterspørsel.`;

  // Medianpris (millioner)
  const medianDiff = Number(((district.medianPrice / 1000000) - CITY_AVERAGE.medianPrice).toFixed(1));
  const medianAbsDiff = Math.abs(medianDiff);
  const medianPrep = medianDiff > 0.2 ? "over" : medianDiff < -0.2 ? "under" : "på nivå med";
  const medianInterp = medianDiff > 1.0
    ? "Betydelig høyere prisnivå."
    : medianDiff > 0.2
    ? "Høyere prisnivå."
    : medianDiff < -0.2
    ? "Lavere prisnivå."
    : "Normalt prisnivå.";
  const medianDesktop = medianAbsDiff > 0.2
    ? `${medianAbsDiff} mill. kr ${medianPrep} Oslo-snittet (${CITY_AVERAGE.medianPrice} mill.). ${medianInterp}`
    : `På nivå med Oslo-snittet (${CITY_AVERAGE.medianPrice} mill.). ${medianInterp}`;
  const medianMobile = medianAbsDiff > 0.2
    ? `${medianAbsDiff}M ${medianPrep} snittet (${CITY_AVERAGE.medianPrice}M). ${medianDiff > 1.0 ? 'Betydelig høyere nivå.' : medianDiff > 0.2 ? 'Høyere nivå.' : 'Lavere nivå.'}`
    : `På nivå med snittet (${CITY_AVERAGE.medianPrice}M). Normalt nivå.`;

  // Kvadratmeterpris (kroner)
  const sqmDiff = district.pricePerSqm - CITY_AVERAGE.avgSqmPrice;
  const sqmAbsDiff = Math.abs(sqmDiff);
  const sqmPrep = sqmDiff > 1000 ? "over" : sqmDiff < -1000 ? "under" : "på nivå med";
  const sqmInterp = sqmDiff > 1000
    ? "Høyere prisnivå enn byen for øvrig."
    : sqmDiff < -1000
    ? "Rimeligere område."
    : "Normalt prisnivå.";
  const sqmDesktop = sqmAbsDiff > 1000
    ? `${(sqmAbsDiff / 1000).toFixed(0)} ${sqmAbsDiff >= 1000 ? '500' : '000'} kr/m² ${sqmPrep} Oslo-snittet (${(CITY_AVERAGE.avgSqmPrice / 1000).toFixed(0)} 500 kr/m²). ${sqmInterp}`
    : `På nivå med Oslo-snittet (${(CITY_AVERAGE.avgSqmPrice / 1000).toFixed(0)} 500 kr/m²). ${sqmInterp}`;
  const sqmMobile = sqmAbsDiff > 1000
    ? `${(sqmAbsDiff / 1000).toFixed(1)}k ${sqmPrep} snittet (${(CITY_AVERAGE.avgSqmPrice / 1000).toFixed(1)}k). ${sqmDiff > 1000 ? 'Høyere nivå.' : 'Rimeligere.'}`
    : `På nivå med snittet (${(CITY_AVERAGE.avgSqmPrice / 1000).toFixed(1)}k). Normalt nivå.`;

  return {
    trend: { desktop: trendDesktop, mobile: trendMobile },
    days: { desktop: daysDesktop, mobile: daysMobile },
    median: { desktop: medianDesktop, mobile: medianMobile },
    sqm: { desktop: sqmDesktop, mobile: sqmMobile }
  };
};

const DistrictStats: React.FC<DistrictStatsProps> = ({ district, isExpanded, onOpenCalculator }) => {
  const data = district || {
    id: 'oslo',
    name: 'Oslo',
    priceChange: CITY_AVERAGE.priceTrend,
    avgDaysOnMarket: CITY_AVERAGE.daysOnMarket,
    pricePerSqm: CITY_AVERAGE.avgSqmPrice,
    medianPrice: CITY_AVERAGE.medianPrice * 1000000,
    description: '',
    lat: 59.9139,
    lng: 10.7522
  };

  const compTexts = district ? getComparisonTexts(district) : null;
  const osloTextColor = 'text-tx-primary';

  if (!district) {
    return (
      <div className="h-full flex items-center animate-in fade-in duration-700 bg-white/50 dark:bg-[#0a0f1d]/50 md:bg-transparent md:dark:bg-transparent">
        <div className="max-w-[1050px] mx-auto px-4 md:px-10 w-full py-3.5 md:py-4">
          <div className="grid grid-cols-4 gap-2 md:gap-4 w-full">
            <StatItem label="Prisendring" value={`+${data.priceChange}%`} color={osloTextColor} labelColor={osloTextColor} center small />
            <StatItem
              label="Salgstid"
              value={<>{data.avgDaysOnMarket} <span className="stat-unit-full">dager</span><span className="stat-unit-short">D</span></>}
              color={osloTextColor}
              labelColor={osloTextColor}
              center
              small
            />
            <StatItem label="Medianpris" value={`${(data.medianPrice / 1000000).toFixed(1)}M`} color={osloTextColor} labelColor={osloTextColor} center small />
            <StatItem label="Per M2" value={`${(data.pricePerSqm / 1000).toFixed(0)} K`} color={osloTextColor} labelColor={osloTextColor} center small />
          </div>
        </div>
      </div>
    );
  }

  if (!isExpanded) {
    return (
      <div className="flex flex-col animate-in fade-in duration-300">
        <div className="flex items-center py-3.5 md:py-4 px-4 md:px-10 border-b border-br-subtle">
           <div className="grid grid-cols-4 gap-2 md:gap-4 w-full max-w-7xl mx-auto">
              <StatItem label="Prisendring" value={`+${data.priceChange}%`} color={getTrendColor(data.priceChange)} small center />
              <StatItem
                label="Salgstid"
                value={<>{data.avgDaysOnMarket} <span className="stat-unit-full">dager</span><span className="stat-unit-short">D</span></>}
                color={getDaysColor(data.avgDaysOnMarket)}
                small
                center
              />
              <StatItem label="Medianpris" value={`${(data.medianPrice / 1000000).toFixed(1)}M`} color={getMedianColor(data.medianPrice)} small center />
              <StatItem label="Per M2" value={`${(data.pricePerSqm / 1000).toFixed(0)} K`} color={getSqmColor(data.pricePerSqm)} small center />
           </div>
        </div>
        <button
          onClick={onOpenCalculator}
          className="w-full bg-accent hover:bg-accent-hover text-white font-bold py-4 transition-all active:scale-[0.99] shadow-[0_-10px_20px_rgba(37,99,235,0.2)] text-[0.8125rem] md:text-[1rem]"
        >
          Hva er boligen din {getPreposisjon(data.name)} {data.name} verdt?
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col animate-in slide-in-from-bottom-4 duration-500">
      <div className="pt-4 pb-1 px-3 md:px-0">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-1.5 md:gap-4">
          <StatBox
            title="Prisendring"
            mobileValue={`+${data.priceChange} %`}
            desktopValue={`+${data.priceChange} %`}
            colorClass={getTrendColor(data.priceChange)}
            icon={<TrendingUp />}
            desktopDesc={compTexts?.trend.desktop || "Gjennomsnittlig vekst."}
            mobileDesc={compTexts?.trend.mobile || "Normal vekst."}
          />

          <StatBox
            title="Salgstid"
            mobileValue={<>{data.avgDaysOnMarket} <span className="stat-unit-full">dager</span><span className="stat-unit-short">D</span></>}
            desktopValue={<>{data.avgDaysOnMarket} dager</>}
            colorClass={getDaysColor(data.avgDaysOnMarket)}
            icon={<Clock />}
            desktopDesc={compTexts?.days.desktop || "Normal etterspørsel."}
            mobileDesc={compTexts?.days.mobile || "Normal etterspørsel."}
          />

          <StatBox
            title="Medianpris"
            mobileValue={`${data.medianPrice.toLocaleString('nb-NO')} kr`}
            desktopValue={`${(data.medianPrice / 1000000).toFixed(1)} M`}
            colorClass={getMedianColor(data.medianPrice)}
            icon={<BarChart3 />}
            desktopDesc={compTexts?.median.desktop || "Normalt prisnivå."}
            mobileDesc={compTexts?.median.mobile || "Normalt nivå."}
          />

          <StatBox
            title="Per m2"
            mobileValue={`${data.pricePerSqm.toLocaleString('nb-NO')} kr`}
            desktopValue={`${(data.pricePerSqm / 1000).toFixed(0)} K`}
            colorClass={getSqmColor(data.pricePerSqm)}
            icon={<Coins />}
            desktopDesc={compTexts?.sqm.desktop || "Normalt prisnivå."}
            mobileDesc={compTexts?.sqm.mobile || "Normalt nivå."}
          />
        </div>
      </div>

      <button
        onClick={onOpenCalculator}
        className="w-full bg-accent hover:bg-accent-hover text-white font-bold py-4 md:py-4 transition-all active:scale-[0.99] shadow-[0_-10px_20px_rgba(37,99,235,0.2)] text-[0.8125rem] md:text-[1rem]"
      >
        Hva er boligen din på {data.name} verdt?
      </button>
    </div>
  );
};

const StatItem = ({ label, value, color, small, center, labelColor = "text-tx-dim" }: { label: string, value: React.ReactNode, color: string, small?: boolean, center?: boolean, labelColor?: string }) => (
  <div className={center ? 'text-center' : 'text-left'}>
    <div className={`${color} font-bold ${small ? 'text-[clamp(1.25rem,4vw,2rem)]' : 'text-2xl md:text-5xl'} tracking-[-0.03em] mb-0.5 md:mb-1 transition-colors duration-500`}>{value}</div>
    <div className={`${labelColor} text-[0.625rem] md:text-[0.6875rem] font-semibold tracking-[0.08em] leading-tight uppercase`}>{label}</div>
  </div>
);

const StatBox = ({ title, mobileValue, desktopValue, colorClass, icon, desktopDesc, mobileDesc }: { title: string, mobileValue?: React.ReactNode, desktopValue?: React.ReactNode, colorClass: string, icon: React.ReactElement, desktopDesc: string, mobileDesc: string }) => (
  <div className="bg-surface rounded-[1rem] p-2 md:p-4 border border-br-subtle hover:border-accent/20 transition-all group">
    <div className="flex items-start justify-between mb-0 md:mb-3">
      {mobileValue && desktopValue ? (
        <>
          <div className={`${colorClass} font-bold text-[clamp(1.25rem,4vw,2rem)] tracking-[-0.03em] transition-colors duration-500 md:hidden`}>{mobileValue}</div>
          <div className={`${colorClass} font-bold text-[2rem] tracking-[-0.03em] transition-colors duration-500 hidden md:block`}>{desktopValue}</div>
        </>
      ) : (
        <div className={`${colorClass} font-bold text-[clamp(1.25rem,4vw,2rem)] md:text-[2rem] tracking-[-0.03em] transition-colors duration-500`}>{mobileValue || desktopValue}</div>
      )}
      <div className={`${colorClass} opacity-70`}>
        {React.cloneElement(icon as React.ReactElement<any>, { size: 14, strokeWidth: 2.5 })}
      </div>
    </div>
    <div className="space-y-0 md:space-y-1">
      <h4 className="text-[0.625rem] md:text-[0.6875rem] font-semibold text-tx-dim tracking-[0.08em] uppercase">{title}</h4>
      <p className="hidden md:block text-[0.8125rem] text-tx-muted leading-snug font-normal opacity-90 line-clamp-2">
        {desktopDesc}
      </p>
      <p className="block md:hidden text-[0.75rem] text-tx-muted leading-snug font-normal line-clamp-2">
        {mobileDesc}
      </p>
    </div>
  </div>
);

export default DistrictStats;
