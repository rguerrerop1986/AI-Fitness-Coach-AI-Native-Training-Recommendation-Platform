import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';
import { Download, Calendar, FileText, Moon, Sun } from 'lucide-react';

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

export default function ClientPlan() {
  const { theme, toggleTheme } = useTheme();
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPlan();
  }, []);

  const fetchPlan = async () => {
    try {
      setLoading(true);
      const response = await api.get('/client/current-plan/');
      setPlan(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch plan');
    } finally {
      setLoading(false);
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
      setError(err.response?.data?.error || 'Failed to download PDF');
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

  if (error || !plan) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded">
            {error || 'No active plan found. Contact your coach.'}
          </div>
        </div>
      </div>
    );
  }

  // Group training entries by date
  const entriesByDate = plan.workout_plan_data?.training_entries.reduce((acc, entry) => {
    const date = entry.date;
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(entry);
    return acc;
  }, {} as Record<string, TrainingEntry[]>) || {};

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Mi Plan Actual</h1>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {plan.start_date} - {plan.end_date} • {plan.duration_days} días
              </p>
            </div>
            <div className="flex items-center gap-x-3">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                title={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
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
                Descargar PDF
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Diet Plan */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Plan de Nutrición</h2>
            {plan.diet_plan_data && plan.diet_plan_data.meals.length > 0 ? (
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
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No hay comidas definidas en este plan.</p>
            )}
          </div>

          {/* Workout Plan */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Plan de Entrenamiento</h2>
            {Object.keys(entriesByDate).length > 0 ? (
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
                              <p>Series: {entry.series}</p>
                              <p>Reps: {entry.repetitions}</p>
                              {entry.weight_kg && <p>Peso: {entry.weight_kg} kg</p>}
                              {entry.rest_seconds && <p>Descanso: {entry.rest_seconds}s</p>}
                              {entry.notes && <p className="text-gray-700 dark:text-gray-300">{entry.notes}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No hay ejercicios definidos en este plan.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
