import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  const [cycles, setCycles] = useState<PlanCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCycles();
  }, []);

  const fetchCycles = async () => {
    try {
      setLoading(true);
      const response = await api.get('/plans/plan-cycles/');
      setCycles(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || t('plans.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = (cycleId: number) => {
    window.open(`/api/plans/plan-cycles/${cycleId}/download-pdf/`, '_blank');
  };

  const handleDeletePlan = async (cycleId: number, clientName: string) => {
    if (!window.confirm(t('plans.deleteConfirm', { name: clientName }))) {
      return;
    }

    try {
      await api.delete(`/plans/plan-cycles/${cycleId}/`);
      await fetchCycles();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || t('plans.deleteFailed');
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('plans.title')}</h1>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {t('plans.subtitle')}
              </p>
            </div>
            <button
              onClick={() => navigate('/plans/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              {t('plans.createNewPlan')}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('plans.client')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('plans.period')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('plans.duration')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('plans.status')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('common.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {cycles.map((cycle) => (
                  <tr key={cycle.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      {cycle.client_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {cycle.start_date} - {cycle.end_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {t('plans.durationDays', { count: cycle.duration_days })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        cycle.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
                        cycle.status === 'draft' ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300' :
                        'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
                      }`}>
                        {t(`status.${cycle.status}` as const)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => navigate(`/plans/${cycle.id}/builder`)}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                          title={t('plans.edit')}
                        >
                          {t('common.edit')}
                        </button>
                        <button
                          onClick={() => handleDownloadPDF(cycle.id)}
                          className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                          title={t('plans.downloadPdf')}
                        >
                          <Download className="h-4 w-4 inline" />
                        </button>
                        <button
                          onClick={() => handleDeletePlan(cycle.id, cycle.client_name)}
                          className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                          title={t('common.delete')}
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
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              {t('plans.noPlans')} {t('plans.noPlansHint')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
