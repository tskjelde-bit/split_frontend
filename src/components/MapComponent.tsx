
import React, { useEffect, useRef, useCallback, forwardRef, useImperativeHandle } from 'react';
import { Property, DistrictInfo } from '../types';
import L from 'leaflet';

// Tile layer definitions — all Mapbox
export type TileLayerKey = 'blue' | 'snapmap' | 'dark';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

export const TILE_LAYERS: Record<TileLayerKey, { name: string; url: string; options?: L.TileLayerOptions }> = {
  blue: {
    name: 'Blue',
    url: `https://api.mapbox.com/styles/v1/drskjelde/cmlqiffkq000301qpb4r778e7/tiles/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`,
    options: { maxZoom: 19, tileSize: 512, zoomOffset: -1 },
  },
  snapmap: {
    name: 'Snapmap',
    url: `https://api.mapbox.com/styles/v1/drskjelde/cmkm3e0hv00it01sd4ddd4syy/tiles/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`,
    options: { maxZoom: 19, tileSize: 512, zoomOffset: -1 },
  },
  dark: {
    name: 'Dark',
    url: `https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`,
    options: { maxZoom: 19, tileSize: 512, zoomOffset: -1 },
  },
};

// Custom Mapbox dark style for automatic theme switching
const MAPBOX_DARK_STYLE_URL = `https://api.mapbox.com/styles/v1/drskjelde/cmlqhxlot000401sdfh3a2ktd/tiles/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`;
const MAPBOX_DARK_STYLE_OPTIONS: L.TileLayerOptions = { maxZoom: 19, tileSize: 512, zoomOffset: -1 };

// Choropleth color scale for light mode (based on priceChange %)
const CHOROPLETH_SCALE: [number, string][] = [
  [0, '#93C5FD'],
  [2, '#60A5FA'],
  [3, '#3B82F6'],
  [4, '#2563EB'],
  [5, '#1D4ED8'],
  [6, '#1E40AF'],
];
const CHOROPLETH_MAX = '#1E3A8A';
const SELECTED_COLOR_LIGHT = '#2D4B5F';

function getChoroplethColor(priceChange: number): string {
  for (let i = CHOROPLETH_SCALE.length - 1; i >= 0; i--) {
    if (priceChange >= CHOROPLETH_SCALE[i][0]) return CHOROPLETH_SCALE[i][1];
  }
  return CHOROPLETH_SCALE[0][1];
}

function getHoverColor(priceChange: number): string {
  const natural = getChoroplethColor(priceChange);
  const idx = CHOROPLETH_SCALE.findIndex(([, c]) => c === natural);
  if (idx < CHOROPLETH_SCALE.length - 1) return CHOROPLETH_SCALE[idx + 1][1];
  return CHOROPLETH_MAX;
}

// Theme-aware style helpers
function getThemeStyles(dark: boolean) {
  return {
    border: {
      color: dark ? 'rgba(255,255,255,0.15)' : '#FFFFFF',
      weight: dark ? 1 : 1.5,
      opacity: dark ? 1 : 0.8,
      selectedColor: dark ? '#3b82f6' : '#2563eb',
      selectedWeight: 2,
    },
    fill: {
      // Dark mode: subtle fills. Light mode: uses choropleth instead.
      default: dark ? 'rgba(59,130,246,0.05)' : 'transparent',
      hover: dark ? 'rgba(59,130,246,0.12)' : 'transparent',
      selected: dark ? 'rgba(59,130,246,0.2)' : SELECTED_COLOR_LIGHT,
    },
    label: {
      color: dark ? '#f1f5f9' : '#1E3A50',
      shadow: dark
        ? '0 1px 3px rgba(0,0,0,0.8), 0 0 8px rgba(0,0,0,0.5)'
        : '0 0 4px rgba(255,255,255,0.9), 0 0 2px rgba(255,255,255,0.9)',
      selectedColor: dark ? '#3b82f6' : '#FFFFFF',
      selectedShadow: dark
        ? '0 1px 3px rgba(0,0,0,0.8), 0 0 8px rgba(0,0,0,0.5)'
        : '0 1px 3px rgba(0,0,0,0.4)',
    },
    dim: {
      labelOpacity: 0.5,
      borderOpacity: 0.3,
      fillOpacity: 0.2,
    },
    useChoropleth: !dark,
  };
}

