import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';
import { Download, Moon, Sun, Dumbbell, CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react';

interface Meal {
  id: number;
  meal_type: string;
  meal_type_display: string;
  name: string;
  description: string;
}

interface TrainingEntry {
  id: number;
  exercise_detail: {
    id: number;
    name: string;
    muscle_group_display: string;
  };
  date: string;
  series: number;
  repetitions: string;
  weight_kg?: number;
  rest_seconds?: number;
  notes?: string;
}

interface PlanData {
  id: number;
  start_date: string;
  end_date: string;
  duration_days: number;
  goal: string;
  diet_plan_data: {
    id: number;
    title: string;
    meals: Meal[];
  } | null;
  workout_plan_data: {
    id: number;
    title: string;
    training_entries: TrainingEntry[];
  } | null;
}

interface DailyRecommendation {
  id: number;
  date: string;
  intensity: string;
  type: string;
  rationale: string;
  status: string;
  exercise_name: string;
  exercise_instructions: string;
  exercise_video_url: string;
  exercise_image_url: string;
  exercise_equipment: string;
  duration_minutes: number;
  warning: string | null;
  exercise?: number;
}

interface ProgressionUpdate {
  outcome_score: number;
  flags: string[];
  intensity_bias_before: number;
  intensity_bias_after: number;
  message: string;
}

export default function ClientPlan() {
  const navigate = useNavigate();
  const { t, i18n: i18nInstance } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [dailyRec, setDailyRec] = useState<DailyRecommendation | null>(null);
  const [dailyRecLoading, setDailyRecLoading] = useState(true);
  const [completingId, setCompletingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [completingRecId, setCompletingRecId] = useState<number | null>(null);
  const [progressionMessage, setProgressionMessage] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [postWorkoutForm, setPostWorkoutForm] = useState({
    rpe: 5,
    energy_level: 6,
    pain_level: 0,
    notes: '',
    executed_exercise_id: null as number | null,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setLoading(true);
    setDailyRecLoading(true);
    let done = 0;
    const maybeDone = () => {
      done += 1;
      if (done === 2) setLoading(false);
    };
    api.get('/client/me/daily-exercise/')
      .then((r) => setDailyRec(r.data))
      .catch(() => setDailyRec(null))
      .finally(() => { setDailyRecLoading(false); maybeDone(); });
    api.get('/client/current-plan/')
      .then((r) => { setPlan(r.data); setPlanError(null); })
      .catch(() => { setPlan(null); setPlanError(t('clientPortal.noPublishedPlan')); })
      .finally(maybeDone);
  }, [t]);

  const fetchPlan = async () => {
    try {
      setLoading(true);
      setPlanError(null);
      const response = await api.get('/client/current-plan/');
      setPlan(response.data);
    } catch (err: any) {
      const msg = err.response?.data?.error || (err.response?.status === 404 ? t('clientPortal.noPublishedPlan') : t('clientPortal.noActivePlan'));
      setPlanError(msg);
      setPlan(null);
    } finally {
      setLoading(false);
    }
  };

  const openCompleteModal = (id: number) => {
    setCompletingRecId(id);
    setPostWorkoutForm({ rpe: 5, energy_level: 6, pain_level: 0, notes: '', executed_exercise_id: null });
    setFormErrors({});
    setProgressionMessage(null);
    setShowCompleteModal(true);
  };

  const handlePostWorkoutSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (completingRecId == null) return;
    const { rpe, energy_level, pain_level, notes, executed_exercise_id } = postWorkoutForm;
    const err: Record<string, string> = {};
    if (rpe < 1 || rpe > 10) err.rpe = 'RPE debe ser entre 1 y 10';
    if (energy_level < 1 || energy_level > 10) err.energy_level = 'Energía debe ser entre 1 y 10';
    if (pain_level < 0 || pain_level > 10) err.pain_level = 'Dolor debe ser entre 0 y 10';
    if (Object.keys(err).length) {
      setFormErrors(err);
      return;
    }
    setFormErrors({});
    try {
      setCompletingId(completingRecId);
      const body: { rpe: number; energy_level: number; pain_level: number; notes?: string; executed_exercise_id?: number } = {
        rpe,
        energy_level,
        pain_level,
        notes: notes || undefined,
      };
      if (executed_exercise_id != null) body.executed_exercise_id = executed_exercise_id;
      const res = await api.post(`/client/me/daily-exercise/${completingRecId}/complete/`, body);
      setDailyRec(res.data.recommendation);
      setProgressionMessage(res.data.progression_update?.message ?? null);
      setShowCompleteModal(false);
      setCompletingRecId(null);
    } catch (err: any) {
      const msg = err.response?.data?.rpe?.[0] ?? err.response?.data?.energy_level?.[0] ?? err.response?.data?.pain_level?.[0] ?? err.response?.data?.error ?? t('clientPortal.downloadPdfFailed');
      setFormErrors({ submit: typeof msg === 'string' ? msg : JSON.stringify(msg) });
    } finally {
      setCompletingId(null);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const url = '/client/current-plan/pdf/';
      const fallbackName = plan
        ? `Plan_${plan.start_date}_${plan.end_date}.pdf`
        : 'MiPlanActual.pdf';

      const res = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const blobUrl = window.URL.createObjectURL(blob);

      let filename = fallbackName;
      const disposition =
        (res.headers && (res.headers['content-disposition'] || res.headers['Content-Disposition'])) || '';
      if (disposition) {
        const match = /filename=\"?([^\";]+)\"?/i.exec(disposition);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      setDownloadError(err.response?.data?.error || t('clientPortal.downloadPdfFailed'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
          </div>
        </div>
      </div>
    );
  }

  const isNoPlan = !plan && (planError === t('clientPortal.noPublishedPlan') || planError?.includes('published'));
  const showPlanContent = plan || isNoPlan;
  if (loading && !dailyRec && !showPlanContent) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
          </div>
        </div>
      </div>
    );
  }
  if (!showPlanContent && planError && !isNoPlan) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded">
            {planError}
          </div>
        </div>
      </div>
    );
  }

  const entriesByDate = plan?.workout_plan_data?.training_entries?.reduce((acc, entry) => {
    const d = entry.date;
    if (!acc[d]) acc[d] = [];
    acc[d].push(entry);
    return acc;
  }, {} as Record<string, TrainingEntry[]>) || {};

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Return to dashboard */}
        <button
          type="button"
          onClick={() => navigate('/client/dashboard')}
          className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 rounded"
        >
          <ArrowLeft className="h-4 w-4" />
          {t('clientPortal.returnToDashboard')}
        </button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('clientPortal.myCurrentPlan')}</h1>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {plan ? `${plan.start_date} - ${plan.end_date} • ${plan.duration_days} ${t('plans.daysLabel')}` : t('clientPortal.contactCoach')}
              </p>
            </div>
            <div className="flex items-center gap-x-3">
              <div className="flex rounded-md border border-gray-300 dark:border-gray-600 overflow-hidden">
                <button
                  type="button"
                  onClick={() => { i18nInstance.changeLanguage('es'); localStorage.setItem('language', 'es'); }}
                  className={`px-2 py-1 text-sm font-medium ${i18nInstance.language?.startsWith('es') ? 'bg-primary-600 text-white dark:bg-primary-500' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                >
                  ES
                </button>
                <button
                  type="button"
                  onClick={() => { i18nInstance.changeLanguage('en'); localStorage.setItem('language', 'en'); }}
                  className={`px-2 py-1 text-sm font-medium ${i18nInstance.language?.startsWith('en') ? 'bg-primary-600 text-white dark:bg-primary-500' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                >
                  EN
                </button>
              </div>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                title={theme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')}
              >
                {theme === 'dark' ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>
              <button
                onClick={handleDownloadPDF}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
              >
                <Download className="h-5 w-5 mr-2" />
                {t('clientPortal.downloadPdfButton')}
              </button>
            </div>
          </div>
        </div>

        {/* Daily exercise recommendation */}
        {dailyRecLoading ? (
          <div className="mb-8 bg-white dark:bg-gray-800 shadow rounded-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-2" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          </div>
        ) : dailyRec ? (
          <div className="mb-8 bg-white dark:bg-gray-800 shadow rounded-lg p-6 border-l-4 border-primary-500">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1 flex items-center gap-2">
              <Dumbbell className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              Recomendación de hoy
            </h2>
            {dailyRec.date && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{dailyRec.date}</p>
            )}
            <div className="space-y-3">
              <p className="font-medium text-gray-900 dark:text-gray-100">{dailyRec.exercise_name}</p>
              <div className="flex flex-wrap gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span className="capitalize">{dailyRec.type}</span>
                <span>•</span>
                <span className="capitalize">{dailyRec.intensity}</span>
                <span>•</span>
                <span>{dailyRec.duration_minutes} min</span>
                {dailyRec.exercise_equipment && (
                  <>
                    <span>•</span>
                    <span>{dailyRec.exercise_equipment}</span>
                  </>
                )}
              </div>
              {dailyRec.rationale && (
                <p className="text-sm text-gray-700 dark:text-gray-300 italic whitespace-pre-wrap break-words">
                  <span>Por tu registro:</span>
                  {'\n'}
                  {dailyRec.rationale}
                </p>
              )}
              {dailyRec.warning && (
                <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded text-amber-800 dark:text-amber-200 text-sm">
                  <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <span>{dailyRec.warning}</span>
                </div>
              )}
              {dailyRec.exercise_instructions && (
                <p className="text-sm text-gray-600 dark:text-gray-400">{dailyRec.exercise_instructions}</p>
              )}
            </div>
            {progressionMessage && (
              <div className="mt-3 p-3 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded text-primary-800 dark:text-primary-200 text-sm">
                <strong>Impacto en progresión:</strong> {progressionMessage}
              </div>
            )}
            <div className="mt-4 flex gap-3">
              {dailyRec.status !== 'completed' && (
                <button
                  type="button"
                  onClick={() => openCompleteModal(dailyRec.id)}
                  disabled={completingId === dailyRec.id}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 disabled:opacity-50"
                >
                  {completingId === dailyRec.id ? (
                    <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  ) : (
                    <CheckCircle className="h-5 w-5 mr-2" />
                  )}
                  Marcar como completado
                </button>
              )}
              {dailyRec.status === 'completed' && (
                <span className="inline-flex items-center text-sm text-green-600 dark:text-green-400">
                  <CheckCircle className="h-5 w-5 mr-1" />
                  Completado
                </span>
              )}
            </div>
          </div>
        ) : null}

        {/* Post-entreno modal */}
        {showCompleteModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto" aria-modal="true">
            <div className="flex min-h-full items-center justify-center p-4">
              <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setShowCompleteModal(false)} />
              <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Post-entreno</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">Indica cómo te sentiste para ajustar tu progresión.</p>
                <form onSubmit={handlePostWorkoutSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">RPE (1–10) <span className="text-gray-500">esfuerzo percibido</span></label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={postWorkoutForm.rpe}
                      onChange={(e) => setPostWorkoutForm((f) => ({ ...f, rpe: parseInt(e.target.value, 10) || 0 }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                    />
                    {formErrors.rpe && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{formErrors.rpe}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Energía (1–10)</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={postWorkoutForm.energy_level}
                      onChange={(e) => setPostWorkoutForm((f) => ({ ...f, energy_level: parseInt(e.target.value, 10) || 0 }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                    />
                    {formErrors.energy_level && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{formErrors.energy_level}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dolor (0–10)</label>
                    <input
                      type="number"
                      min={0}
                      max={10}
                      value={postWorkoutForm.pain_level}
                      onChange={(e) => setPostWorkoutForm((f) => ({ ...f, pain_level: parseInt(e.target.value, 10) || 0 }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                    />
                    {formErrors.pain_level && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{formErrors.pain_level}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notas (opcional)</label>
                    <textarea
                      rows={2}
                      value={postWorkoutForm.notes}
                      onChange={(e) => setPostWorkoutForm((f) => ({ ...f, notes: e.target.value }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                      placeholder="Comentarios..."
                    />
                  </div>
                  {formErrors.submit && <p className="text-sm text-red-600 dark:text-red-400">{formErrors.submit}</p>}
                  <div className="flex gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowCompleteModal(false)}
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={completingId !== null}
                      className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white rounded-md disabled:opacity-50"
                    >
                      {completingId !== null ? (
                        <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent inline-block" />
                      ) : (
                        'Enviar'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Diet Plan */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{t('clientPortal.nutritionPlan')}</h2>
            {plan?.diet_plan_data && plan.diet_plan_data.meals.length > 0 ? (
              <div className="space-y-4">
                {plan.diet_plan_data.meals.map(meal => (
                  <div key={meal.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100">{meal.meal_type_display}</h3>
                    {meal.name && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{meal.name}</p>
                    )}
                    {meal.description && (
                      <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">{meal.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : isNoPlan ? (
              <p className="text-gray-500 dark:text-gray-400">{t('clientPortal.noPublishedPlan')}</p>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">{t('plans.noMeals')}</p>
            )}
          </div>

          {/* Workout Plan */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{t('clientPortal.trainingPlan')}</h2>
            {isNoPlan ? (
              <p className="text-gray-500 dark:text-gray-400">{t('clientPortal.contactCoach')}</p>
            ) : Object.keys(entriesByDate).length > 0 ? (
              <div className="space-y-6">
                {Object.entries(entriesByDate)
                  .sort()
                  .map(([date, entries]) => (
                    <div key={date}>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">{date}</h3>
                      <div className="space-y-3">
                        {entries.map(entry => (
                          <div key={entry.id} className="bg-gray-50 dark:bg-gray-700 rounded p-3">
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                              {entry.exercise_detail.name}
                            </h4>
                            <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1">
                              <p>{t('clientPortal.series')}: {entry.series}</p>
                              <p>{t('clientPortal.reps')}: {entry.repetitions}</p>
                              {entry.weight_kg && <p>{t('clientPortal.weight')}: {entry.weight_kg} kg</p>}
                              {entry.rest_seconds && <p>{t('clientPortal.rest')}: {entry.rest_seconds}s</p>}
                              {entry.notes && (
                              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                                {entry.notes}
                              </p>
                            )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">{t('plans.noExercises')}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
