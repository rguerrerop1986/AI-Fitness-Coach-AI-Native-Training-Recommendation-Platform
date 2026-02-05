import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { formatLocalYYYYMMDD } from '../lib/date';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-hot-toast';
import { calculateBmi, getBmiCategory, getBmiTooltipText } from '../utils/health';

// Payload exacto para POST (nested)
export interface StructuralPayload {
  client_id: number;
  date: string;
  weight_kg: number;
  height_m: number;
  rc_termino: number;
  rc_1min: number;
  skinfolds: {
    triceps: { m1: number; m2: number; m3: number; avg: number };
    subscapular: { m1: number; m2: number; m3: number; avg: number };
    suprailiac: { m1: number; m2: number; m3: number; avg: number };
    abdominal: { m1: number; m2: number; m3: number; avg: number };
    ant_thigh: { m1: number; m2: number; m3: number; avg: number };
    calf: { m1: number; m2: number; m3: number; avg: number };
  };
  diameters: {
    femoral: { l: number; r: number; avg: number };
    humeral: { l: number; r: number; avg: number };
    styloid: { l: number; r: number; avg: number };
  };
  perimeters: {
    waist: number;
    abdomen: number;
    calf: number;
    hip: number;
    chest: number;
    arm: { relaxed: number; flexed: number };
    thigh: { relaxed: number; flexed: number };
  };
  feedback: {
    rpe: number;
    fatigue: number;
    diet_adherence_pct: number;
    training_adherence_pct: number;
    notes: string;
  };
}

const SKINFOLD_KEYS = ['triceps', 'subscapular', 'suprailiac', 'abdominal', 'ant_thigh', 'calf'] as const;
const DIAMETER_KEYS = ['femoral', 'humeral', 'styloid'] as const;

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function avg3(a: number, b: number, c: number): number {
  return round2((a + b + c) / 3);
}

function avg2(a: number, b: number): number {
  return round2((a + b) / 2);
}

function num(v: string | number | undefined): number | undefined {
  if (v === '' || v === undefined) return undefined;
  const n = typeof v === 'number' ? v : parseFloat(String(v));
  return Number.isNaN(n) ? undefined : n;
}

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

const defaultSkincare = () => ({ m1: undefined as number | undefined, m2: undefined, m3: undefined, avg: 0 });
const defaultDiameter = () => ({ l: undefined as number | undefined, r: undefined, avg: 0 });

