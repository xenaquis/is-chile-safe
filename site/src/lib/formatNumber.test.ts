/**
 * formatNumber.test.ts — TDD RED: tests fail before implementation exists.
 */
import { describe, it, expect } from 'vitest';
import { formatRate, formatDecimal } from './formatNumber';

describe('formatRate', () => {
  it('formats EN with comma thousands separator', () => {
    expect(formatRate(4984.1, 'en')).toBe('4,984');
  });

  it('formats ES with period thousands separator', () => {
    expect(formatRate(4984.1, 'es')).toBe('4.984');
  });

  it('rounds to integer', () => {
    expect(formatRate(100.6, 'en')).toBe('101');
  });

  it('handles zero', () => {
    expect(formatRate(0, 'en')).toBe('0');
    expect(formatRate(0, 'es')).toBe('0');
  });
});

describe('formatDecimal', () => {
  it('formats EN with comma thousands and period decimal', () => {
    expect(formatDecimal(2871.5, 'en')).toBe('2,871.5');
  });

  it('formats ES with period thousands and comma decimal', () => {
    expect(formatDecimal(8.69, 'es', 1)).toBe('8,7');
  });

  it('respects custom decimals parameter', () => {
    expect(formatDecimal(1.234, 'en', 2)).toBe('1.23');
  });
});
