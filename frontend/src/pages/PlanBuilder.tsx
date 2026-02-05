import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-hot-toast';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Download, FileText } from 'lucide-react';
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
  plan_pdf?: string | null;
  diet_plan?: any;
  workout_plan?: any;
  has_diet_plan?: boolean;
  has_workout_plan?: boolean;
  can_publish?: boolean;
}

export default function PlanBuilder() {
  const navigate = useNavigate();
  const { cycleId } = useParams<{ cycleId: string }>();
  const [searchParams] = useSearchParams();
  const preselectedClientId = searchParams.get('client') || '';
  useAuth();
  const { t } = useTranslation();
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
      setError(err.response?.data?.message || t('errors.failedToFetch'));
    }
  };

  const fetchCycle = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/plans/plan-cycles/${cycleId}/`);
      setCycle(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || t('errors.failedToFetch'));
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

      const response = await api.post('/plans/plan-cycles/', data);
      navigate(`/plans/${response.data.id}/builder`);
    } catch (err: any) {
      if (err.response?.status === 409) {
        const detail = err.response?.data?.detail || 'El cliente está inactivo. No se pueden crear planes.';
        toast.error(detail);
        if (clientId) navigate(`/clients/${clientId}`);
        return;
      }
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
        setError(t('errors.failedToCreate'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    if (!cycleId) return;
    try {
      setLoading(true);
      // Backend route is /api/plan-cycles/<pk>/generate-pdf/
      // Our axios client already prefixes with /api, so we use /plan-cycles/ here.
      await api.post(`/plans/plan-cycles/${cycleId}/generate-pdf/`);
      console.log('PDF generated successfully!');
      
      // PDF generated - UI will show download button
      fetchCycle();
    } catch (err: any) {
      setError(err.response?.data?.error || t('plans.generatePdf'));
    } finally {
      setLoading(false);
    }
  };

  const setPlanStatus = async (newStatus: 'saved' | 'published') => {
    if (!cycleId) return;
    try {
      setError(null);
      setLoading(true);
      await api.post(`/plans/plan-cycles/${cycleId}/set-status/`, { status: newStatus });
      await fetchCycle();
    } catch (err: any) {
      const msg = err.response?.data?.error || err.response?.data?.detail || t('errors.failedToUpdate');
      setError(Array.isArray(msg) ? msg.join(' ') : msg);
    } finally {
      setLoading(false);
    }
  };

  const statusLabel = (s: string) => {
    if (s === 'draft') return t('plans.statusDraft');
    if (s === 'saved') return t('plans.statusSaved');
    if (s === 'published') return t('plans.statusPublished');
    return s;
  };

  const handleDownloadPDF = async () => {
    if (!cycleId || !cycle) return;
    try {
      const url = `/plans/plan-cycles/${cycleId}/download-pdf/`;
      const fallbackName = `Plan_${cycle.client_name.replace(/\s+/g, '')}_${cycle.start_date}_${cycle.end_date}.pdf`;

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
      setError(err.response?.data?.error || t('clientPortal.downloadPdfFailed'));
    }
  };

  if (cycleId && !cycle) {
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

  if (cycleId && cycle) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('plans.planBuilder')}</h1>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      cycle.status === 'published'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                        : cycle.status === 'saved'
                        ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {statusLabel(cycle.status)}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {cycle.client_name} • {t('plans.durationDays', { count: cycle.duration_days })} • {cycle.start_date} - {cycle.end_date}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {(cycle.status === 'draft' || cycle.status === 'saved') && (
                  <>
                    <button
                      type="button"
                      onClick={() => setPlanStatus('saved')}
                      disabled={loading}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                    >
                      {t('plans.savePlan')}
                    </button>
                    <button
                      type="button"
                      onClick={() => setPlanStatus('published')}
                      disabled={loading || cycle.can_publish === false}
                      title={cycle.can_publish === false ? t('plans.publishPlanDisabled') : undefined}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t('plans.publishPlan')}
                    </button>
                  </>
                )}
                {cycle.status === 'published' && (
                  <button
                    type="button"
                    onClick={() => setPlanStatus('saved')}
                    disabled={loading}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                  >
                    {t('plans.savePlan')}
                  </button>
                )}
                <button
                  onClick={handleGeneratePDF}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                >
                  <FileText className="h-5 w-5 mr-2" />
                  {t('plans.generatePdf')}
                </button>
                {cycle.plan_pdf && (
                  <button
                    onClick={handleDownloadPDF}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                  >
                    <Download className="h-5 w-5 mr-2" />
                    {t('plans.downloadPdf')}
                  </button>
                )}
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="border-b border-gray-200 dark:border-gray-700">
              <nav className="-mb-px flex">
                <button
                  onClick={() => setActiveTab('diet')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'diet'
                      ? 'border-blue-500 dark:border-blue-400 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  {t('plans.nutritionPlan')}
                </button>
                <button
                  onClick={() => setActiveTab('workout')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'workout'
                      ? 'border-blue-500 dark:border-blue-400 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  {t('plans.workoutPlan')}
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('plans.createPlan')}</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {t('plans.createPlanSubtitle')}
          </p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded">
            <pre className="whitespace-pre-wrap text-sm">{error}</pre>
          </div>
        )}

        <form onSubmit={handleCreateCycle} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('plans.client')} <span className="text-red-500">*</span>
            </label>
            <select
              name="client_id"
              required
              defaultValue={preselectedClientId}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{t('plans.selectClient')}</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.full_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('plans.periodDays')} <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="period_days"
              required
              min="1"
              defaultValue="15"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('plans.goalOptional')}
            </label>
            <select
              name="goal"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{t('plans.selectGoal')}</option>
              <option value="fat_loss">{t('plans.fatLoss')}</option>
              <option value="recomp">{t('plans.recomp')}</option>
              <option value="muscle_gain">{t('plans.muscleGain')}</option>
              <option value="maintenance">{t('plans.maintenance')}</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={() => navigate('/plans')}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 disabled:opacity-50"
            >
              <Plus className="h-4 w-4 mr-2" />
              {loading ? t('plans.creating') : t('plans.createPlan')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
