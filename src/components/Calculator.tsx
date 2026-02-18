
"use client";

import React, { useState } from 'react';
import { DistrictInfo, BoligType, Standard } from '@/types';
import { OSLO_DISTRICTS, BOLIGTYPE_FACTORS, STANDARD_FACTORS, getPreposisjon } from '@/constants';
import { X, Loader2, Sparkles, Home, Building2, Warehouse, DoorOpen, ArrowRight, TrendingUp, ChevronLeft, ChevronUp, ChevronDown } from 'lucide-react';

interface CalculatorProps {
  district: DistrictInfo;
  onDistrictChange: (id: string) => void;
  onClose: () => void;
}

const Calculator: React.FC<CalculatorProps> = ({ district, onDistrictChange, onClose }) => {
  const [type, setType] = useState<BoligType>(BoligType.LEILIGHET);
  const [area, setArea] = useState<number>(85);
  const [standard, setStandard] = useState<Standard>(Standard.STANDARD);
  const [isCalculating, setIsCalculating] = useState(false);
  const [estimatedValue, setEstimatedValue] = useState<number | null>(null);

  const getIconForType = (t: BoligType) => {
    switch (t) {
      case BoligType.LEILIGHET: return <Building2 className="w-5 h-5" />;
      case BoligType.REKKEHUS: return <Warehouse className="w-5 h-5" />;
      case BoligType.TOMANNSBOLIG: return <DoorOpen className="w-5 h-5" />;
      case BoligType.ENEBOLIG: return <Home className="w-5 h-5" />;
    }
  };

  const handleCalculate = () => {
    setIsCalculating(true);
    setEstimatedValue(null);

    setTimeout(() => {
      const boligtypeFaktor = BOLIGTYPE_FACTORS[type];
      const effektivPrisPerKvm = district.pricePerSqm * boligtypeFaktor;
      const basisverdi = area * effektivPrisPerKvm;
      const standardFaktor = STANDARD_FACTORS[standard];
      const finalValue = basisverdi * (1 + standardFaktor);
      setEstimatedValue(Math.round(finalValue));
      setIsCalculating(false);
    }, 1000);
  };

  const handleReset = () => {
    setEstimatedValue(null);
  };

  const showResultOnMobile = estimatedValue !== null;

  return (
    <div className="flex flex-col h-full w-full bg-base animate-in fade-in duration-300 overflow-hidden md:relative md:bg-transparent md:max-w-6xl md:mx-auto md:px-10 md:py-10">

      {/* Header for kalkulator */}
      <div className="flex items-start justify-between px-4 pt-4 pb-2 md:p-0 md:mb-8 border-b border-br-subtle md:border-none md:bg-transparent shrink-0">
        <div className="flex flex-col text-left">
          <h1 className="text-[1.75rem] md:text-[2.25rem] font-bold text-tx-primary tracking-[-0.02em] leading-[1.15] mb-0.5 md:mb-1">
            Verdikalkulator
          </h1>
          <p className="text-tx-muted font-normal text-[0.8125rem] md:text-[0.9375rem] opacity-90">
            Boligestimat {getPreposisjon(district.name)} <span className="text-accent">{district.name}</span>
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1 md:p-2 text-tx-dim hover:text-tx-primary transition-all group shrink-0"
        >
          <X className="w-6 h-6 group-hover:rotate-90 transition-transform duration-300" />
        </button>
      </div>

      <div className="flex-1 overflow-hidden md:overflow-hidden relative">
        <div className="h-full w-full grid grid-cols-1 lg:grid-cols-12 gap-0 md:gap-8 p-0 md:p-0">

          {/* VENSTRE SIDE / FORM */}
          <div className={`lg:col-span-7 md:bg-surface md:rounded-[2rem] md:border border-br-subtle p-4 md:p-8 flex flex-col h-full ${showResultOnMobile ? 'hidden lg:flex' : 'flex'}`}>
            <div className="flex-1 space-y-4 md:space-y-6 flex flex-col justify-start md:justify-center">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-[0.6875rem] font-semibold text-tx-dim uppercase tracking-[0.08em] ml-1">Bydel</label>
                  <div className="relative">
                    <select
                      value={district.id}
                      onChange={(e) => onDistrictChange(e.target.value)}
                      className="w-full bg-base border border-br-default rounded-xl px-3 py-2.5 text-accent font-bold appearance-none text-sm focus:ring-1 focus:ring-accent outline-none"
                    >
                      {OSLO_DISTRICTS.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-tx-dim">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[0.6875rem] font-semibold text-tx-dim uppercase tracking-[0.08em] ml-1">Areal</label>
                  <div className="flex items-center justify-between bg-base border border-br-default rounded-xl px-3 py-2.5 focus-within:ring-1 focus-within:ring-accent group">
                    <div className="flex items-center">
                      <input
                        type="number"
                        value={area}
                        onChange={(e) => setArea(Number(e.target.value))}
                        className="bg-transparent text-accent font-bold text-sm md:text-base outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none w-[2ch]"
                        style={{ width: `${area.toString().length}ch` }}
                      />
                      <span className="text-accent font-bold text-sm md:text-base ml-1">m2</span>
                    </div>
                    <div className="flex flex-col -space-y-1 ml-2">
                      <button onClick={() => setArea(prev => prev + 1)} className="text-tx-dim hover:text-accent transition-colors">
                        <ChevronUp className="w-3 h-3" />
                      </button>
                      <button onClick={() => setArea(prev => Math.max(0, prev - 1))} className="text-tx-dim hover:text-accent transition-colors">
                        <ChevronDown className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[0.6875rem] font-semibold text-tx-dim uppercase tracking-[0.08em] ml-1">Boligtype</label>
                <div className="grid grid-cols-4 gap-2">
                  {Object.values(BoligType).map((t) => (
                    <button
                      key={t}
                      onClick={() => setType(t)}
                      className={`flex flex-col items-center justify-center p-2 rounded-xl border transition-all ${
                        type === t ? 'bg-accent-subtle border-accent text-accent shadow-lg shadow-accent/10' : 'bg-base border-br-default text-tx-dim'
                      }`}
                    >
                      {getIconForType(t)}
                      <span className="text-[0.625rem] font-semibold uppercase tracking-[0.06em] mt-1">{t.slice(0, 3)}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[0.6875rem] font-semibold text-tx-dim uppercase tracking-[0.08em] ml-1">Standard</label>
                <div className="grid grid-cols-3 gap-1 bg-base p-1 rounded-xl border border-br-default">
                  {Object.values(Standard).map((s) => (
                    <button
                      key={s}
                      onClick={() => setStandard(s)}
                      className={`py-2 rounded-lg text-[0.625rem] font-semibold uppercase tracking-[0.06em] transition-all ${
                        standard === s ? 'bg-elevated text-accent' : 'text-tx-dim'
                      }`}
                    >
                      {s === Standard.RENOVERINGSBEHOV ? 'Behov' : s}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={handleCalculate}
              disabled={isCalculating}
              className="w-full bg-accent hover:bg-accent-hover disabled:bg-elevated text-white font-semibold py-4 rounded-xl mt-6 flex items-center justify-center gap-3 uppercase tracking-[0.08em] text-[0.6875rem] transition-all active:scale-95 shadow-xl shadow-accent/20"
            >
              {isCalculating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {isCalculating ? 'Analyserer...' : 'Beregn verdi'}
            </button>
          </div>

          {/* HOYRE SIDE / RESULTAT */}
          <div className={`lg:col-span-5 md:bg-surface md:rounded-[2rem] md:border border-br-default p-4 md:p-8 flex flex-col h-full relative transition-all duration-500 ${showResultOnMobile ? 'flex' : 'hidden lg:flex'}`}>
            {estimatedValue ? (
              <div className="animate-in fade-in zoom-in-95 flex flex-col h-full justify-between pb-2">
                <div className="flex-none flex flex-col items-center">
                  <div className="inline-flex items-center gap-2 text-positive px-3 py-1 rounded-full text-[0.6875rem] font-semibold uppercase tracking-[0.08em] mb-3 mx-auto" style={{ backgroundColor: 'rgba(34, 197, 94, 0.1)', borderWidth: '1px', borderColor: 'rgba(34, 197, 94, 0.2)' }}>
                    Beregning klar
                  </div>

                  <div className="text-center mb-4">
                    <h3 className="text-tx-dim text-[0.6875rem] font-semibold uppercase tracking-[0.08em] mb-1 opacity-80">Ditt verdiestimat</h3>
                    <div className="text-[2.25rem] md:text-[3rem] font-bold text-tx-primary tracking-[-0.03em] leading-[1.15]">
                      {estimatedValue.toLocaleString('no-NO')}
                      <span className="ml-1 text-tx-primary text-[1.35rem] md:text-[1.8rem] font-normal">kr</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto w-full mb-4">
                     <div className="bg-elevated p-3 rounded-xl border border-br-subtle text-center">
                        <div className="text-tx-dim text-[0.625rem] font-semibold uppercase tracking-[0.06em] mb-0.5">Pris/m²</div>
                        <div className="text-tx-primary font-bold text-[0.875rem]">{Math.round(estimatedValue / area).toLocaleString('no-NO')}</div>
                     </div>
                     <div className="bg-elevated p-3 rounded-xl border border-br-subtle text-center">
                        <div className="text-tx-dim text-[0.625rem] font-semibold uppercase tracking-[0.06em] mb-0.5">Trend</div>
                        <div className="text-positive font-bold text-[0.875rem] flex items-center justify-center gap-1">
                          <TrendingUp className="w-3.5 h-3.5" />
                          +{district.priceChange}%
                        </div>
                     </div>
                  </div>

                  <div className="w-full space-y-4 mb-2">
                    <div className="text-center">
                      <h4 className="text-tx-primary font-bold text-[1rem] mb-1">Trenger du en verdivurdering?</h4>
                      <p className="text-tx-muted text-[0.8125rem] font-normal leading-relaxed max-w-[280px] mx-auto opacity-90 px-2">
                        Jeg hjelper deg med en kostnadsfri e-takst av boligen din
                      </p>
                    </div>

                    <div className="flex justify-center">
                      <ul className="space-y-2">
                        {[
                          'Uforpliktende møte',
                          'Motta tips og råd',
                          'Sett av 30 – 60 minutter'
                        ].map((item, i) => (
                          <li key={i} className="flex items-center gap-3 text-tx-primary text-[0.6875rem] font-semibold uppercase tracking-[0.08em]">
                            <div className="w-1.5 h-1.5 rounded-full bg-positive" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mt-auto">
                  <button className="w-full bg-positive hover:opacity-90 text-white font-semibold py-4 rounded-xl flex items-center justify-center gap-2 uppercase tracking-[0.08em] text-[0.8125rem] transition-all shadow-xl shadow-positive/20 active:scale-[0.98]">
                    Få en presis verdivurdering
                    <ArrowRight className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleReset}
                    className="w-full text-tx-dim hover:text-tx-primary text-[0.8125rem] font-normal flex items-center justify-center gap-2 py-1 transition-colors"
                  >
                    <ChevronLeft className="w-3 h-3" />
                    Endre detaljer
                  </button>
                </div>
              </div>
            ) : (
              <div className="hidden lg:flex flex-col items-center justify-center h-full max-w-[250px] mx-auto opacity-40">
                <div className="w-16 h-16 bg-elevated rounded-3xl flex items-center justify-center border border-br-default mb-6">
                  <CalcIcon className="w-8 h-8 text-tx-dim" />
                </div>
                <h4 className="text-tx-dim font-semibold text-[0.6875rem] tracking-[0.08em] mb-2 uppercase">Resultat</h4>
                <p className="text-tx-dim text-[0.8125rem] leading-relaxed text-center font-normal">
                  Verdiestimatet ditt dukker opp her når du har fylt ut detaljene.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Hjelpe-ikon for Calc
const CalcIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="4" y="2" width="16" height="20" rx="2" ry="2"/>
    <line x1="8" y1="10" x2="16" y2="10"/>
    <line x1="8" y1="14" x2="16" y2="14"/>
    <line x1="8" y1="18" x2="16" y2="18"/>
    <line x1="8" y1="6" x2="16" y2="6"/>
  </svg>
);

export default Calculator;
