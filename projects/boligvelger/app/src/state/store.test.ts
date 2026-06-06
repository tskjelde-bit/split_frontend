import { describe, it, expect, beforeEach } from 'vitest';
import { useVelger } from './store';

beforeEach(() => useVelger.getState().reset());

describe('velger store', () => {
  it('starts in landing mode', () => {
    expect(useVelger.getState().mode).toBe('landing');
  });
  it('explode sets mode and focus', () => {
    useVelger.getState().explode('2');
    expect(useVelger.getState().mode).toBe('exploded');
    expect(useVelger.getState().focus).toBe('2');
  });
  it('assemble clears selection and focus', () => {
    useVelger.getState().explode('all');
    useVelger.getState().select('H0204');
    useVelger.getState().assemble();
    const s = useVelger.getState();
    expect(s.mode).toBe('orbit');
    expect(s.selected).toBeNull();
    expect(s.focus).toBe('all');
  });
  it('selecting a unit in landing promotes to exploded', () => {
    useVelger.getState().select('H0101');
    expect(useVelger.getState().mode).toBe('exploded');
  });
});
