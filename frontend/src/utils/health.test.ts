import { describe, it, expect } from 'vitest';
import { calculateBmi, getBmiCategory } from './health';

describe('calculateBmi', () => {
  it('returns rounded bmi for valid weight and height', () => {
    const bmi1 = calculateBmi(106.4, 1.85);
    expect(bmi1).toBeGreaterThanOrEqual(31.07);
    expect(bmi1).toBeLessThanOrEqual(31.10);
    expect(Number(bmi1!.toFixed(2))).toBe(bmi1);
    expect(calculateBmi(70, 1.75)).toBe(22.86);
  });

  it('returns null when height <= 0', () => {
    expect(calculateBmi(70, 0)).toBe(null);
    expect(calculateBmi(70, -1)).toBe(null);
  });

  it('returns null when weight or height is null/undefined', () => {
    expect(calculateBmi(null, 1.75)).toBe(null);
    expect(calculateBmi(70, null)).toBe(null);
    expect(calculateBmi(undefined, 1.75)).toBe(null);
    expect(calculateBmi(70, undefined)).toBe(null);
  });
});

describe('getBmiCategory', () => {
  it('returns underweight for bmi < 18.5', () => {
    expect(getBmiCategory(18.49)).toBe('underweight');
    expect(getBmiCategory(0)).toBe('underweight');
    expect(getBmiCategory(10)).toBe('underweight');
  });

  it('returns normal for 18.5 <= bmi < 25', () => {
    expect(getBmiCategory(18.5)).toBe('normal');
    expect(getBmiCategory(24.99)).toBe('normal');
    expect(getBmiCategory(20)).toBe('normal');
  });

  it('returns overweight for 25 <= bmi < 30', () => {
    expect(getBmiCategory(25.0)).toBe('overweight');
    expect(getBmiCategory(29.99)).toBe('overweight');
    expect(getBmiCategory(27)).toBe('overweight');
  });

  it('returns obesity1 for 30 <= bmi < 35', () => {
    expect(getBmiCategory(30.0)).toBe('obesity1');
    expect(getBmiCategory(34.99)).toBe('obesity1');
    expect(getBmiCategory(32)).toBe('obesity1');
  });

  it('returns obesity2 for 35 <= bmi < 40', () => {
    expect(getBmiCategory(35.0)).toBe('obesity2');
    expect(getBmiCategory(39.99)).toBe('obesity2');
    expect(getBmiCategory(37)).toBe('obesity2');
  });

  it('returns obesity3 for bmi >= 40', () => {
    expect(getBmiCategory(40.0)).toBe('obesity3');
    expect(getBmiCategory(45)).toBe('obesity3');
    expect(getBmiCategory(100)).toBe('obesity3');
  });

  it('returns noData for null, undefined, NaN (Sin datos)', () => {
    expect(getBmiCategory(null)).toBe('noData');
    expect(getBmiCategory(undefined)).toBe('noData');
    expect(getBmiCategory(NaN)).toBe('noData');
  });
});
