/**
 * Catalog of definitions and scale equivalences for Daily Log metrics.
 * Used for helper text and "¿Qué es?" sections in the client Registro diario.
 */

export type DailyLogMetricKey =
  | 'rpe'
  | 'energy_level'
  | 'pain_level'
  | 'hunger_level'
  | 'cravings_level'
  | 'digestion_quality'

export interface MetricRange {
  /** e.g. "1-2" or "0" */
  range: string
  label: string
  /** Inclusive min value for this range */
  min: number
  /** Inclusive max value for this range */
  max: number
}

export interface MetricDefinition {
  title: string
  /** "¿Qué es?" / "Qué mide" body as list items */
  descriptionLines: string[]
  ranges: MetricRange[]
  /** min value for the scale (1 or 0 for pain) */
  scaleMin: number
  /** max value for the scale */
  scaleMax: number
}

const metricsCatalog: Record<DailyLogMetricKey, MetricDefinition> = {
  rpe: {
    title: 'Esfuerzo percibido (RPE)',
    scaleMin: 1,
    scaleMax: 10,
    descriptionLines: [
      'Es qué tan duro sentiste el entrenamiento, independientemente de lo que diga el video.',
      'No mide duración',
      'No mide calorías',
      'Mide sensación interna de exigencia',
    ],
    ranges: [
      { range: '1–2', label: 'Muy suave (movilidad, caminar)', min: 1, max: 2 },
      { range: '3–4', label: 'Cómodo', min: 3, max: 4 },
      { range: '5–6', label: 'Retador pero controlado', min: 5, max: 6 },
      { range: '7–8', label: 'Muy demandante', min: 7, max: 8 },
      { range: '9–10', label: 'Máximo, al límite', min: 9, max: 10 },
    ],
  },
  energy_level: {
    title: 'Nivel de energía',
    scaleMin: 1,
    scaleMax: 10,
    descriptionLines: [
      'Cómo te sentías durante y al final del entrenamiento, no antes.',
      'No es motivación mental, es:',
      'gasolina física',
      'capacidad de sostener el esfuerzo',
      'recuperación intra-entreno',
    ],
    ranges: [
      { range: '1–2', label: 'Drenado', min: 1, max: 2 },
      { range: '3–4', label: 'Bajo', min: 3, max: 4 },
      { range: '5–6', label: 'Estable', min: 5, max: 6 },
      { range: '7–8', label: 'Alto', min: 7, max: 8 },
      { range: '9–10', label: 'Explosivo', min: 9, max: 10 },
    ],
  },
  pain_level: {
    title: 'Dolor (0–10)',
    scaleMin: 0,
    scaleMax: 10,
    descriptionLines: [
      'Dolor físico real: articulaciones, músculos, molestias sospechosas.',
      'NO es cansancio',
      'NO es ardor muscular normal',
    ],
    ranges: [
      { range: '0', label: 'Nada', min: 0, max: 0 },
      { range: '1–3', label: 'Molestia leve', min: 1, max: 3 },
      { range: '4–6', label: 'Dolor que requiere atención', min: 4, max: 6 },
      { range: '7–10', label: 'Riesgo de lesión', min: 7, max: 10 },
    ],
  },
  hunger_level: {
    title: 'Hambre',
    scaleMin: 1,
    scaleMax: 10,
    descriptionLines: [
      'La señal fisiológica real de tu cuerpo pidiendo energía.',
      'No es ansiedad, no es antojo. Es: "necesito comida".',
    ],
    ranges: [
      { range: '1–2', label: 'Nada de hambre', min: 1, max: 2 },
      { range: '3–4', label: 'Ligera', min: 3, max: 4 },
      { range: '5–6', label: 'Normal / saludable', min: 5, max: 6 },
      { range: '7–8', label: 'Hambre intensa', min: 7, max: 8 },
      { range: '9–10', label: 'Déficit fuerte (riesgo)', min: 9, max: 10 },
    ],
  },
  cravings_level: {
    title: 'Antojos',
    scaleMin: 1,
    scaleMax: 10,
    descriptionLines: [
      'Deseo emocional o neuroquímico, no hambre real.',
      'Aquí entran:',
      'azúcar',
      'pan',
      'alcohol',
      'comida ultra-palatable',
    ],
    ranges: [
      { range: '1–2', label: 'Nada', min: 1, max: 2 },
      { range: '3–4', label: 'Leves', min: 3, max: 4 },
      { range: '5–6', label: 'Presentes pero manejables', min: 5, max: 6 },
      { range: '7–8', label: 'Difíciles de ignorar', min: 7, max: 8 },
      { range: '9–10', label: 'Descontrol', min: 9, max: 10 },
    ],
  },
  digestion_quality: {
    title: 'Digestión',
    scaleMin: 1,
    scaleMax: 10,
    descriptionLines: [
      'Cómo responde tu sistema digestivo a:',
      'volumen de comida',
      'tipos de alimentos',
      'timing',
      'estrés',
      'Incluye:',
      'inflamación',
      'pesadez',
      'gases',
      'reflujo',
      'regularidad',
    ],
    ranges: [
      { range: '1–2', label: 'Muy mala', min: 1, max: 2 },
      { range: '3–4', label: 'Molesta', min: 3, max: 4 },
      { range: '5–6', label: 'Normal', min: 5, max: 6 },
      { range: '7–8', label: 'Buena', min: 7, max: 8 },
      { range: '9–10', label: 'Excelente', min: 9, max: 10 },
    ],
  },
}

/**
 * Returns the label for the given metric and numeric value, or null if value is empty/invalid.
 * Used for helper text below the control, e.g. "RPE 7 → Muy demandante".
 */
export function getScaleLabel(metricKey: DailyLogMetricKey, value: number | '' | null | undefined): string | null {
  if (value === '' || value === null || value === undefined) return null
  const num = typeof value === 'number' ? value : Number(value)
  if (Number.isNaN(num)) return null
  const def = metricsCatalog[metricKey]
  if (!def) return null
  for (const r of def.ranges) {
    if (num >= r.min && num <= r.max) {
      const prefix = metricKey === 'rpe' ? 'RPE' : metricKey === 'energy_level' ? 'Energía' : metricKey === 'pain_level' ? 'Dolor' : metricKey === 'hunger_level' ? 'Hambre' : metricKey === 'cravings_level' ? 'Antojos' : 'Digestión'
      return `${prefix} ${num} → ${r.label}`
    }
  }
  return null
}

/**
 * Returns the full definition for a metric (title, description bullets, ranges).
 */
export function getMetricDefinition(metricKey: DailyLogMetricKey): MetricDefinition | null {
  return metricsCatalog[metricKey] ?? null
}

export { metricsCatalog }
