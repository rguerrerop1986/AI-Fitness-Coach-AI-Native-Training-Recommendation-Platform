import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { Plus, Calendar, User, Download, Trash2 } from 'lucide-react';

interface PlanCycle {
  id: number;
  client_name: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  status: string;
  goal: string;
}

export default function Plans() {
  const navigate = useNavigate();
  const [cycles, setCycles] = useState<PlanCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCycles();
  }, []);

  const fetchCycles = async () => {
    try {
      setLoading(true);
      const response = await api.get('/plan-cycles/');
      setCycles(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch plans');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = (cycleId: number) => {
    window.open(`/api/plans/plan-cycles/${cycleId}/download-pdf/`, '_blank');
  };

  const handleDeletePlan = async (cycleId: number, clientName: string) => {
    if (!window.confirm(`Are you sure you want to delete the plan for ${clientName}? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.delete(`/plan-cycles/${cycleId}/`);
      // Refresh the list after deletion
      await fetchCycles();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'Failed to delete plan';
      setError(errorMessage);
      setTimeout(() => setError(null), 5000);
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
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Plans</h1>
              <p className="mt-2 text-sm text-gray-600">
                Create and manage diet and workout plans for clients
              </p>
            </div>
            <button
              onClick={() => navigate('/plans/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create New Plan
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {cycles.map((cycle) => (
                  <tr key={cycle.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {cycle.client_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cycle.start_date} - {cycle.end_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cycle.duration_days} días
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        cycle.status === 'active' ? 'bg-green-100 text-green-800' :
                        cycle.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {cycle.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => navigate(`/plans/${cycle.id}/builder`)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit plan"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDownloadPDF(cycle.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Download PDF"
                        >
                          <Download className="h-4 w-4 inline" />
                        </button>
                        <button
                          onClick={() => handleDeletePlan(cycle.id, cycle.client_name)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete plan"
                        >
                          <Trash2 className="h-4 w-4 inline" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cycles.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No plans found. Click "Create New Plan" to get started.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
