import { useEffect, useRef } from 'react';
import { CameraControls } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import { useVelger } from '../state/store';

// Fixed 3/4 view direction. Both the framing distance and the lateral target
// offset are derived from the viewport aspect: portrait shrinks the horizontal
// FOV (so we pull back) and shifts the building's silhouette centre (so we slide
// the look-target along the screen-right axis to keep it centred, never
// clipping on mobile). Tuned against 1440x900 (landscape) and 390x844 (portrait).
type View = { dir: [number, number, number]; target: [number, number, number]; dist: number };

const VIEWS: Record<string, View> = {
  landing: { dir: [1, 0.5, 1], target: [2, 5, 1.5], dist: 42 },
  orbit: { dir: [1, 0.5, 1], target: [2, 5, 1.5], dist: 42 },
  exploded: { dir: [1, 0.7, 1], target: [2, 9.5, 1.5], dist: 52 },
};

// Screen-right axis for the 3/4 view; sliding the target along it recentres the
// silhouette in portrait without changing the viewing angle.
// SHIFT[0]/[2] reduced slightly so the right-side roof overhang has ≥15 px clearance
// at 390×844; the larger portrait-boost coefficient (1.65) also helps.
const SHIFT: [number, number, number] = [2.0, 0, -2.5];

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

// 0 in landscape -> 1 at the reference portrait aspect (~0.46).
function portraitK(aspect: number): number {
  return aspect >= 1 ? 0 : clamp01((1 - aspect) / (1 - 0.46));
}

function distanceFor(view: View, aspect: number): number {
  // Increased portrait boost coefficient from 1.5 to 1.65 to ensure ≥15 px
  // clearance on all sides at 390×844 (roof-overhang gate fix).
  const boost = aspect < 1 ? 1.65 / Math.max(aspect, 0.35) : 1;
  return view.dist * boost;
}

function lookAt(c: CameraControls, view: View, aspect: number, enableTransition: boolean) {
  const d = distanceFor(view, aspect);
  const k = portraitK(aspect);
  const [dx, dy, dz] = view.dir;
  const len = Math.hypot(dx, dy, dz);
  const tx = view.target[0] + SHIFT[0] * k;
  const ty = view.target[1] + SHIFT[1] * k;
  const tz = view.target[2] + SHIFT[2] * k;
  c.setLookAt(
    tx + (dx / len) * d, ty + (dy / len) * d, tz + (dz / len) * d,
    tx, ty, tz,
    enableTransition,
  );
}

export function CameraRig() {
  const ref = useRef<CameraControls>(null!);
  const mode = useVelger((s) => s.mode);
  const setMode = useVelger((s) => s.setMode);
  const size = useThree((s) => s.size);
  const aspect = size.width / size.height;

  // Keep a ref to the current aspect so the mode-change effect reads the live
  // value instead of a stale closure capture.
  const aspectRef = useRef(aspect);
  aspectRef.current = aspect;

  // Slow auto-rotate while on the landing view.
  useFrame((_, dt) => {
    if (useVelger.getState().mode === 'landing' && ref.current) {
      ref.current.azimuthAngle += dt * 0.12;
    }
  });

  // Re-frame on mode change (smooth transition).
  // Read aspectRef.current so we always use the live viewport size, not a
  // stale closure value from when this effect was registered.
  useEffect(() => {
    if (ref.current) lookAt(ref.current, VIEWS[mode], aspectRef.current, true);
  }, [mode]);

  // Re-frame on aspect/viewport change (snap, no transition) so portrait fits.
  useEffect(() => {
    if (ref.current) lookAt(ref.current, VIEWS[useVelger.getState().mode], aspect, false);
  }, [aspect]);

  // First user interaction promotes landing -> orbit.
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const onStart = () => {
      if (useVelger.getState().mode === 'landing') setMode('orbit');
    };
    c.addEventListener('controlstart', onStart);
    return () => c.removeEventListener('controlstart', onStart);
  }, [setMode]);

  return (
    <CameraControls
      ref={ref}
      makeDefault
      minDistance={10}
      maxDistance={160}
      maxPolarAngle={Math.PI / 2.05}
      smoothTime={0.45}
    />
  );
}
