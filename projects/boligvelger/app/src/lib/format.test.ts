import { describe, it, expect } from 'vitest';
import { formatNOK } from './format';

describe('formatNOK', () => {
  it('formats millions with normalized spaces and em-dash suffix', () => {
    expect(formatNOK(6400000)).toBe('6 400 000,—');
  });
  it('formats price per sqm', () => {
    expect(formatNOK(230000)).toBe('230 000,—');
  });
});
