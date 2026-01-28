import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Download, FileText, Calendar, User } from 'lucide-react';
import { DietBuilder, WorkoutBuilder } from '../components/plan';

interface Client {
  id: number;
  full_name: string;
}

interface PlanCycle {
  id: number;
  client: number;
  client_name: string;
  start_date: string;
  end_date: string;
  cadence: string;
  goal: string;
  status: string;
  duration_days: number;
  diet_plan?: any;
  workout_plan?: any;
}

export default function PlanBuilder() {
  const navigate = useNavigate();
  const { cycleId } = useParams<{ cycleId: string }>();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [cycle, setCycle] = useState<PlanCycle | null>(null);
  const [activeTab, setActiveTab] = useState<'diet' | 'workout'>('diet');

  useEffect(() => {
    fetchClients();
    if (cycleId) {
      fetchCycle();
    }
  }, [cycleId]);

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients/');
      setClients(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch clients');
    }
  };

  const fetchCycle = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/plan-cycles/${cycleId}/`);
      setCycle(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch cycle');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCycle = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const clientId = formData.get('client_id');
    const periodDays = formData.get('period_days');
    const goal = formData.get('goal');

    try {
      const data: any = {
        client: parseInt(clientId as string),
        period_days: parseInt(periodDays as string),
        status: 'draft',
      };

      // Only include goal if it's not empty
      if (goal && goal !== '') {
        data.goal = goal;
      }

      const response = await api.post('/plan-cycles/', data);
      navigate(`/plans/${response.data.id}/builder`);
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
        setError('Failed to create plan cycle');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    if (!cycleId) return;
    try {
      setLoading(true);
      await api.post(`/plan-cycles/${cycleId}/generate-pdf/`);
      alert('PDF generated successfully!');
      fetchCycle();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to generate PDF');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    if (!cycleId) return;
    window.open(`/api/plans/plan-cycles/${cycleId}/download-pdf/`, '_blank');
  };

  if (cycleId && !cycle) {
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

  if (cycleId && cycle) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Plan Builder</h1>
                <p className="mt-2 text-sm text-gray-600">
                  {cycle.client_name} • {cycle.duration_days} días • {cycle.start_date} - {cycle.end_date}
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleGeneratePDF}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  <FileText className="h-5 w-5 mr-2" />
                  Generar PDF
                </button>
                {cycle.plan_pdf && (
                  <button
                    onClick={handleDownloadPDF}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <Download className="h-5 w-5 mr-2" />
                    Descargar PDF
                  </button>
                )}
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white shadow rounded-lg">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex">
                <button
                  onClick={() => setActiveTab('diet')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'diet'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Plan de Nutrición
                </button>
                <button
                  onClick={() => setActiveTab('workout')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'workout'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Plan de Entrenamiento
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'diet' && <DietBuilder cycleId={parseInt(cycleId!)} />}
              {activeTab === 'workout' && <WorkoutBuilder cycleId={parseInt(cycleId!)} />}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Create new cycle form
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Create New Plan</h1>
          <p className="mt-2 text-sm text-gray-600">
            Create a new diet and workout plan for a client
          </p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            <pre className="whitespace-pre-wrap text-sm">{error}</pre>
          </div>
        )}

        <form onSubmit={handleCreateCycle} className="bg-white shadow rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client <span className="text-red-500">*</span>
            </label>
            <select
              name="client_id"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a client</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.full_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Period (days) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="period_days"
              required
              min="1"
              defaultValue="15"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Goal (optional)
            </label>
            <select
              name="goal"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select goal</option>
              <option value="fat_loss">Fat Loss</option>
              <option value="recomp">Recomposition</option>
              <option value="muscle_gain">Muscle Gain</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => navigate('/plans')}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              <Plus className="h-4 w-4 mr-2" />
              {loading ? 'Creating...' : 'Create Plan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
