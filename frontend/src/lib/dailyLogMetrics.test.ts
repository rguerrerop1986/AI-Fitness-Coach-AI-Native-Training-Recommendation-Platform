import { describe, it, expect } from 'vitest'
import { getScaleLabel, getMetricDefinition } from './dailyLogMetrics'

describe('getScaleLabel', () => {
  describe('rpe', () => {
    it('returns null for empty value', () => {
      expect(getScaleLabel('rpe', '')).toBeNull()
      expect(getScaleLabel('rpe', null)).toBeNull()
      expect(getScaleLabel('rpe', undefined)).toBeNull()
    })
    it('returns label for 1-2', () => {
      expect(getScaleLabel('rpe', 1)).toBe('RPE 1 → Muy suave (movilidad, caminar)')
      expect(getScaleLabel('rpe', 2)).toBe('RPE 2 → Muy suave (movilidad, caminar)')
    })
    it('returns label for 5-6', () => {
      expect(getScaleLabel('rpe', 5)).toBe('RPE 5 → Retador pero controlado')
      expect(getScaleLabel('rpe', 6)).toBe('RPE 6 → Retador pero controlado')
    })
    it('returns label for 9-10', () => {
      expect(getScaleLabel('rpe', 9)).toBe('RPE 9 → Máximo, al límite')
      expect(getScaleLabel('rpe', 10)).toBe('RPE 10 → Máximo, al límite')
    })
  })

  describe('pain_level (0-10)', () => {
    it('returns "Nada" for 0', () => {
      expect(getScaleLabel('pain_level', 0)).toBe('Dolor 0 → Nada')
    })
    it('returns label for 1-3', () => {
      expect(getScaleLabel('pain_level', 1)).toBe('Dolor 1 → Molestia leve')
      expect(getScaleLabel('pain_level', 3)).toBe('Dolor 3 → Molestia leve')
    })
    it('returns label for 7-10', () => {
      expect(getScaleLabel('pain_level', 7)).toBe('Dolor 7 → Riesgo de lesión')
      expect(getScaleLabel('pain_level', 10)).toBe('Dolor 10 → Riesgo de lesión')
    })
    it('returns null for empty', () => {
      expect(getScaleLabel('pain_level', '')).toBeNull()
    })
  })

  describe('energy_level', () => {
    it('returns label for 1-2 (Drenado)', () => {
      expect(getScaleLabel('energy_level', 1)).toBe('Energía 1 → Drenado')
    })
    it('returns label for 9-10 (Explosivo)', () => {
      expect(getScaleLabel('energy_level', 10)).toBe('Energía 10 → Explosivo')
    })
  })

  describe('hunger_level', () => {
    it('returns label for 1-2', () => {
      expect(getScaleLabel('hunger_level', 1)).toBe('Hambre 1 → Nada de hambre')
    })
    it('returns label for 9-10', () => {
      expect(getScaleLabel('hunger_level', 9)).toBe('Hambre 9 → Déficit fuerte (riesgo)')
    })
  })

  describe('cravings_level', () => {
    it('returns label for 7-8', () => {
      expect(getScaleLabel('cravings_level', 7)).toBe('Antojos 7 → Difíciles de ignorar')
    })
  })

  describe('digestion_quality', () => {
    it('returns label for 1-2 (Muy mala)', () => {
      expect(getScaleLabel('digestion_quality', 1)).toBe('Digestión 1 → Muy mala')
    })
    it('returns label for 9-10 (Excelente)', () => {
      expect(getScaleLabel('digestion_quality', 10)).toBe('Digestión 10 → Excelente')
    })
  })

  describe('edge cases', () => {
    it('returns null for NaN', () => {
      expect(getScaleLabel('rpe', Number.NaN)).toBeNull()
    })
  })
})

describe('getMetricDefinition', () => {
  it('returns definition for each metric key', () => {
    const keys = ['rpe', 'energy_level', 'pain_level', 'hunger_level', 'cravings_level', 'digestion_quality'] as const
    keys.forEach((key) => {
      const def = getMetricDefinition(key)
      expect(def).not.toBeNull()
      expect(def!.title).toBeTruthy()
      expect(Array.isArray(def!.descriptionLines)).toBe(true)
      expect(Array.isArray(def!.ranges)).toBe(true)
      expect(def!.scaleMin).toBeGreaterThanOrEqual(0)
      expect(def!.scaleMax).toBe(10)
    })
  })
  it('pain_level has scaleMin 0', () => {
    expect(getMetricDefinition('pain_level')!.scaleMin).toBe(0)
  })
  it('rpe has correct ranges', () => {
    const def = getMetricDefinition('rpe')!
    expect(def.ranges).toHaveLength(5)
    expect(def.ranges[0].range).toBe('1–2')
    expect(def.ranges[4].range).toBe('9–10')
  })
})
