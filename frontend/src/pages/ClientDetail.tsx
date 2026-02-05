import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { toast } from 'react-hot-toast';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  sex: string;
  height_cm: number;
  initial_weight_kg: number;
  notes: string;
  emergency_contact: string;
  created_at: string;
  is_active?: boolean;
  deactivated_at?: string | null;
  deactivation_reason?: string;
  has_portal_access?: boolean;
  portal_username?: string | null;
}

interface CheckIn {
  id: number;
  date: string;
  weight_kg: number;
  body_fat_pct?: number;
  chest_cm?: number;
  waist_cm?: number;
  hips_cm?: number;
  bicep_cm?: number;
  thigh_cm?: number;
  calf_cm?: number;
  rpe?: number;
  fatigue?: number;
  diet_adherence?: number;
  workout_adherence?: number;
  notes?: string;
  created_at: string;
}

export default function ClientDetail() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [checkIns, setCheckIns] = useState<CheckIn[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>('weight_kg');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [deactivateReason, setDeactivateReason] = useState('');
  const [deactivateLoading, setDeactivateLoading] = useState(false);
  const [reactivateLoading, setReactivateLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchClientData();
    }
  }, [id]);

  const fetchClientData = async () => {
    try {
      // Fetch client details
      const clientResponse = await api.get(`/clients/${id}/`);
      setClient(clientResponse.data);

      // Fetch client check-ins
      const checkInsResponse = await api.get(`/clients/${id}/check-ins/`);
      setCheckIns(checkInsResponse.data.results || checkInsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch client data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeactivateLoading(true);
    try {
      const response = await api.post(`/clients/${id}/deactivate/`, { reason: deactivateReason.trim() || undefined });
      setClient(response.data);
      const count = response.data.cancelled_appointments_count ?? 0;
      toast.success(
        count > 0
          ? `Cliente dado de baja. Citas futuras canceladas: ${count}`
          : 'Cliente dado de baja.',
      );
      setShowDeactivateModal(false);
      setDeactivateReason('');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Error al dar de baja';
      toast.error(msg);
    } finally {
      setDeactivateLoading(false);
    }
  };

  const handleReactivate = async () => {
    setReactivateLoading(true);
    try {
      const response = await api.post(`/clients/${id}/reactivate/`);
      setClient(response.data);
      toast.success('Cliente reactivado.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Error al reactivar';
      toast.error(msg);
    } finally {
      setReactivateLoading(false);
    }
  };

  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);
    setPasswordLoading(true);

    if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      setPasswordLoading(false);
      return;
    }

    try {
      const response = await api.post(`/clients/${id}/set_password/`, {
        password,
      });
      setPasswordSuccess(response.data.message || 'Password set successfully');
      setPassword('');
      setShowPasswordModal(false);
      // Refresh client data to get updated portal_username
      await fetchClientData();
    } catch (err: any) {
      console.error('Set password error:', err);
      if (err.response?.status === 404) {
        setPasswordError('Endpoint not found. Please make sure the server is running and has been restarted after the latest changes.');
      } else if (err.response?.status === 403) {
        setPasswordError('You do not have permission to set passwords. Only coaches can perform this action.');
      } else if (err.response?.status === 401) {
        setPasswordError('You are not authenticated. Please log in again.');
      } else {
        const detail = err.response?.data;
        const msg = typeof detail === 'object' && detail !== null
          ? (detail.password?.[0] || detail.error || detail.detail || JSON.stringify(detail))
          : (err.response?.data?.message || err.message || 'Failed to set password');
        setPasswordError(msg);
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    
    return age;
  };

  const getMetricLabel = (metric: string) => {
    const labels: { [key: string]: string } = {
      weight_kg: 'Weight (kg)',
      body_fat_pct: 'Body Fat (%)',
      chest_cm: 'Chest (cm)',
      waist_cm: 'Waist (cm)',
      hips_cm: 'Hips (cm)',
      bicep_cm: 'Bicep (cm)',
      thigh_cm: 'Thigh (cm)',
      calf_cm: 'Calf (cm)',
          rpe: 'RPE Rating',
    fatigue: 'Fatigue Level',
    diet_adherence: 'Diet Adherence (%)',
    workout_adherence: 'Workout Adherence (%)',
    };
    return labels[metric] || metric;
  };

  const calculateTrend = (checkIns: CheckIn[], metric: string) => {
    if (checkIns.length < 2) return null;
    
    const sortedCheckIns = [...checkIns].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    const first = sortedCheckIns[0];
    const last = sortedCheckIns[sortedCheckIns.length - 1];
    
    const firstValue = first[metric as keyof CheckIn] as number;
    const lastValue = last[metric as keyof CheckIn] as number;
    
    if (firstValue === undefined || lastValue === undefined) return null;
    
    const change = lastValue - firstValue;
    const percentChange = (change / firstValue) * 100;
    
    return {
      change,
      percentChange,
      isPositive: change > 0,
      isNegative: change < 0,
      isNeutral: change === 0,
    };
  };

  const formatTrend = (trend: { change: number; percentChange: number; isPositive: boolean; isNegative: boolean; isNeutral: boolean } | null) => {
    if (!trend) return null;
    
    const sign = trend.isPositive ? '+' : '';
    const color = trend.isPositive ? 'text-green-600' : trend.isNegative ? 'text-red-600' : 'text-gray-600';
    const icon = trend.isPositive ? '↗' : trend.isNegative ? '↘' : '→';
    
    return (
      <span className={`text-sm font-medium ${color}`}>
        {icon} {sign}{trend.change.toFixed(1)} ({sign}{trend.percentChange.toFixed(1)}%)
      </span>
    );
  };

  const getChartData = () => {
    return checkIns
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(checkIn => ({
        date: formatDate(checkIn.date),
        value: checkIn[selectedMetric as keyof CheckIn] as number,
      }))
      .filter(item => item.value !== undefined);
  };

  const getLatestCheckIn = () => {
    if (checkIns.length === 0) return null;
    return checkIns.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())[0];
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

  if (!client) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">Client not found</div>
          </div>
        </div>
      </div>
    );
  }

  const latestCheckIn = getLatestCheckIn();
  const weightTrend = calculateTrend(checkIns, 'weight_kg');

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-gray-900">
                  {client.first_name} {client.last_name}
                </h1>
                {client.is_active === false && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                    Inactivo
                  </span>
                )}
              </div>
              <p className="mt-2 text-sm text-gray-600">
                Client since {formatDate(client.created_at)}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {client.is_active === false ? (
                <>
                  <span
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-500 bg-gray-100 cursor-not-allowed"
                    title="Cliente inactivo. Reactívalo para crear nuevos planes o seguimientos."
                  >
                    <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    New Check-In
                  </span>
                  <span
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-500 bg-gray-100 cursor-not-allowed"
                    title="Cliente inactivo. Reactívalo para crear nuevos planes o seguimientos."
                  >
                    New Plan
                  </span>
                  <button
                    onClick={handleReactivate}
                    disabled={reactivateLoading}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                  >
                    {reactivateLoading ? 'Reactivando...' : 'Reactivar cliente'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => navigate(`/clients/${id}/check-in`)}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    New Check-In
                  </button>
                  <button
                    onClick={() => navigate(`/plans/new?client=${id}`)}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    New Plan
                  </button>
                  <button
                    onClick={() => setShowDeactivateModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Dar de baja
                  </button>
                </>
              )}
              <button
                onClick={() => navigate('/clients')}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                ← Back to Clients
              </button>
            </div>
          </div>
          {client.is_active === false && (
            <p className="mt-2 text-sm text-amber-700">
              Cliente inactivo. Reactívalo para crear nuevos planes o seguimientos.
            </p>
          )}
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Client Information */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow-lg rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Client Information</h2>
              </div>
              <div className="px-6 py-4">
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Full Name</dt>
                    <dd className="mt-1 text-sm text-gray-900">{client.first_name} {client.last_name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Age</dt>
                    <dd className="mt-1 text-sm text-gray-900">{getAge(client.date_of_birth)} years old</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Sex</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {client.sex === 'M' ? 'Male' : client.sex === 'F' ? 'Female' : 'Other'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Email</dt>
                    <dd className="mt-1 text-sm text-gray-900">{client.email}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Phone</dt>
                    <dd className="mt-1 text-sm text-gray-900">{client.phone}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Height</dt>
                    <dd className="mt-1 text-sm text-gray-900">{client.height_cm} cm</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Initial Weight</dt>
                    <dd className="mt-1 text-sm text-gray-900">{client.initial_weight_kg} kg</dd>
                  </div>
                  {client.emergency_contact && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Emergency Contact</dt>
                      <dd className="mt-1 text-sm text-gray-900">{client.emergency_contact}</dd>
                    </div>
                  )}
                  {client.notes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Notes</dt>
                      <dd className="mt-1 text-sm text-gray-900">{client.notes}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Portal Access</dt>
                    <dd className="mt-1 text-sm">
                      {client.has_portal_access ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Not Set
                        </span>
                      )}
                      {client.portal_username && (
                        <span className="ml-2 text-gray-600">({client.portal_username})</span>
                      )}
                    </dd>
                  </div>
                </dl>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => setShowPasswordModal(true)}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {client.has_portal_access ? 'Update Portal Password' : 'Set Portal Password'}
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="mt-6 bg-white shadow-lg rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Quick Stats</h2>
              </div>
              <div className="px-6 py-4">
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Total Check-Ins</dt>
                    <dd className="mt-1 text-2xl font-semibold text-gray-900">{checkIns.length}</dd>
                  </div>
                  {latestCheckIn && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Latest Weight</dt>
                      <dd className="mt-1 text-2xl font-semibold text-gray-900">
                        {latestCheckIn.weight_kg} kg
                      </dd>
                    </div>
                  )}
                  {weightTrend && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Weight Trend</dt>
                      <dd className="mt-1 text-sm">
                        {formatTrend(weightTrend)}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          </div>

          {/* Progress Chart and Check-Ins */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Chart */}
            <div className="bg-white shadow-lg rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Progress Chart</h2>
                  <select
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value)}
                    className="block w-48 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    <option value="weight_kg">Weight (kg)</option>
                    <option value="body_fat_pct">Body Fat (%)</option>
                    <option value="chest_cm">Chest (cm)</option>
                    <option value="waist_cm">Waist (cm)</option>
                    <option value="hips_cm">Hips (cm)</option>
                    <option value="bicep_cm">Bicep (cm)</option>
                    <option value="thigh_cm">Thigh (cm)</option>
                    <option value="calf_cm">Calf (cm)</option>
                                         <option value="rpe">RPE Rating</option>
                     <option value="fatigue">Fatigue Level</option>
                     <option value="diet_adherence">Diet Adherence (%)</option>
                     <option value="workout_adherence">Workout Adherence (%)</option>
                  </select>
                </div>
              </div>
              <div className="px-6 py-4">
                {getChartData().length > 0 ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={getChartData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="value" 
                          stroke="#3B82F6" 
                          strokeWidth={2}
                          name={getMetricLabel(selectedMetric)}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No data to display</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Create a check-in to see progress charts.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Check-Ins History */}
            <div className="bg-white shadow-lg rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Check-Ins History</h2>
                  <span className="text-sm text-gray-500">
                    {checkIns.length} check-in{checkIns.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {checkIns.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No check-ins yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Start tracking progress by creating the first check-in.
                  </p>
                  <div className="mt-6">
                    {client.is_active !== false ? (
                      <button
                        onClick={() => navigate(`/clients/${id}/check-in`)}
                        className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Create First Check-In
                      </button>
                    ) : (
                      <p className="text-sm text-amber-700">Cliente inactivo. Reactívalo para crear seguimientos.</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Weight
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Body Fat
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Adherence
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Notes
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {checkIns
                        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                        .map((checkIn) => (
                          <tr key={checkIn.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatDate(checkIn.date)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {checkIn.weight_kg} kg
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {checkIn.body_fat_pct ? `${checkIn.body_fat_pct}%` : '-'}
                            </td>
                                                       <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                             {checkIn.diet_adherence ? `${checkIn.diet_adherence}%` : '-'}
                           </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {checkIn.notes ? (
                                <span className="truncate max-w-xs block" title={checkIn.notes}>
                                  {checkIn.notes}
                                </span>
                              ) : (
                                '-'
                              )}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {client.has_portal_access ? 'Update Portal Password' : 'Set Portal Password'}
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                {client.has_portal_access
                  ? 'Enter a new password for the client portal. The client will use their email as username.'
                  : 'Set a password so the client can access the portal. They will use their email as username.'}
              </p>
              {passwordError && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-800">{passwordError}</p>
                </div>
              )}
              {passwordSuccess && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-3">
                  <p className="text-sm text-green-800">{passwordSuccess}</p>
                </div>
              )}
              <form onSubmit={handleSetPassword}>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password (min. 8 characters)
                  </label>
                  <input
                    type="password"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter password"
                    required
                    minLength={8}
                  />
                </div>
                <div className="mt-4 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowPasswordModal(false);
                      setPassword('');
                      setPasswordError(null);
                      setPasswordSuccess(null);
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={passwordLoading || password.length < 8}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {passwordLoading ? 'Setting...' : 'Set Password'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Deactivate confirmation modal */}
      {showDeactivateModal && client && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Dar de baja cliente</h3>
              <p className="text-sm text-gray-600 mb-4">
                Se cancelarán automáticamente todas las citas futuras del cliente.
              </p>
              <form onSubmit={handleDeactivate}>
                <div className="mb-4">
                  <label htmlFor="deactivate-reason" className="block text-sm font-medium text-gray-700 mb-1">
                    Motivo (opcional)
                  </label>
                  <input
                    type="text"
                    id="deactivate-reason"
                    value={deactivateReason}
                    onChange={(e) => setDeactivateReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                    placeholder="Ej. Se fue del programa"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowDeactivateModal(false);
                      setDeactivateReason('');
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={deactivateLoading}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    {deactivateLoading ? 'Procesando...' : 'Dar de baja'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
