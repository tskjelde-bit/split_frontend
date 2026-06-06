import { describe, it, expect, beforeEach } from 'vitest';
import { applyQaParam } from './qa';
import { useVelger } from '../state/store';

beforeEach(() => useVelger.getState().reset());

describe('applyQaParam', () => {
  it('exploded → exploded all', () => {
    applyQaParam('exploded');
    expect(useVelger.getState().mode).toBe('exploded');
  });
  it('floor2 → exploded with focus 2', () => {
    applyQaParam('floor2');
    expect(useVelger.getState().focus).toBe('2');
  });
  it('unit-H0204 → selects unit', () => {
    applyQaParam('unit-H0204');
    expect(useVelger.getState().selected).toBe('H0204');
  });
  it('null is a no-op', () => {
    applyQaParam(null);
    expect(useVelger.getState().mode).toBe('landing');
  });
});
