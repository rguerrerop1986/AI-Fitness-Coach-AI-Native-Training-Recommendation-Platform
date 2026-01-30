import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Trash2 } from 'lucide-react';

interface Exercise {
  id: number;
  name: string;
  muscle_group_display: string;
}

interface TrainingEntry {
  id?: number;
  exercise: number;
  exercise_detail?: Exercise;
  date: string;
  series: number;
  repetitions: string;
  weight_kg?: number;
  rest_seconds?: number;
  notes?: string;
}

interface WorkoutPlan {
  id: number;
  training_entries: TrainingEntry[];
}

export default function WorkoutBuilder({ cycleId }: { cycleId: number }) {
  const [workoutPlan, setWorkoutPlan] = useState<WorkoutPlan | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showEntryForm, setShowEntryForm] = useState(false);
  const [editingEntry, setEditingEntry] = useState<TrainingEntry | null>(null);

  useEffect(() => {
    fetchWorkoutPlan();
    fetchExercises();
  }, [cycleId]);

  const fetchWorkoutPlan = async () => {
    try {
      const response = await api.get(`/plans/plan-cycles/${cycleId}/workout-plan/`);
      setWorkoutPlan(response.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setWorkoutPlan(null);
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch workout plan');
      }
    }
  };

  const fetchExercises = async () => {
    try {
      const response = await api.get('/exercises/');
      setExercises(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch exercises');
    }
  };

  const handleCreateWorkoutPlan = async () => {
    try {
      setLoading(true);
      await api.post(`/plans/plan-cycles/${cycleId}/workout-plan/`, {
        title: `Workout Plan for Cycle ${cycleId}`,
      });
      await fetchWorkoutPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create workout plan');
    } finally {
      setLoading(false);
    }
  };

  const handleAddEntry = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const entryData: any = {
      workout_plan: workoutPlan!.id,
      exercise: parseInt(formData.get('exercise') as string),
      date: formData.get('date'),
      series: parseInt(formData.get('series') as string),
      repetitions: formData.get('repetitions'),
    };

    const weight_kg = formData.get('weight_kg');
    if (weight_kg) {
      entryData.weight_kg = parseFloat(weight_kg as string);
    }

    const rest_seconds = formData.get('rest_seconds');
    if (rest_seconds) {
      entryData.rest_seconds = parseInt(rest_seconds as string);
    }

    const notes = formData.get('notes');
    if (notes) {
      entryData.notes = notes;
    }

    try {
      if (editingEntry && editingEntry.id) {
        await api.patch(`/plans/training-entries/${editingEntry.id}/`, entryData);
      } else {
        await api.post('/plans/training-entries/', entryData);
      }
      setShowEntryForm(false);
      setEditingEntry(null);
      await fetchWorkoutPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save training entry');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEntry = async (entryId: number) => {
    if (!confirm('Are you sure you want to delete this training entry?')) return;
    try {
      await api.delete(`/plans/training-entries/${entryId}/`);
      await fetchWorkoutPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete entry');
    }
  };

  const handleEditEntry = (entry: TrainingEntry) => {
    setEditingEntry(entry);
    setShowEntryForm(true);
  };

  // Group entries by date
  const entriesByDate = workoutPlan?.training_entries.reduce((acc, entry) => {
    const date = entry.date;
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(entry);
    return acc;
  }, {} as Record<string, TrainingEntry[]>) || {};

  if (!workoutPlan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">No workout plan created yet.</p>
        <button
          onClick={handleCreateWorkoutPlan}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Workout Plan
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Training Entries</h2>
        <button
          onClick={() => {
            setEditingEntry(null);
            setShowEntryForm(true);
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Exercise
        </button>
      </div>

      {showEntryForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-medium mb-4">
            {editingEntry ? 'Edit Training Entry' : 'Add New Training Entry'}
          </h3>
          <form onSubmit={handleAddEntry} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Exercise <span className="text-red-500">*</span>
                </label>
                <select
                  name="exercise"
                  required
                  defaultValue={editingEntry?.exercise || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select exercise</option>
                  {exercises.map(ex => (
                    <option key={ex.id} value={ex.id}>
                      {ex.name} ({ex.muscle_group_display})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="date"
                  required
                  defaultValue={editingEntry?.date || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Series <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="series"
                  required
                  min="1"
                  defaultValue={editingEntry?.series || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Repetitions <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="repetitions"
                  required
                  defaultValue={editingEntry?.repetitions || ''}
                  placeholder="e.g., 8-12 or 10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Weight (kg) (optional)
                </label>
                <input
                  type="number"
                  name="weight_kg"
                  step="0.1"
                  min="0"
                  defaultValue={editingEntry?.weight_kg || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rest (seconds) (optional)
                </label>
                <input
                  type="number"
                  name="rest_seconds"
                  min="0"
                  defaultValue={editingEntry?.rest_seconds || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (optional)
              </label>
              <textarea
                name="notes"
                rows={3}
                defaultValue={editingEntry?.notes || ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowEntryForm(false);
                  setEditingEntry(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Saving...' : editingEntry ? 'Update' : 'Add Entry'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-6">
        {Object.keys(entriesByDate).length > 0 ? (
          Object.entries(entriesByDate)
            .sort()
            .map(([date, entries]) => (
              <div key={date} className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{date}</h3>
                <div className="space-y-3">
                  {entries.map(entry => (
                    <div key={entry.id} className="bg-gray-50 rounded p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">
                            {entry.exercise_detail?.name || `Exercise ${entry.exercise}`}
                          </h4>
                          <div className="mt-2 text-sm text-gray-600 space-y-1">
                            <p>Series: {entry.series}</p>
                            <p>Reps: {entry.repetitions}</p>
                            {entry.weight_kg && <p>Weight: {entry.weight_kg} kg</p>}
                            {entry.rest_seconds && <p>Rest: {entry.rest_seconds}s</p>}
                            {entry.notes && <p className="text-gray-700">{entry.notes}</p>}
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditEntry(entry)}
                            className="text-blue-600 hover:text-blue-900 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => entry.id && handleDeleteEntry(entry.id)}
                            className="text-red-600 hover:text-red-900 text-sm"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
        ) : (
          <p className="text-gray-500 text-center py-8">
            No training entries added yet. Click "Add Exercise" to get started.
          </p>
        )}
      </div>
    </div>
  );
}