export default function CreateCheckIn() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { clientId } = useParams<{ clientId: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [weight_kg, setWeightKg] = useState<string>('');
  const [height_m, setHeightM] = useState<string>('');
  const [rc_termino, setRcTermino] = useState<string>('');
  const [rc_1min, setRc1min] = useState<string>('');

  const [skinfolds, setSkinfolds] = useState<Record<string, { m1?: number; m2?: number; m3?: number; avg: number }>>(
    Object.fromEntries(SKINFOLD_KEYS.map((k) => [k, defaultSkincare()]))
  );
  const [diameters, setDiameters] = useState<Record<string, { l?: number; r?: number; avg: number }>>(
    Object.fromEntries(DIAMETER_KEYS.map((k) => [k, defaultDiameter()]))
  );
  const [perimeters, setPerimeters] = useState({
    waist: '',
    abdomen: '',
    calf: '',
    hip: '',
    chest: '',
    arm_relaxed: '',
    arm_flexed: '',
    thigh_relaxed: '',
    thigh_flexed: '',
  });
  const [feedback, setFeedback] = useState({
    rpe: 5,
    fatigue: 5,
    diet_adherence_pct: 80,
    training_adherence_pct: 80,
    notes: '',
  });
  const [bmiTooltipOpen, setBmiTooltipOpen] = useState(false);

  useEffect(() => {
    if (clientId) fetchClient();
  }, [clientId]);

  const fetchClient = async () => {
    try {
      const res = await api.get(`/clients/${clientId}/`);
      setClient(res.data);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Error al cargar cliente');
    } finally {
      setLoading(false);
    }
  };

  const updateSkinfold = useCallback((key: string, field: 'm1' | 'm2' | 'm3', value: string) => {
    const v = num(value);
    setSkinfolds((prev) => {
      const next = { ...prev[key], [field]: v };
      const m1 = next.m1 ?? 0;
      const m2 = next.m2 ?? 0;
      const m3 = next.m3 ?? 0;
      next.avg = m1 && m2 && m3 ? avg3(m1, m2, m3) : 0;
      return { ...prev, [key]: next };
    });
  }, []);

  const updateDiameter = useCallback((key: string, side: 'l' | 'r', value: string) => {
    const v = num(value);
    setDiameters((prev) => {
      const next = { ...prev[key], [side]: v };
      const l = next.l ?? 0;
      const r = next.r ?? 0;
      next.avg = l && r ? avg2(l, r) : 0;
      return { ...prev, [key]: next };
    });
  }, []);

  const bmiLive = calculateBmi(num(weight_kg), num(height_m));

  const validate = useCallback((): boolean => {
    const err: Record<string, string> = {};
    if (num(weight_kg) == null) err['weight_kg'] = t('validation.required');
    const h = num(height_m);
    if (h == null) err['height_m'] = t('validation.required');
    else if (h <= 0) err['height_m'] = t('checkIns.structural.heightMustBePositive');
    if (num(rc_termino) == null) err['rc_termino'] = t('validation.required');
    if (num(rc_1min) == null) err['rc_1min'] = t('validation.required');
    SKINFOLD_KEYS.forEach((k) => {
      const s = skinfolds[k];
      if (num(s?.m1) == null) err[`skinfold_${k}_1`] = t('validation.required');
      if (num(s?.m2) == null) err[`skinfold_${k}_2`] = t('validation.required');
      if (num(s?.m3) == null) err[`skinfold_${k}_3`] = t('validation.required');
    });
    DIAMETER_KEYS.forEach((k) => {
      const d = diameters[k];
      if (num(d?.l) == null) err[`diameter_${k}_l`] = t('validation.required');
      if (num(d?.r) == null) err[`diameter_${k}_r`] = t('validation.required');
    });
    const perimKeys = ['waist', 'abdomen', 'calf', 'hip', 'chest', 'arm_relaxed', 'arm_flexed', 'thigh_relaxed', 'thigh_flexed'] as const;
    perimKeys.forEach((k) => {
      const val = perimeters[k];
      if (num(val) == null) err[`perimeter_${k}`] = t('validation.required');
    });
    setFieldErrors(err);
    return Object.keys(err).length === 0;
  }, [weight_kg, height_m, rc_termino, rc_1min, skinfolds, diameters, perimeters, t]);

  const buildPayload = useCallback((): StructuralPayload | null => {
    const w = num(weight_kg);
    const h = num(height_m);
    const rcT = num(rc_termino);
    const rc1 = num(rc_1min);
    if (w == null || h == null || rcT == null || rc1 == null) return null;

    const sf: StructuralPayload['skinfolds'] = {} as StructuralPayload['skinfolds'];
    SKINFOLD_KEYS.forEach((k) => {
      const s = skinfolds[k];
      const m1 = num(s?.m1);
      const m2 = num(s?.m2);
      const m3 = num(s?.m3);
      if (m1 == null || m2 == null || m3 == null) return;
      sf[k] = { m1, m2, m3, avg: avg3(m1, m2, m3) };
    });
    if (Object.keys(sf).length !== SKINFOLD_KEYS.length) return null;

    const diam: StructuralPayload['diameters'] = {} as StructuralPayload['diameters'];
    DIAMETER_KEYS.forEach((k) => {
      const d = diameters[k];
      const l = num(d?.l);
      const r = num(d?.r);
      if (l == null || r == null) return;
      diam[k] = { l, r, avg: avg2(l, r) };
    });
    if (Object.keys(diam).length !== DIAMETER_KEYS.length) return null;

    const waist = num(perimeters.waist);
    const abdomen = num(perimeters.abdomen);
    const calf = num(perimeters.calf);
    const hip = num(perimeters.hip);
    const chest = num(perimeters.chest);
    const armR = num(perimeters.arm_relaxed);
    const armF = num(perimeters.arm_flexed);
    const thighR = num(perimeters.thigh_relaxed);
    const thighF = num(perimeters.thigh_flexed);
    if ([waist, abdomen, calf, hip, chest, armR, armF, thighR, thighF].some((x) => x == null)) return null;

    return {
      client_id: Number(clientId),
      date: formatLocalYYYYMMDD(),
      weight_kg: w,
      height_m: h,
      rc_termino: rcT,
      rc_1min: rc1,
      skinfolds: sf,
      diameters: diam,
      perimeters: {
        waist: waist!,
        abdomen: abdomen!,
        calf: calf!,
        hip: hip!,
        chest: chest!,
        arm: { relaxed: armR!, flexed: armF! },
        thigh: { relaxed: thighR!, flexed: thighF! },
      },
      feedback: {
        rpe: feedback.rpe,
        fatigue: feedback.fatigue,
        diet_adherence_pct: feedback.diet_adherence_pct,
        training_adherence_pct: feedback.training_adherence_pct,
        notes: feedback.notes || '',
      },
    };
  }, [clientId, weight_kg, height_m, rc_termino, rc_1min, skinfolds, diameters, perimeters, feedback]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!validate()) return;
    const payload = buildPayload();
    if (!payload) return;
    setIsSubmitting(true);
    try {
      await api.post(`/clients/${clientId}/check-ins/`, payload);
      navigate(`/clients/${clientId}`);
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { detail?: string; message?: string } | Record<string, string[]> } };
      if (ax.response?.status === 409) {
        const detail = ax.response?.data && typeof ax.response.data === 'object' && 'detail' in ax.response.data
          ? String((ax.response.data as { detail?: string }).detail)
          : 'El cliente está inactivo. No se pueden crear seguimientos.';
        toast.error(detail);
        navigate(`/clients/${clientId}`);
        return;
      }
      const msg = ax?.response?.data;
      if (typeof msg === 'object' && msg !== null && !('detail' in msg)) {
        const flat: Record<string, string> = {};
        Object.entries(msg).forEach(([k, v]) => {
          flat[k] = Array.isArray(v) ? v.join(' ') : String(v);
        });
        setFieldErrors((prev) => ({ ...prev, ...flat }));
      }
      setError(ax?.response?.data?.message || (ax?.response?.data && typeof ax.response.data === 'object' && 'detail' in ax.response.data ? (ax.response.data as { detail?: string }).detail : undefined) || 'Error al crear seguimiento');
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClass = 'block w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500';
  const thClass = 'border border-gray-300 bg-gray-100 px-2 py-1.5 text-left text-sm font-medium text-gray-700';
  const tdClass = 'border border-gray-300 px-1 py-0.5';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-800">{t('errors.clientNotFound')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-lg rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{t('checkIns.newCheckIn')}</h1>
              <p className="mt-1 text-sm text-gray-600">
                {t('checkIns.client')}: {client.first_name} {client.last_name}
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate(`/clients/${clientId}`)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              {t('checkIns.backToClient')}
            </button>
          </div>

          <form onSubmit={onSubmit} className="px-6 py-6">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-700">{error}</div>
            )}

            {/* A) Datos principales */}
            <section className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t('checkIns.structural.mainData')}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('checkIns.structural.weightKg')} *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={weight_kg}
                    onChange={(e) => setWeightKg(e.target.value)}
                    className={inputClass}
                    placeholder="70.0"
                  />
                  {fieldErrors.weight_kg && <p className="mt-1 text-sm text-red-600">{fieldErrors.weight_kg}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('checkIns.structural.heightM')} *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max="2.5"
                    value={height_m}
                    onChange={(e) => setHeightM(e.target.value)}
                    className={inputClass}
                    placeholder="1.75"
                  />
                  {fieldErrors.height_m && <p className="mt-1 text-sm text-red-600">{fieldErrors.height_m}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('checkIns.structural.bmi')}</label>
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={bmiLive != null ? String(bmiLive) : ''}
                      className={`${inputClass} bg-gray-100 cursor-not-allowed w-24 flex-shrink-0`}
                      aria-readonly="true"
                    />
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        getBmiCategory(bmiLive) === 'noData'
                          ? 'bg-gray-100 text-gray-600'
                          : getBmiCategory(bmiLive) === 'normal'
                            ? 'bg-green-100 text-green-800'
                            : getBmiCategory(bmiLive) === 'underweight'
                              ? 'bg-sky-100 text-sky-800'
                              : getBmiCategory(bmiLive) === 'overweight'
                                ? 'bg-amber-100 text-amber-800'
                                : getBmiCategory(bmiLive) === 'obesity1' || getBmiCategory(bmiLive) === 'obesity2'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {t(`checkIns.structural.bmiCategory.${getBmiCategory(bmiLive)}`)}
                    </span>
                    <span className="relative inline-flex">
                      <button
                        type="button"
                        onMouseEnter={() => setBmiTooltipOpen(true)}
                        onMouseLeave={() => setBmiTooltipOpen(false)}
                        onFocus={() => setBmiTooltipOpen(true)}
                        onBlur={() => setBmiTooltipOpen(false)}
                        className="rounded p-0.5 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                        aria-label={t('checkIns.structural.bmiCategoryLabel')}
                        aria-describedby={bmiTooltipOpen ? 'bmi-ranges-tooltip' : undefined}
                      >
                        <span className="text-sm font-bold leading-none" style={{ fontFamily: 'serif' }}>ⓘ</span>
                      </button>
                      {bmiTooltipOpen && (
                        <span
                          id="bmi-ranges-tooltip"
                          role="tooltip"
                          className="absolute left-full top-0 z-50 ml-1 w-48 rounded border border-gray-200 bg-white px-2.5 py-2 text-left text-xs text-gray-700 shadow-lg whitespace-pre-line"
                        >
                          {getBmiTooltipText()}
                        </span>
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            {/* B) RC */}
            <section className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t('checkIns.structural.rcSection')}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('checkIns.structural.rcTermino')} *</label>
                  <input
                    type="number"
                    value={rc_termino}
                    onChange={(e) => setRcTermino(e.target.value)}
                    className={inputClass}
                  />
                  {fieldErrors.rc_termino && <p className="mt-1 text-sm text-red-600">{fieldErrors.rc_termino}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('checkIns.structural.rc1min')} *</label>
                  <input
                    type="number"
                    value={rc_1min}
                    onChange={(e) => setRc1min(e.target.value)}
                    className={inputClass}
                  />
                  {fieldErrors.rc_1min && <p className="mt-1 text-sm text-red-600">{fieldErrors.rc_1min}</p>}
                </div>
              </div>
            </section>

            {/* C) Pliegues - tabla tipo Excel */}
            <section className="mb-6 overflow-x-auto">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t('checkIns.structural.pliegues')}</h2>
              <table className="min-w-full border-collapse border border-gray-300">
                <thead>
                  <tr>
                    <th className={thClass} style={{ minWidth: 120 }}></th>
                    <th className={thClass}>{t('checkIns.structural.promedio')}</th>
                    <th className={thClass}>{t('checkIns.structural.measure1')}</th>
                    <th className={thClass}>{t('checkIns.structural.measure2')}</th>
                    <th className={thClass}>{t('checkIns.structural.measure3')}</th>
                  </tr>
                </thead>
                <tbody>
                  {SKINFOLD_KEYS.map((key) => (
                    <tr key={key}>
                      <td className={`${tdClass} bg-gray-50 font-medium`}>
                        {t(`checkIns.structural.${key === 'ant_thigh' ? 'antThigh' : key}`)}
                      </td>
                      <td className={tdClass}>
                        <input
                          type="text"
                          readOnly
                          value={skinfolds[key]?.avg ? String(skinfolds[key].avg) : ''}
                          className="w-full bg-gray-100 border-0 text-sm"
                        />
                      </td>
                      {(['m1', 'm2', 'm3'] as const).map((m) => (
                        <td key={m} className={tdClass}>
                          <input
                            type="number"
                            step="0.01"
                            value={skinfolds[key]?.[m] ?? ''}
                            onChange={(e) => updateSkinfold(key, m, e.target.value)}
                            className={`w-full ${inputClass}`}
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            {/* D) Diámetros */}
            <section className="mb-6 overflow-x-auto">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t('checkIns.structural.diameters')}</h2>
              <table className="min-w-full border-collapse border border-gray-300">
                <thead>
                  <tr>
                    <th className={thClass} style={{ minWidth: 100 }}></th>
                    <th className={thClass}>{t('checkIns.structural.left')}</th>
                    <th className={thClass}>{t('checkIns.structural.right')}</th>
                    <th className={thClass}>{t('checkIns.structural.promedio')}</th>
                  </tr>
                </thead>
                <tbody>
                  {DIAMETER_KEYS.map((key) => (
                    <tr key={key}>
                      <td className={`${tdClass} bg-gray-50 font-medium`}>{t(`checkIns.structural.${key}`)}</td>
                      <td className={tdClass}>
                        <input
                          type="number"
                          step="0.01"
                          value={diameters[key]?.l ?? ''}
                          onChange={(e) => updateDiameter(key, 'l', e.target.value)}
                          className={`w-full ${inputClass}`}
                        />
                      </td>
                      <td className={tdClass}>
                        <input
                          type="number"
                          step="0.01"
                          value={diameters[key]?.r ?? ''}
                          onChange={(e) => updateDiameter(key, 'r', e.target.value)}
                          className={`w-full ${inputClass}`}
                        />
                      </td>
                      <td className={tdClass}>
                        <input
                          type="text"
                          readOnly
                          value={diameters[key]?.avg ? String(diameters[key].avg) : ''}
                          className="w-full bg-gray-100 border-0 text-sm"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            {/* E) Perímetros */}
            <section className="mb-6 overflow-x-auto">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t('checkIns.structural.perimeters')}</h2>
              <table className="min-w-full border-collapse border border-gray-300">
                <thead>
                  <tr>
                    <th className={thClass} style={{ minWidth: 120 }}></th>
                    <th className={thClass}>{t('checkIns.structural.valueCm')}</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: 'waist', label: t('checkIns.structural.waist') },
                    { key: 'abdomen', label: t('checkIns.structural.abdomen') },
                    { key: 'calf', label: t('checkIns.structural.calf') },
                    { key: 'hip', label: t('checkIns.structural.hip') },
                    { key: 'chest', label: t('checkIns.structural.chest') },
                  ].map(({ key, label }) => (
                    <tr key={key}>
                      <td className={`${tdClass} bg-gray-50 font-medium`}>{label}</td>
                      <td className={tdClass}>
                        <input
                          type="number"
                          step="0.01"
                          value={perimeters[key as keyof typeof perimeters] ?? ''}
                          onChange={(e) => setPerimeters((p) => ({ ...p, [key]: e.target.value }))}
                          className={`w-full ${inputClass}`}
                        />
                      </td>
                    </tr>
                  ))}
                  <tr>
                    <td className={`${tdClass} bg-gray-50 font-medium`}>{t('checkIns.structural.arm')}</td>
                    <td className={tdClass}>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          step="0.01"
                          placeholder={t('checkIns.structural.relaxed')}
                          value={perimeters.arm_relaxed}
                          onChange={(e) => setPerimeters((p) => ({ ...p, arm_relaxed: e.target.value }))}
                          className={`flex-1 ${inputClass}`}
                        />
                        <input
                          type="number"
                          step="0.01"
                          placeholder={t('checkIns.structural.flexed')}
                          value={perimeters.arm_flexed}
                          onChange={(e) => setPerimeters((p) => ({ ...p, arm_flexed: e.target.value }))}
                          className={`flex-1 ${inputClass}`}
                        />
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td className={`${tdClass} bg-gray-50 font-medium`}>{t('checkIns.structural.thigh')}</td>
                    <td className={tdClass}>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          step="0.01"
                          placeholder={t('checkIns.structural.relaxed')}
                          value={perimeters.thigh_relaxed}
                          onChange={(e) => setPerimeters((p) => ({ ...p, thigh_relaxed: e.target.value }))}
                          className={`flex-1 ${inputClass}`}
                        />
                        <input
                          type="number"
                          step="0.01"
                          placeholder={t('checkIns.structural.flexed')}
                          value={perimeters.thigh_flexed}
                          onChange={(e) => setPerimeters((p) => ({ ...p, thigh_flexed: e.target.value }))}
                          className={`flex-1 ${inputClass}`}
                        />
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* F) Retroalimentación */}
            <section className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t('checkIns.structural.feedback')}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('metrics.rpe')}</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={feedback.rpe}
                    onChange={(e) => setFeedback((f) => ({ ...f, rpe: Number(e.target.value) || 0 }))}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('metrics.fatigue')}</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={feedback.fatigue}
                    onChange={(e) => setFeedback((f) => ({ ...f, fatigue: Number(e.target.value) || 0 }))}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('metrics.dietAdherence')}</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={feedback.diet_adherence_pct}
                    onChange={(e) => setFeedback((f) => ({ ...f, diet_adherence_pct: Number(e.target.value) || 0 }))}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('metrics.workoutAdherence')}</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={feedback.training_adherence_pct}
                    onChange={(e) => setFeedback((f) => ({ ...f, training_adherence_pct: Number(e.target.value) || 0 }))}
                    className={inputClass}
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('checkIns.notes')}</label>
                <textarea
                  rows={3}
                  value={feedback.notes}
                  onChange={(e) => setFeedback((f) => ({ ...f, notes: e.target.value }))}
                  className={inputClass}
                  placeholder={t('checkIns.notesPlaceholder')}
                />
              </div>
            </section>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => navigate(`/clients/${clientId}`)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              >
                {isSubmitting ? `${t('checkIns.creating')}...` : t('checkIns.createCheckIn')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
