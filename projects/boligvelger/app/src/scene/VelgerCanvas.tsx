import { Canvas } from '@react-three/fiber';
import { ContactShadows, Environment } from '@react-three/drei';
import { Building } from './Building';
import { CameraRig } from './CameraRig';
import type { AppData } from '../lib/types';

const CREAM_BG = '#FBFAF6';

export function VelgerCanvas({ data }: { data: AppData }) {
  return (
    <Canvas
      shadows
      dpr={[1, Math.min(2, window.devicePixelRatio)]}
      camera={{ position: [18, 12, 18], fov: 35 }}
      style={{ background: CREAM_BG }}
    >
      <ambientLight intensity={0.80} />
      <directionalLight position={[12, 20, 8]} intensity={1.40} castShadow
        shadow-mapSize={[1024, 1024]} />
      <directionalLight position={[-10, 15, -10]} intensity={0.30} />
      <Environment preset="park" environmentIntensity={0.35} />
      <Building data={data} />
      <ContactShadows position={[0, -0.01, 0]} opacity={0.35} scale={45} blur={2.2} far={12} resolution={512} />
      <CameraRig geo={data.geo} />
    </Canvas>
  );
}
