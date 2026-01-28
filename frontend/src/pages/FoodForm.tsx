import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Save } from 'lucide-react';

interface Food {
  id?: number;
  name: string;
  brand: string;
  nutritional_group: string | null;
  origin_classification: string | null;
  serving_size: number;
  calories_kcal: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fats_g: number | null;
  fiber_g?: number | null;
  water_g?: number | null;
  creatine_mg?: number | null;
  micronutrients_notes: string;
  notes: string;
}

const NUTRITIONAL_GROUPS = [
  { value: 'cereales_tuberculos_derivados', label: 'Cereales, tubérculos y derivados.' },
  { value: 'frutas_verduras', label: 'Frutas y verduras.' },
  { value: 'leche_derivados', label: 'Leche y derivados.' },
  { value: 'carnes_legumbres_huevos', label: 'Carnes, legumbres secas y huevos.' },
  { value: 'azucares_mieles', label: 'Azúcares o mieles.' },
  { value: 'aceites_grasas', label: 'Aceites o grasas.' },
];

const ORIGIN_CLASSIFICATIONS = [
  { value: 'vegetal', label: 'Vegetal' },
  { value: 'animal', label: 'Animal' },
  { value: 'mineral', label: 'Mineral' },
];

export default function FoodForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<Food>({
    name: '',
    brand: '',
    nutritional_group: '',
    origin_classification: '',
    serving_size: 100.0,
    calories_kcal: null,
    protein_g: null,
    carbs_g: null,
    fats_g: null,
    fiber_g: null,
    water_g: null,
    creatine_mg: null,
    micronutrients_notes: '',
    notes: '',
  });

  // Check if user is coach/assistant
  useEffect(() => {
    if (user && user.role !== 'coach' && user.role !== 'assistant') {
      navigate('/foods');
    }
  }, [user, navigate]);

  useEffect(() => {
    if (id) {
      fetchFood();
    }
  }, [id]);

  const fetchFood = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/foods/${id}/`);
      // Ensure null/undefined values are converted to empty strings for form selects
      const data = response.data;
      setFormData({
        ...data,
        nutritional_group: data.nutritional_group || '',
        origin_classification: data.origin_classification || '',
        calories_kcal: data.calories_kcal ?? null,
        protein_g: data.protein_g ?? null,
        carbs_g: data.carbs_g ?? null,
        fats_g: data.fats_g ?? null,
        fiber_g: data.fiber_g ?? null,
        water_g: data.water_g ?? null,
        creatine_mg: data.creatine_mg ?? null,
      });
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load food');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Clean up the payload - ensure required fields are not empty strings
      const payload: any = {
        name: formData.name.trim(),
        brand: formData.brand?.trim() || '',
        nutritional_group: formData.nutritional_group?.trim() || null,
        origin_classification: formData.origin_classification?.trim() || null,
        serving_size: formData.serving_size || 100.0,
        calories_kcal: formData.calories_kcal ?? null,
        protein_g: formData.protein_g ?? null,
        carbs_g: formData.carbs_g ?? null,
        fats_g: formData.fats_g ?? null,
        micronutrients_notes: formData.micronutrients_notes?.trim() || '',
        notes: formData.notes?.trim() || '',
      };
      
      // Only include optional fields if they have values
      if (formData.fiber_g !== undefined && formData.fiber_g !== null) {
        payload.fiber_g = formData.fiber_g;
      }
      if (formData.water_g !== undefined && formData.water_g !== null) {
        payload.water_g = formData.water_g;
      }
      if (formData.creatine_mg !== undefined && formData.creatine_mg !== null) {
        payload.creatine_mg = formData.creatine_mg;
      }

      if (id) {
        await api.patch(`/foods/${id}/`, payload);
      } else {
        await api.post('/foods/', payload);
      }

      navigate('/foods');
    } catch (err: any) {
      if (err.response?.data) {
        const errors = err.response.data;
        if (typeof errors === 'object') {
          const errorMessages = Object.entries(errors)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('\n');
          setError(errorMessages);
        } else {
          setError(errors);
        }
      } else {
        setError('Failed to save food');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    const numericFields = new Set([
      'serving_size',
      'calories_kcal',
      'protein_g',
      'carbs_g',
      'fats_g',
      'fiber_g',
      'water_g',
      'creatine_mg',
    ]);

    setFormData(prev => ({
      ...prev,
      [name]: numericFields.has(name)
        ? (value === '' ? null : parseFloat(value))
        : value,
    }));
  };

  if (loading && id) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/foods')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Foods
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {id ? 'Edit Food' : 'Create New Food'}
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Add or update food nutritional information (per 100g)
          </p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            <pre className="whitespace-pre-wrap text-sm">{error}</pre>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
          {/* Basic Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Food Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Brand (optional)
                </label>
                <input
                  type="text"
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Classification */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Classification</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nutritional Group <span className="text-red-500">*</span>
                </label>
                <select
                  name="nutritional_group"
                  required
                  value={formData.nutritional_group || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a group</option>
                  {NUTRITIONAL_GROUPS.map(group => (
                    <option key={group.value} value={group.value}>
                      {group.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Origin Classification <span className="text-red-500">*</span>
                </label>
                <select
                  name="origin_classification"
                  required
                  value={formData.origin_classification || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select origin</option>
                  {ORIGIN_CLASSIFICATIONS.map(origin => (
                    <option key={origin.value} value={origin.value}>
                      {origin.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Macronutrients */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Macronutrients (per 100g)</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Calories (kcal) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="calories_kcal"
                  required
                  min="0"
                  step="0.1"
                  value={formData.calories_kcal ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Protein (g) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="protein_g"
                  required
                  min="0"
                  step="0.1"
                  value={formData.protein_g ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Carbs (g) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="carbs_g"
                  required
                  min="0"
                  step="0.1"
                  value={formData.carbs_g ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fats (g) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="fats_g"
                  required
                  min="0"
                  step="0.1"
                  value={formData.fats_g ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Optional Nutrition */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Optional Nutrition (per 100g)</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fiber (g)
                </label>
                <input
                  type="number"
                  name="fiber_g"
                  min="0"
                  step="0.1"
                  value={formData.fiber_g ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Water (g)
                </label>
                <input
                  type="number"
                  name="water_g"
                  min="0"
                  step="0.1"
                  value={formData.water_g ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Creatine (mg)
                </label>
                <input
                  type="number"
                  name="creatine_mg"
                  min="0"
                  step="0.01"
                  value={formData.creatine_mg ?? ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Notes</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Micronutrients Notes
                </label>
                <textarea
                  name="micronutrients_notes"
                  rows={3}
                  value={formData.micronutrients_notes}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Notes about micronutrients..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  General Notes
                </label>
                <textarea
                  name="notes"
                  rows={3}
                  value={formData.notes}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="General notes, sources, remarks..."
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => navigate('/foods')}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Saving...' : id ? 'Update Food' : 'Create Food'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
