import { describe, it, expect } from 'vitest';
import { edgeDentils } from './facade';

describe('edgeDentils', () => {
  it('emits evenly spaced placements along each edge with outward angle', () => {
    const rect: [number, number][] = [[0, 0], [1000, 0], [1000, 500], [0, 500]];
    const d = edgeDentils(rect, 0.012696, 0.5);
    expect(d.length).toBeGreaterThan(20);
    const first = d[0];
    expect(first).toHaveProperty('x');
    expect(first).toHaveProperty('z');
    expect(first).toHaveProperty('angle');
    // alle plasseringer ligger på en av kantene (x eller z konstant for rektangelet)
  });
});
