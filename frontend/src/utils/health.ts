/**
 * BMI category keys (OMS standard, adults).
 * Use with i18n: t('checkIns.bmiCategory.' + getBmiCategory(bmi))
 */
export type BmiCategoryKey =
  | 'underweight'
  | 'normal'
  | 'overweight'
  | 'obesity1'
  | 'obesity2'
  | 'obesity3'
  | 'noData';

/**
 * Calculates BMI from weight (kg) and height (m). Rounds to 2 decimals.
 * Returns null if either is null/undefined or heightM <= 0.
 */
export function calculateBmi(
  weightKg: number | null | undefined,
  heightM: number | null | undefined
): number | null {
  if (weightKg == null || heightM == null || typeof weightKg !== 'number' || typeof heightM !== 'number') {
    return null;
  }
  if (heightM <= 0 || Number.isNaN(weightKg) || Number.isNaN(heightM)) {
    return null;
  }
  const bmi = weightKg / (heightM * heightM);
  return parseFloat(bmi.toFixed(2));
}

/**
 * Returns the BMI category key for the given BMI value (OMS standard).
 * Use in UI with i18n: t('checkIns.bmiCategory.' + getBmiCategory(bmi))
 */
export function getBmiCategory(bmi: number | null | undefined): BmiCategoryKey {
  if (bmi == null || Number.isNaN(bmi) || typeof bmi !== 'number') {
    return 'noData';
  }
  if (bmi < 18.5) return 'underweight';
  if (bmi < 25.0) return 'normal';
  if (bmi < 30.0) return 'overweight';
  if (bmi < 35.0) return 'obesity1';
  if (bmi < 40.0) return 'obesity2';
  return 'obesity3';
}

/** Tooltip text with BMI ranges (OMS, adults). Multi-line, exact format. */
export function getBmiTooltipText(): string {
  return [
    'Bajo peso: < 18.5',
    'Normal: 18.5–24.9',
    'Sobrepeso: 25.0–29.9',
    'Obesidad I: 30.0–34.9',
    'Obesidad II: 35.0–39.9',
    'Obesidad III: ≥ 40.0',
  ].join('\n');
}
