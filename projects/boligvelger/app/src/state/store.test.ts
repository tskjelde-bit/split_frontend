import { describe, it, expect, beforeEach } from 'vitest';
import { useVelger, focusForFloor } from './store';

beforeEach(() => useVelger.getState().reset());

describe('focusForFloor', () => {
  it('maps basement and floor 1 to the shared U1 focus', () => {
    expect(focusForFloor('U')).toBe('U1');
    expect(focusForFloor('1')).toBe('U1');
  });
  it('maps floors 2 and 3 to themselves', () => {
    expect(focusForFloor('2')).toBe('2');
    expect(focusForFloor('3')).toBe('3');
  });
});

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
