import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Download, Calendar, FileText } from 'lucide-react';

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

  const handleDownloadPDF = () => {
    window.open('/api/client/current-plan/pdf/', '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
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
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Mi Plan Actual</h1>
              <p className="mt-2 text-sm text-gray-600">
                {plan.start_date} - {plan.end_date} • {plan.duration_days} días
              </p>
            </div>
            <button
              onClick={handleDownloadPDF}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Download className="h-5 w-5 mr-2" />
              Descargar PDF
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Diet Plan */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Plan de Nutrición</h2>
            {plan.diet_plan_data && plan.diet_plan_data.meals.length > 0 ? (
              <div className="space-y-4">
                {plan.diet_plan_data.meals.map(meal => (
                  <div key={meal.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900">{meal.meal_type_display}</h3>
                    {meal.name && (
                      <p className="text-sm text-gray-600 mt-1">{meal.name}</p>
                    )}
                    {meal.description && (
                      <p className="text-sm text-gray-700 mt-2">{meal.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No hay comidas definidas en este plan.</p>
            )}
          </div>

          {/* Workout Plan */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Plan de Entrenamiento</h2>
            {Object.keys(entriesByDate).length > 0 ? (
              <div className="space-y-6">
                {Object.entries(entriesByDate)
                  .sort()
                  .map(([date, entries]) => (
                    <div key={date}>
                      <h3 className="font-medium text-gray-900 mb-3">{date}</h3>
                      <div className="space-y-3">
                        {entries.map(entry => (
                          <div key={entry.id} className="bg-gray-50 rounded p-3">
                            <h4 className="font-medium text-gray-900">
                              {entry.exercise_detail.name}
                            </h4>
                            <div className="mt-2 text-sm text-gray-600 space-y-1">
                              <p>Series: {entry.series}</p>
                              <p>Reps: {entry.repetitions}</p>
                              {entry.weight_kg && <p>Peso: {entry.weight_kg} kg</p>}
                              {entry.rest_seconds && <p>Descanso: {entry.rest_seconds}s</p>}
                              {entry.notes && <p className="text-gray-700">{entry.notes}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-gray-500">No hay ejercicios definidos en este plan.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
