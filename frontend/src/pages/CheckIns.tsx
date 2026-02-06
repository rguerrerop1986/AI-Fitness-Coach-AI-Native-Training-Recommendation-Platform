import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTranslation } from 'react-i18next';

interface CheckIn {
  id: number;
  client: {
    id: number;
    first_name: string;
    last_name: string;
  };
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

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export default function CheckIns() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [checkIns, setCheckIns] = useState<CheckIn[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<string>('weight_kg');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Fetch all check-ins
      const checkInsResponse = await api.get('/tracking/check-ins/');
      setCheckIns(checkInsResponse.data.results || checkInsResponse.data);

      // Fetch all clients
      const clientsResponse = await api.get('/clients/');
      setClients(clientsResponse.data.results || clientsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch check-ins');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
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
    let filteredCheckIns = checkIns.filter(checkIn => checkIn.client); // Only include check-ins with client data
    
    if (selectedClient !== 'all') {
      filteredCheckIns = filteredCheckIns.filter(checkIn => checkIn.client.id.toString() === selectedClient);
    }
    
    return filteredCheckIns
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(checkIn => ({
        date: formatDate(checkIn.date),
        value: checkIn[selectedMetric as keyof CheckIn] as number,
        client: `${checkIn.client.first_name} ${checkIn.client.last_name}`,
      }))
      .filter(item => item.value !== undefined);
  };

  const filteredCheckIns = selectedClient === 'all' 
    ? checkIns.filter(checkIn => checkIn.client) // Only include check-ins with client data
    : checkIns.filter(checkIn => checkIn.client && checkIn.client.id.toString() === selectedClient);

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
              <h1 className="text-3xl font-bold text-gray-900">{t('checkIns.title')}</h1>
              <p className="mt-2 text-sm text-gray-600">
                {t('checkIns.subtitle')}
              </p>
            </div>
            <button
              onClick={() => navigate('/clients')}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {t('checkIns.viewClients')}
            </button>
          </div>
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
                <h3 className="text-sm font-medium text-red-800">{t('common.error')}</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Filters and Chart */}
        <div className="bg-white shadow-lg rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">{t('checkIns.progressTrends')}</h2>
          </div>
          
          <div className="px-6 py-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label htmlFor="client-filter" className="block text-sm font-medium text-gray-700">
                  {t('checkIns.filterByClient')}
                </label>
                <select
                  id="client-filter"
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="all">{t('checkIns.allClients')}</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id.toString()}>
                      {client.first_name} {client.last_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="metric-filter" className="block text-sm font-medium text-gray-700">
                  {t('checkIns.metricToDisplay')}
                </label>
                <select
                  id="metric-filter"
                  value={selectedMetric}
                  onChange={(e) => setSelectedMetric(e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="weight_kg">{t('metrics.weight')}</option>
                  <option value="body_fat_pct">{t('metrics.bodyFat')}</option>
                  <option value="chest_cm">{t('metrics.chest')}</option>
                  <option value="waist_cm">{t('metrics.waist')}</option>
                  <option value="hips_cm">{t('metrics.hips')}</option>
                  <option value="bicep_cm">{t('metrics.bicep')}</option>
                  <option value="thigh_cm">{t('metrics.thigh')}</option>
                  <option value="calf_cm">{t('metrics.calf')}</option>
                  <option value="rpe">{t('metrics.rpe')}</option>
                  <option value="fatigue">{t('metrics.fatigue')}</option>
                  <option value="diet_adherence">{t('metrics.dietAdherence')}</option>
                  <option value="workout_adherence">{t('metrics.workoutAdherence')}</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={() => {
                    setSelectedClient('all');
                    setSelectedMetric('weight_kg');
                  }}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {t('common.reset')}
                </button>
              </div>
            </div>

            {/* Chart */}
            {getChartData().length > 0 && (
              <div className="mt-6 h-64">
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
            )}
          </div>
        </div>

        {/* Check-Ins List */}
        <div className="bg-white shadow-lg rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">{t('checkIns.recentCheckIns')}</h2>
              <span className="text-sm text-gray-500">
                {filteredCheckIns.length} {t('checkIns.title').toLowerCase()}
              </span>
            </div>
          </div>

          {filteredCheckIns.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">{t('checkIns.noCheckIns')}</h3>
              <p className="mt-1 text-sm text-gray-500">
                {selectedClient === 'all' 
                  ? t('checkIns.noCheckInsDescription')
                  : t('checkIns.noCheckInsYetDescription')}
              </p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('checkIns.client')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('checkIns.date')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('checkIns.weight')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('checkIns.bodyFat')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('checkIns.adherence')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('checkIns.trend')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('common.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredCheckIns.map((checkIn) => {
                    // Skip check-ins without client data
                    if (!checkIn.client) {
                      return null;
                    }
                    
                    const clientCheckIns = checkIns.filter(c => c.client && c.client.id === checkIn.client.id);
                    const trend = calculateTrend(clientCheckIns, 'weight_kg');
                    
                    return (
                      <tr key={checkIn.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <span className="text-sm font-medium text-blue-800">
                                  {checkIn.client.first_name?.charAt(0) || '?'}{checkIn.client.last_name?.charAt(0) || '?'}
                                </span>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {checkIn.client.first_name || 'Unknown'} {checkIn.client.last_name || 'Client'}
                              </div>
                            </div>
                          </div>
                        </td>
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
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatTrend(trend)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => navigate(`/clients/${checkIn.client.id}`)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            {t('checkIns.viewDetails')}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
