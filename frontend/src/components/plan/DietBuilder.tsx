import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Trash2 } from 'lucide-react';

interface Meal {
  id?: number;
  meal_type: string;
  meal_type_display?: string;
  name: string;
  description: string;
  order: number;
}

interface DietPlan {
  id: number;
  meals: Meal[];
}

const MEAL_TYPES = [
  { value: 'breakfast', label: 'Desayuno' },
  { value: 'pre_workout', label: 'Pre-entreno' },
  { value: 'post_workout', label: 'Post-entreno' },
  { value: 'dinner', label: 'Cena' },
  { value: 'snack', label: 'Snack' },
];

export default function DietBuilder({ cycleId }: { cycleId: number }) {
  const [dietPlan, setDietPlan] = useState<DietPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMealForm, setShowMealForm] = useState(false);
  const [editingMeal, setEditingMeal] = useState<Meal | null>(null);

  useEffect(() => {
    fetchDietPlan();
  }, [cycleId]);

  const fetchDietPlan = async () => {
    try {
      const response = await api.get(`/plan-cycles/${cycleId}/diet-plan/`);
      const plan = response.data as DietPlan;

      // Refrescar meals directamente desde el endpoint de meals para evitar desincronizaciones
      try {
        const mealsResp = await api.get(`/meals/?diet_plan=${plan.id}`);
        const meals = mealsResp.data.results || mealsResp.data;
        plan.meals = Array.isArray(meals) ? meals : [];
        console.log('Fetched meals:', plan.meals);
      } catch (err: any) {
        console.error('Error fetching meals:', err);
        // Si falla por cualquier motivo, usamos lo que venga embebido (si es que viene)
        plan.meals = plan.meals || [];
      }

      setDietPlan(plan);
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Diet plan doesn't exist yet, that's okay
        setDietPlan(null);
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch diet plan');
      }
    }
  };

  const handleCreateDietPlan = async () => {
    try {
      setLoading(true);
      await api.post(`/plan-cycles/${cycleId}/diet-plan/`, {
        title: `Diet Plan for Cycle ${cycleId}`,
      });
      await fetchDietPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create diet plan');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMeal = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const mealData: any = {
      meal_type: formData.get('meal_type'),
      name: formData.get('name') || '',
      description: formData.get('description') || '',
      order: parseInt(formData.get('order') as string) || 0,
    };
    
    // Ensure order is a number, not NaN
    if (isNaN(mealData.order)) {
      mealData.order = 0;
    }
    
    console.log('Sending meal data:', mealData);
    try {
      if (editingMeal && editingMeal.id) {
        await api.patch(`/meals/${editingMeal.id}/`, mealData);
      } else {
        await api.post(`/plan-cycles/${cycleId}/diet-plan/meals/`, mealData);
      }
      setShowMealForm(false);
      setEditingMeal(null);
      await fetchDietPlan();
    } catch (err: any) {
      // Show detailed error message from backend
      console.error('Error response:', err.response?.data);
      if (err.response?.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object') {
          // Show the detail message if available (preferred)
          if (errorData.detail) {
            setError(errorData.detail);
          } else {
            // If it's an object with validation errors, show them
            const errorMessages = Object.entries(errorData)
              .map(([key, value]) => {
                if (Array.isArray(value)) {
                  return `${key}: ${value.join(', ')}`;
                }
                return `${key}: ${value}`;
              })
              .join('\n');
            setError(errorMessages || 'Failed to save meal');
          }
        } else {
          setError(String(errorData));
        }
      } else {
        setError('Failed to save meal');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMeal = async (mealId: number) => {
    if (!confirm('Are you sure you want to delete this meal?')) return;
    try {
      await api.delete(`/meals/${mealId}/`);
      await fetchDietPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete meal');
    }
  };

  const handleEditMeal = (meal: Meal) => {
    setEditingMeal(meal);
    setShowMealForm(true);
  };

  if (!dietPlan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">No diet plan created yet.</p>
        <button
          onClick={handleCreateDietPlan}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Diet Plan
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
        <h2 className="text-xl font-semibold text-gray-900">Meals</h2>
        <button
          onClick={() => {
            setEditingMeal(null);
            setShowMealForm(true);
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Meal
        </button>
      </div>

      {showMealForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-medium mb-4">
            {editingMeal ? 'Edit Meal' : 'Add New Meal'}
          </h3>
          <form onSubmit={handleAddMeal} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meal Type <span className="text-red-500">*</span>
              </label>
              <select
                name="meal_type"
                required
                defaultValue={editingMeal?.meal_type || ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select meal type</option>
                {MEAL_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name (optional)
              </label>
              <input
                type="text"
                name="name"
                defaultValue={editingMeal?.name || ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description <span className="text-red-500">*</span>
              </label>
              <textarea
                name="description"
                required
                rows={3}
                defaultValue={editingMeal?.description || ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., pan tostado con aguacate..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order
              </label>
              <input
                type="number"
                name="order"
                defaultValue={editingMeal?.order || 0}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowMealForm(false);
                  setEditingMeal(null);
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
                {loading ? 'Saving...' : editingMeal ? 'Update' : 'Add Meal'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-4">
        {dietPlan.meals && Array.isArray(dietPlan.meals) && dietPlan.meals.length > 0 ? (
          dietPlan.meals.map(meal => (
            <div key={meal.id} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="text-lg font-medium text-gray-900">
                    {meal.meal_type_display || meal.meal_type}
                  </h4>
                  {meal.name && (
                    <p className="text-sm text-gray-600 mt-1">{meal.name}</p>
                  )}
                  {meal.description && (
                    <p className="text-sm text-gray-700 mt-2">{meal.description}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEditMeal(meal)}
                    className="text-blue-600 hover:text-blue-900 text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => meal.id && handleDeleteMeal(meal.id)}
                    className="text-red-600 hover:text-red-900 text-sm"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-500 text-center py-8">No meals added yet. Click "Add Meal" to get started.</p>
        )}
      </div>
    </div>
  );
}
