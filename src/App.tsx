import React, { useState, useRef, useCallback, useEffect } from 'react';
import { OSLO_DISTRICTS, getPreposisjon } from '@/constants';
import { DistrictInfo } from '@/types';
import MapComponent, { MapComponentHandle, TileLayerKey, TILE_LAYERS } from '@/components/MapComponent';
import DistrictStats from '@/components/DistrictStats';
import Calculator from '@/components/Calculator';
import Header from '@/components/Header';
import { ChevronDown, ChevronUp, Plus, Minus, Layers, Target, Moon, Sun } from 'lucide-react';
import logoStackedLight from '@/assets/logo-stacked-light.png';
import heroBackground from '@/assets/M-hero.webp';

const App: React.FC = () => {
  const [selectedDistrictId, setSelectedDistrictId] = useState<string | null>(null);
  const [showCalculator, setShowCalculator] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTileLayer, setActiveTileLayer] = useState<TileLayerKey>('blue');
  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);
  const mapComponentRef = useRef<MapComponentHandle>(null);
  const heroTitleRef = useRef<HTMLHeadingElement>(null);

  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return !window.matchMedia('(prefers-color-scheme: light)').matches;
  });

  const [isDesktop, setIsDesktop] = useState(() => window.innerWidth >= 768);
  const [fixedColPx] = useState(() => Math.round(window.innerWidth * 0.4));

  useEffect(() => {
    const update = () => setIsDesktop(window.innerWidth >= 768);
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDark(prev => {
      const next = !prev;
      document.documentElement.classList.toggle('dark', next);
      localStorage.setItem('theme', next ? 'dark' : 'light');
      return next;
    });
  }, []);

  const selectedDistrict = OSLO_DISTRICTS.find(d => d.id === selectedDistrictId) || null;

  const fitHeroTitle = useCallback(() => {
    const el = heroTitleRef.current;
    if (!el) return;
    const maxSize = 28;
    const minSize = 20;
    el.style.fontSize = '';
    el.style.whiteSpace = 'nowrap';
    if (window.innerWidth >= 768) return;
    el.style.fontSize = maxSize + 'px';
    let currentSize = maxSize;
    while (el.scrollWidth > el.clientWidth && currentSize > minSize) {
      currentSize -= 0.5;
      el.style.fontSize = currentSize + 'px';
    }
  }, []);

  useEffect(() => { requestAnimationFrame(fitHeroTitle); }, [selectedDistrictId, fitHeroTitle]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const onResize = () => { clearTimeout(timer); timer = setTimeout(fitHeroTitle, 100); };
    window.addEventListener('resize', onResize);
    return () => { window.removeEventListener('resize', onResize); clearTimeout(timer); };
  }, [fitHeroTitle]);

  const handleDistrictSelect = (district: DistrictInfo) => {
    setSelectedDistrictId(district.id);
    setIsExpanded(true);
    setShowCalculator(false);
  };

  const handleDistrictChangeById = (id: string) => setSelectedDistrictId(id);

  const toggleExpand = () => { if (selectedDistrictId) setIsExpanded(!isExpanded); };

  const getPanelHeightClass = () => showCalculator ? 'h-full' : 'h-auto';

  const MapControls = ({ size = 10 }: { size?: number }) => (
    <div className="absolute top-1/2 -translate-y-1/2 right-4 z-[500] flex flex-col gap-2 pointer-events-auto">
      <button onClick={() => mapComponentRef.current?.zoomIn()} className={`w-${size} h-${size} rounded-full flex items-center justify-center bg-white text-accent dark:bg-surface dark:text-white shadow-lg hover:bg-accent hover:text-white transition-all`}><Plus size={14} /></button>
      <button onClick={() => mapComponentRef.current?.zoomOut()} className={`w-${size} h-${size} rounded-full flex items-center justify-center bg-white text-accent dark:bg-surface dark:text-white shadow-lg hover:bg-accent hover:text-white transition-all`}><Minus size={14} /></button>
      <div className="relative mt-1">
        <button onClick={() => setIsLayerMenuOpen(!isLayerMenuOpen)} className={`w-${size} h-${size} rounded-full flex items-center justify-center transition-all shadow-lg ${isLayerMenuOpen ? 'bg-accent text-white' : 'bg-white text-accent dark:bg-surface dark:text-white'} hover:bg-accent hover:text-white`}><Layers size={14} /></button>
        {isLayerMenuOpen && (
          <div className="absolute right-full mr-2 top-0 rounded-lg shadow-xl overflow-hidden border bg-base border-br-subtle" style={{ minWidth: '120px' }}>
            {(Object.keys(TILE_LAYERS) as TileLayerKey[]).map((key) => (
              <button key={key} onClick={() => { mapComponentRef.current?.setTileLayer(key); setActiveTileLayer(key); setIsLayerMenuOpen(false); }} className={`w-full flex items-center gap-2 px-3 py-2 text-left text-[0.6875rem] font-semibold uppercase tracking-[0.08em] transition-colors ${activeTileLayer === key ? 'bg-accent text-white' : 'text-tx-muted hover:bg-elevated'}`}>{TILE_LAYERS[key].name}</button>
            ))}
          </div>
        )}
      </div>
      <button onClick={() => { mapComponentRef.current?.resetView(); setSelectedDistrictId(null); setIsExpanded(false); }} className={`w-${size} h-${size} rounded-full flex items-center justify-center bg-white text-accent dark:bg-surface dark:text-white shadow-lg hover:bg-accent hover:text-white transition-all`}><Target size={14} /></button>
    </div>
  );

  const StatsOverlay = () => (
    <div className="absolute bottom-0 left-0 right-0 z-[500] pointer-events-none">
      <div className="pointer-events-auto">
        {selectedDistrictId && !showCalculator && (
          <div className="flex justify-center mb-[-16px] md:mb-[-20px]">
            <button onClick={toggleExpand} className="w-8 h-8 md:w-10 md:h-10 bg-accent border-[3px] md:border-4 border-base rounded-full flex items-center justify-center text-white hover:bg-accent-hover transition-all shadow-2xl active:scale-90 group relative z-30">
              {isExpanded ? <ChevronDown className="w-4 h-4 md:w-5 md:h-5 group-hover:translate-y-0.5 transition-transform" /> : <ChevronUp className="w-4 h-4 md:w-5 md:h-5 group-hover:-translate-y-0.5 transition-transform" />}
            </button>
          </div>
        )}
        <div className={`overflow-hidden transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] ${getPanelHeightClass()} ${selectedDistrictId ? 'bg-base' : ''}`}>
          {showCalculator && selectedDistrict ? (
            <Calculator district={selectedDistrict} onDistrictChange={handleDistrictChangeById} onClose={() => setShowCalculator(false)} />
          ) : (
            <DistrictStats district={selectedDistrict} isExpanded={isExpanded} onOpenCalculator={() => setShowCalculator(true)} />
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col min-h-[100dvh] w-full bg-base text-tx-primary font-sans overflow-x-hidden">

      {isDesktop ? (
        /* ── DESKTOP / TABLET SPLIT HERO ── */
        <div className="relative flex overflow-hidden" style={{ height: '100vh' }}>

          {/* Nav — absolutt, spenner full bredde over begge kolonner */}
          <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center px-10 pt-6 pb-4">
            <nav className="flex gap-8">
              {['Forsiden', 'Kart', 'Markedsrapporter', 'Innsikt', 'Blogg'].map(name => (
                <a key={name} href="#" className="hover:underline transition-all" style={{ fontFamily: 'Poppins, sans-serif', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.85)', fontWeight: 600 }}>
                  {name}
                </a>
              ))}
            </nav>
            <button
              onClick={toggleTheme}
              className="absolute right-8 w-10 h-10 rounded-full border border-white/30 flex items-center justify-center text-white hover:bg-white/10 transition-all"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>

          {/* LEFT COLUMN — blå, logo sentrert */}
          <div className="w-1/2 bg-[#45aaf7] flex items-center justify-center">
            <img src={logoStackedLight} alt="Innsikt" className="object-contain" style={{ maxWidth: '360px', width: '70%' }} />
          </div>

          {/* RIGHT COLUMN — mørk, kart som card */}
          <div className="w-1/2 relative overflow-hidden" style={{ height: '100vh' }}>
            <img src={heroBackground} alt="" className="absolute inset-0 w-full h-full object-cover" />
            <div className="absolute overflow-hidden" style={{ top: 'calc(22vh + 150px)', bottom: '0', left: '9%', right: '9%', borderRadius: '16px' }}>
              <div className="absolute inset-0">
                <MapComponent
                  ref={mapComponentRef}
                  properties={[]}
                  districts={OSLO_DISTRICTS}
                  selectedProperty={null}
                  selectedDistrict={selectedDistrict}
                  onPropertySelect={() => {}}
                  onDistrictSelect={handleDistrictSelect}
                  isDark={isDark}
                />
              </div>
              <MapControls size={10} />
              <StatsOverlay />
            </div>
          </div>
        </div>

      ) : (
        /* ── MOBILE LAYOUT ── */
        <>
          <Header onToggleTheme={toggleTheme} isDark={isDark} />
          <div className="flex-1 flex flex-col min-h-0">
            <div className="w-full flex flex-col px-0 mx-auto min-h-0 flex-1">
              <div className={`pt-2 pb-2 shrink-0 text-left px-4 ${showCalculator ? 'hidden' : 'block'}`}>
                <h1 ref={heroTitleRef} className="font-hero text-[2rem] font-extrabold text-tx-primary tracking-[-1px] leading-[1.1] mb-0.5">
                  Boligmarkedet {getPreposisjon(selectedDistrict?.name)} <span className="text-accent">{selectedDistrict?.name || 'Oslo'}</span>
                </h1>
                <p className="text-tx-muted font-normal text-[0.875rem] opacity-90 leading-relaxed whitespace-nowrap overflow-hidden text-ellipsis">
                  {selectedDistrict?.description || 'Er det kjøper eller selgers marked i Oslo nå?'}
                </p>
              </div>
              <div className="flex-1 min-h-0 relative">
                <div className="absolute inset-0">
                  <MapComponent
                    ref={mapComponentRef}
                    properties={[]}
                    districts={OSLO_DISTRICTS}
                    selectedProperty={null}
                    selectedDistrict={selectedDistrict}
                    onPropertySelect={() => {}}
                    onDistrictSelect={handleDistrictSelect}
                    isDark={isDark}
                  />
                </div>
                <MapControls size={8} />
                <StatsOverlay />
              </div>
            </div>
          </div>
        </>
      )}


    </div>
  );
};

export default App;
