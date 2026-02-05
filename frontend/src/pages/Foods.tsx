import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search } from 'lucide-react';

interface Food {
  id: number;
  name: string;
  brand: string;
  nutritional_group: string;
  nutritional_group_display: string;
  origin_classification: string;
  origin_classification_display: string;
  calories_kcal: number | string | null;
  protein_g: number | string | null;
  carbs_g: number | string | null;
  fats_g: number | string | null;
  fiber_g?: number | string | null;
  water_g?: number | string | null;
  creatine_mg?: number | string | null;
  is_active: boolean;
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

export default function Foods() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [foods, setFoods] = useState<Food[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterNutritionalGroup, setFilterNutritionalGroup] = useState('');
  const [filterOrigin, setFilterOrigin] = useState('');

  const isCoach = user?.role === 'coach' || user?.role === 'assistant';

  useEffect(() => {
    fetchFoods();
  }, [filterNutritionalGroup, filterOrigin]);

  const fetchFoods = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterNutritionalGroup) {
        params.append('nutritional_group', filterNutritionalGroup);
      }
      if (filterOrigin) {
        params.append('origin_classification', filterOrigin);
      }
      if (searchQuery) {
        params.append('search', searchQuery);
      }

      const response = await api.get(`/foods/?${params.toString()}`);
      const foodsData = response.data.results || response.data;
      // Ensure numeric fields are properly converted from strings
      const processedFoods = (Array.isArray(foodsData) ? foodsData : []).map((food: any) => ({
        ...food,
        calories_kcal: food.calories_kcal != null ? Number(food.calories_kcal) : null,
        protein_g: food.protein_g != null ? Number(food.protein_g) : null,
        carbs_g: food.carbs_g != null ? Number(food.carbs_g) : null,
        fats_g: food.fats_g != null ? Number(food.fats_g) : null,
        fiber_g: food.fiber_g != null ? Number(food.fiber_g) : null,
        water_g: food.water_g != null ? Number(food.water_g) : null,
        creatine_mg: food.creatine_mg != null ? Number(food.creatine_mg) : null,
      }));
      setFoods(processedFoods);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch foods');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFoods();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this food?')) return;
    try {
      await api.delete(`/foods/${id}/`);
      fetchFoods();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete food');
    }
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

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Food Catalog</h1>
              <p className="mt-2 text-sm text-gray-600">
                Manage your food database with complete nutritional information
              </p>
            </div>
            {isCoach && (
              <button
                onClick={() => navigate('/foods/new')}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-5 w-5 mr-2" />
                Add Food
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white shadow rounded-lg p-4 mb-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by name or brand..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <select
                  value={filterNutritionalGroup}
                  onChange={(e) => setFilterNutritionalGroup(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Nutritional Groups</option>
                  {NUTRITIONAL_GROUPS.map(group => (
                    <option key={group.value} value={group.value}>
                      {group.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <select
                  value={filterOrigin}
                  onChange={(e) => setFilterOrigin(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Origins</option>
                  {ORIGIN_CLASSIFICATIONS.map(origin => (
                    <option key={origin.value} value={origin.value}>
                      {origin.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button
              type="submit"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Search className="h-4 w-4 mr-2" />
              Search
            </button>
          </form>
        </div>

        {/* Foods Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nutritional Group
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Origin
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Calories
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Protein
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Carbs
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fats
                  </th>
                  {isCoach && (
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {foods.map((food) => (
                  <tr key={food.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{food.name}</div>
                      {food.brand && (
                        <div className="text-sm text-gray-500">{food.brand}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {food.nutritional_group_display || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {food.origin_classification_display || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {food.calories_kcal != null ? Number(food.calories_kcal).toFixed(1) : '-'} kcal
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {food.protein_g != null ? Number(food.protein_g).toFixed(1) : '-'} g
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {food.carbs_g != null ? Number(food.carbs_g).toFixed(1) : '-'} g
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {food.fats_g != null ? Number(food.fats_g).toFixed(1) : '-'} g
                    </td>
                    {isCoach && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => navigate(`/foods/${food.id}/edit`)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(food.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {foods.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No foods found. {isCoach && 'Click "Add Food" to create one.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