// Desktop/tablet settings
const DEFAULT_CENTER: L.LatLngExpression = [59.92, 10.76];
const DEFAULT_ZOOM = 11.5;

// Mobile settings
const MOBILE_CENTER: L.LatLngExpression = [59.91, 10.76];
const MOBILE_ZOOM = 10.6;

function getDefaultView(): { center: L.LatLngExpression; zoom: number } {
  const isMobile = window.innerWidth < 768;
  return isMobile
    ? { center: MOBILE_CENTER, zoom: MOBILE_ZOOM }
    : { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM };
}

export interface MapComponentHandle {
  zoomIn: () => void;
  zoomOut: () => void;
  resetView: () => void;
  setTileLayer: (key: TileLayerKey) => void;
}

interface MapComponentProps {
  properties: Property[];
  districts: DistrictInfo[];
  selectedProperty: Property | null;
  selectedDistrict: DistrictInfo | null;
  onPropertySelect: (p: Property) => void;
  onDistrictSelect: (d: DistrictInfo) => void;
  isDark?: boolean;
}

const MapComponent = forwardRef<MapComponentHandle, MapComponentProps>(({
  properties,
  districts,
  selectedProperty,
  selectedDistrict,
  onPropertySelect,
  onDistrictSelect,
  isDark
}, ref) => {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null);
  const hoveredLayerRef = useRef<L.Layer | null>(null);
  const labelMarkersRef = useRef<L.Marker[]>([]);
  const geoJsonDataRef = useRef<any>(null);
  const labelDataRef = useRef<any[]>([]);
  const dataLoadedRef = useRef(false);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const userTileKeyRef = useRef<TileLayerKey>('blue');
  const activeTileKeyRef = useRef<TileLayerKey>('blue');

  // Stable refs for callbacks
  const districtsRef = useRef(districts);
  districtsRef.current = districts;
  const selectedDistrictRef = useRef(selectedDistrict);
  selectedDistrictRef.current = selectedDistrict;
  const onDistrictSelectRef = useRef(onDistrictSelect);
  onDistrictSelectRef.current = onDistrictSelect;
  const isDarkRef = useRef(isDark);
  isDarkRef.current = isDark;

  const findDistrictByName = useCallback((name: string): DistrictInfo | undefined => {
    return districtsRef.current.find(d => d.name === name);
  }, []);

  const renderGeoJson = useCallback(() => {
    const map = mapRef.current;
    const geoJsonData = geoJsonDataRef.current;
    if (!map || !geoJsonData) return;

    if (geoJsonLayerRef.current) {
      map.removeLayer(geoJsonLayerRef.current);
      geoJsonLayerRef.current = null;
    }

    const selected = selectedDistrictRef.current;
    const dark = !!isDarkRef.current;
    const ts = getThemeStyles(dark);
    const isSnapmap = activeTileKeyRef.current === 'snapmap';

    const layer = L.geoJSON(geoJsonData, {
      style: (feature) => {
        if (isSnapmap) {
          return { fillColor: 'transparent', fillOpacity: 0, weight: 0, color: 'transparent', opacity: 0 };
        }

        const name = feature?.properties?.BYDELSNAVN;
        const district = findDistrictByName(name);
        const isSelected = district && selected && district.name === selected.name;
        const hasSelection = !!selected;

        if (isSelected) {
          return {
            fillColor: ts.fill.selected,
            fillOpacity: ts.useChoropleth ? 0.4 : 1,
            weight: ts.border.selectedWeight,
            color: ts.border.selectedColor,
            opacity: 1,
          };
        }

        if (ts.useChoropleth && district) {
          // Light mode: choropleth fill
          return {
            fillColor: getChoroplethColor(district.priceChange),
            fillOpacity: hasSelection ? ts.dim.fillOpacity : 0.4,
            weight: ts.border.weight,
            color: ts.border.color,
            opacity: hasSelection ? ts.dim.borderOpacity : ts.border.opacity,
          };
        }

        // Dark mode: subtle fill
        return {
          fillColor: ts.fill.default,
          fillOpacity: hasSelection ? ts.dim.fillOpacity : 1,
          weight: ts.border.weight,
          color: ts.border.color,
          opacity: hasSelection ? ts.dim.borderOpacity : 1,
        };
      },
      onEachFeature: (feature, layer) => {
        const name = feature?.properties?.BYDELSNAVN;
        const district = findDistrictByName(name);
        if (!district) return;

        layer.on({
          mouseover: (e: L.LeafletMouseEvent) => {
            const target = e.target;
            const sel = selectedDistrictRef.current;
            const dark = !!isDarkRef.current;
            const hoverTs = getThemeStyles(dark);

            // Reset previously hovered layer to avoid stuck highlights
            if (hoveredLayerRef.current && hoveredLayerRef.current !== target) {
              if (geoJsonLayerRef.current) {
                geoJsonLayerRef.current.resetStyle(hoveredLayerRef.current);
              }
            }
            hoveredLayerRef.current = target;

            if (!sel || district.name !== sel.name) {
              if (!isSnapmap) {
                if (hoverTs.useChoropleth) {
                  target.setStyle({
                    fillColor: getHoverColor(district.priceChange),
                    fillOpacity: 0.55,
                    weight: hoverTs.border.selectedWeight,
                    color: hoverTs.border.selectedColor,
                    opacity: 1,
                  });
                } else {
                  target.setStyle({
                    fillColor: hoverTs.fill.hover,
                    fillOpacity: 1,
                    weight: hoverTs.border.selectedWeight,
                    color: hoverTs.border.selectedColor,
                    opacity: 1,
                  });
                }
              }
            }
            const el = (target as any)._path;
            if (el) el.style.cursor = 'pointer';
          },
          mouseout: (e: L.LeafletMouseEvent) => {
            if (geoJsonLayerRef.current) {
              geoJsonLayerRef.current.resetStyle(e.target);
            }
            if (hoveredLayerRef.current === e.target) {
              hoveredLayerRef.current = null;
            }
          },
          click: (e: L.LeafletMouseEvent) => {
            L.DomEvent.stopPropagation(e);
            onDistrictSelectRef.current(district);
          }
        });
      }
    }).addTo(map);

    geoJsonLayerRef.current = layer;
  }, [findDistrictByName]);

  const renderLabels = useCallback(() => {
    const map = mapRef.current;
    const labels = labelDataRef.current;
    if (!map || labels.length === 0) return;

    labelMarkersRef.current.forEach(m => m.remove());
    labelMarkersRef.current = [];

    const dark = !!isDarkRef.current;
    const ts = getThemeStyles(dark);
    const selected = selectedDistrictRef.current;
    const hasSelection = !!selected;
    const isMobile = window.innerWidth < 768;

    labels.forEach((feature: any) => {
      const name = feature.properties.BYDELSNAVN;
      const district = findDistrictByName(name);
      if (!district) return;
      if (district.name === 'Oslo (Totalt)') return;

      const coords = feature.geometry.coordinates;
      const isSelected = selected && district.name === selected.name;
      const isDimmed = hasSelection && !isSelected;

      const fontSize = isSelected
        ? (isMobile ? '0.6875rem' : '0.75rem')
        : (isMobile ? '0.625rem' : '0.6875rem');
      const fontWeight = isSelected ? '700' : '600';
      const letterSpacing = isMobile ? '0.06em' : '0.08em';
      const color = isSelected ? ts.label.selectedColor : ts.label.color;
      const shadow = isSelected ? ts.label.selectedShadow : ts.label.shadow;
      const opacity = isDimmed ? ts.dim.labelOpacity : 1;

      const icon = L.divIcon({
        className: 'district-choropleth-label',
        html: `<div style="
          font-size: ${fontSize};
          font-weight: ${fontWeight};
          text-transform: uppercase;
          letter-spacing: ${letterSpacing};
          white-space: nowrap;
          color: ${color};
          text-shadow: ${shadow};
          opacity: ${opacity};
          pointer-events: auto;
          cursor: pointer;
          user-select: none;
          transition: opacity 0.3s ease;
        ">${district.name}</div>`,
        iconSize: [0, 0],
        iconAnchor: [0, 0],
      });

      const marker = L.marker([coords[1], coords[0]], {
        icon,
        zIndexOffset: isSelected ? 2000 : 1000,
        interactive: true,
      })
        .addTo(map)
        .on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          onDistrictSelectRef.current(district);
        });

      labelMarkersRef.current.push(marker);
    });
  }, [findDistrictByName]);

  useImperativeHandle(ref, () => ({
    zoomIn: () => { mapRef.current?.zoomIn(); },
    zoomOut: () => { mapRef.current?.zoomOut(); },
    resetView: () => {
      const view = getDefaultView();
      mapRef.current?.setView(view.center, view.zoom);
    },
    setTileLayer: (key: TileLayerKey) => {
      const map = mapRef.current;
      if (!map) return;
      if (tileLayerRef.current) {
        map.removeLayer(tileLayerRef.current);
      }
      userTileKeyRef.current = key;
      activeTileKeyRef.current = key;
      const def = TILE_LAYERS[key];
      tileLayerRef.current = L.tileLayer(def.url, def.options).addTo(map);
      if (dataLoadedRef.current) {
        renderGeoJson();
        renderLabels();
      }
    },
  }));

  // Initialize map and load data
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const view = getDefaultView();
    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView(view.center, view.zoom);

    if (isDark) {
      tileLayerRef.current = L.tileLayer(MAPBOX_DARK_STYLE_URL, MAPBOX_DARK_STYLE_OPTIONS).addTo(map);
      activeTileKeyRef.current = 'dark';
    } else {
      const def = TILE_LAYERS.blue;
      tileLayerRef.current = L.tileLayer(def.url, def.options).addTo(map);
    }

    mapRef.current = map;

    let lastIsMobile = window.innerWidth < 768;
    const handleResize = () => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
        const currentIsMobile = window.innerWidth < 768;
        if (currentIsMobile !== lastIsMobile) {
          lastIsMobile = currentIsMobile;
          const newView = getDefaultView();
          mapRef.current.setView(newView.center, newView.zoom);
        }
      }
    };
    window.addEventListener('resize', handleResize);

    const basePath = import.meta.env.BASE_URL || '/';
    Promise.all([
      fetch(`${basePath}oslo_bydeler.geojson`).then(r => r.json()),
      fetch(`${basePath}oslo_label_points.geojson`).then(r => r.json()),
    ]).then(([polygons, labels]) => {
      geoJsonDataRef.current = polygons;
      labelDataRef.current = labels.features;
      dataLoadedRef.current = true;
      renderGeoJson();
      renderLabels();
    }).catch(err => {
      console.error('Failed to load GeoJSON data:', err);
    });

    return () => {
      window.removeEventListener('resize', handleResize);
      map.remove();
      mapRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Switch between dark/light tiles when isDark changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (userTileKeyRef.current !== 'blue') return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }
    if (isDark) {
      tileLayerRef.current = L.tileLayer(MAPBOX_DARK_STYLE_URL, MAPBOX_DARK_STYLE_OPTIONS).addTo(map);
      activeTileKeyRef.current = 'dark';
    } else {
      const def = TILE_LAYERS.blue;
      tileLayerRef.current = L.tileLayer(def.url, def.options).addTo(map);
      activeTileKeyRef.current = 'blue';
    }

    if (dataLoadedRef.current) {
      renderGeoJson();
      renderLabels();
    }
  }, [isDark, renderGeoJson, renderLabels]);

  // Re-render when selectedDistrict changes
  useEffect(() => {
    if (!dataLoadedRef.current) return;
    renderGeoJson();
    renderLabels();
  }, [selectedDistrict, renderGeoJson, renderLabels]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full"
      style={{ background: 'transparent' }}
    />
  );
});

MapComponent.displayName = 'MapComponent';

export default MapComponent;
