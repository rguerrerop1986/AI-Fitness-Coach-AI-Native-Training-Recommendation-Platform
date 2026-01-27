import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { api } from '../lib/api';
import { useTranslation } from 'react-i18next';

type CreateCheckInFormData = {
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
};

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

interface PreviousCheckIn {
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
}

export default function CreateCheckIn() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { clientId } = useParams<{ clientId: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [previousCheckIn, setPreviousCheckIn] = useState<PreviousCheckIn | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Validation schema for check-in creation
  const createCheckInSchema = z.object({
    weight_kg: z.number().min(30, t('validation.weightMin')).max(300, t('validation.weightMax')),
    body_fat_pct: z.number().min(0, t('validation.bodyFatMin')).max(50, t('validation.bodyFatMax')).optional(),
    chest_cm: z.number().min(50, t('validation.chestMin')).max(200, t('validation.chestMax')).optional(),
    waist_cm: z.number().min(50, t('validation.waistMin')).max(200, t('validation.waistMax')).optional(),
    hips_cm: z.number().min(50, t('validation.hipsMin')).max(200, t('validation.hipsMax')).optional(),
    bicep_cm: z.number().min(20, t('validation.bicepMin')).max(100, t('validation.bicepMax')).optional(),
    thigh_cm: z.number().min(30, t('validation.thighMin')).max(150, t('validation.thighMax')).optional(),
    calf_cm: z.number().min(20, t('validation.calfMin')).max(100, t('validation.calfMax')).optional(),
    rpe: z.number().min(1, t('validation.rpeMin')).max(10, t('validation.rpeMax')).optional(),
    fatigue: z.number().min(1, t('validation.fatigueMin')).max(10, t('validation.fatigueMax')).optional(),
    diet_adherence: z.number().min(0, t('validation.adherenceMin')).max(100, t('validation.adherenceMax')).optional(),
    workout_adherence: z.number().min(0, t('validation.adherenceMin')).max(100, t('validation.adherenceMax')).optional(),
    notes: z.string().optional(),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CreateCheckInFormData>({
    resolver: zodResolver(createCheckInSchema),
    defaultValues: {
      rpe: 5,
      fatigue: 5,
      diet_adherence: 80,
      workout_adherence: 80,
    },
  });

  const watchedValues = watch();

  useEffect(() => {
    if (clientId) {
      fetchClientAndPreviousCheckIn();
    }
  }, [clientId]);

  const fetchClientAndPreviousCheckIn = async () => {
    try {
      // Fetch client details
      const clientResponse = await api.get(`/clients/${clientId}/`);
      setClient(clientResponse.data);

      // Fetch previous check-in
      const checkInsResponse = await api.get(`/clients/${clientId}/check-ins/`);
      if (checkInsResponse.data.results && checkInsResponse.data.results.length > 0) {
        setPreviousCheckIn(checkInsResponse.data.results[0]); // Most recent
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch client data');
    } finally {
      setLoading(false);
    }
  };

  const calculateDifference = (current: number | undefined, previous: number | undefined) => {
    if (current === undefined || previous === undefined) return null;
    const diff = current - previous;
    return {
      value: diff,
      isPositive: diff > 0,
      isNegative: diff < 0,
      isNeutral: diff === 0,
    };
  };

  const formatDifference = (diff: { value: number; isPositive: boolean; isNegative: boolean; isNeutral: boolean } | null) => {
    if (!diff) return null;
    
    const sign = diff.isPositive ? '+' : '';
    const color = diff.isPositive ? 'text-green-600' : diff.isNegative ? 'text-red-600' : 'text-gray-600';
    const icon = diff.isPositive ? '↗' : diff.isNegative ? '↘' : '→';
    
    return (
      <span className={`text-sm font-medium ${color}`}>
        {icon} {sign}{diff.value.toFixed(1)}
      </span>
    );
  };

  const onSubmit = async (data: CreateCheckInFormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.post(`/clients/${clientId}/check-ins/`, {
        ...data,
        date: new Date().toISOString().split('T')[0], // Today's date
      });

      if (response.status === 201) {
        navigate(`/clients/${clientId}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create check-in');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
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

  if (!client) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">Client not found</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-lg rounded-lg">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{t('checkIns.newCheckIn')}</h1>
                <p className="mt-1 text-sm text-gray-600">
                  {t('checkIns.client')}: {client.first_name} {client.last_name}
                </p>
              </div>
              <button
                onClick={() => navigate(`/clients/${clientId}`)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {t('checkIns.backToClient')}
              </button>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-6">
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

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Weight and Body Fat */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('checkIns.weightAndBodyComposition')}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="weight_kg" className="block text-sm font-medium text-gray-700">
                        {t('metrics.weight')} *
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="weight_kg"
                          step="0.1"
                          {...register('weight_kg', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="70.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.weight_kg, previousCheckIn.weight_kg))}
                          </div>
                        )}
                      </div>
                      {errors.weight_kg && (
                        <p className="mt-1 text-sm text-red-600">{errors.weight_kg.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="body_fat_pct" className="block text-sm font-medium text-gray-700">
                        {t('metrics.bodyFat')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="body_fat_pct"
                          step="0.1"
                          {...register('body_fat_pct', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="15.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.body_fat_pct, previousCheckIn.body_fat_pct))}
                          </div>
                        )}
                      </div>
                      {errors.body_fat_pct && (
                        <p className="mt-1 text-sm text-red-600">{errors.body_fat_pct.message}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Upper Body Measurements */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('checkIns.upperBody')}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="chest_cm" className="block text-sm font-medium text-gray-700">
                        {t('metrics.chest')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="chest_cm"
                          step="0.1"
                          {...register('chest_cm', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="100.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.chest_cm, previousCheckIn.chest_cm))}
                          </div>
                        )}
                      </div>
                      {errors.chest_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.chest_cm.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="bicep_cm" className="block text-sm font-medium text-gray-700">
                        {t('metrics.bicep')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="bicep_cm"
                          step="0.1"
                          {...register('bicep_cm', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="35.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.bicep_cm, previousCheckIn.bicep_cm))}
                          </div>
                        )}
                      </div>
                      {errors.bicep_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.bicep_cm.message}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Lower Body Measurements */}
              <div className="space-y-6">
                {/* Core Measurements */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('checkIns.core')}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="waist_cm" className="block text-sm font-medium text-gray-700">
                        {t('metrics.waist')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="waist_cm"
                          step="0.1"
                          {...register('waist_cm', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="80.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.waist_cm, previousCheckIn.waist_cm))}
                          </div>
                        )}
                      </div>
                      {errors.waist_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.waist_cm.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="hips_cm" className="block text-sm font-medium text-gray-700">
                        {t('metrics.hips')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="hips_cm"
                          step="0.1"
                          {...register('hips_cm', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="95.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.hips_cm, previousCheckIn.hips_cm))}
                          </div>
                        )}
                      </div>
                      {errors.hips_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.hips_cm.message}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Lower Body Measurements */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('checkIns.lowerBody')}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="thigh_cm" className="block text-sm font-medium text-gray-700">
                        {t('metrics.thigh')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="thigh_cm"
                          step="0.1"
                          {...register('thigh_cm', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="55.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.thigh_cm, previousCheckIn.thigh_cm))}
                          </div>
                        )}
                      </div>
                      {errors.thigh_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.thigh_cm.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="calf_cm" className="block text-sm font-medium text-gray-700">
                        {t('metrics.calf')}
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type="number"
                          id="calf_cm"
                          step="0.1"
                          {...register('calf_cm', { valueAsNumber: true })}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="35.0"
                        />
                        {previousCheckIn && (
                          <div className="absolute right-2 top-2">
                            {formatDifference(calculateDifference(watchedValues.calf_cm, previousCheckIn.calf_cm))}
                          </div>
                        )}
                      </div>
                      {errors.calf_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.calf_cm.message}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Training Feedback */}
            <div className="mt-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">{t('checkIns.trainingFeedback')}</h3>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <label htmlFor="rpe" className="block text-sm font-medium text-gray-700">
                    {t('metrics.rpe')}
                  </label>
                  <input
                    type="number"
                    id="rpe"
                    min="1"
                    max="10"
                    {...register('rpe', { valueAsNumber: true })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {errors.rpe && (
                    <p className="mt-1 text-sm text-red-600">{errors.rpe.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="fatigue" className="block text-sm font-medium text-gray-700">
                    {t('metrics.fatigue')}
                  </label>
                  <input
                    type="number"
                    id="fatigue"
                    min="1"
                    max="10"
                    {...register('fatigue', { valueAsNumber: true })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {errors.fatigue && (
                    <p className="mt-1 text-sm text-red-600">{errors.fatigue.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="diet_adherence" className="block text-sm font-medium text-gray-700">
                    {t('metrics.dietAdherence')}
                  </label>
                  <input
                    type="number"
                    id="diet_adherence"
                    min="0"
                    max="100"
                    {...register('diet_adherence', { valueAsNumber: true })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {errors.diet_adherence && (
                    <p className="mt-1 text-sm text-red-600">{errors.diet_adherence.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="workout_adherence" className="block text-sm font-medium text-gray-700">
                    {t('metrics.workoutAdherence')}
                  </label>
                  <input
                    type="number"
                    id="workout_adherence"
                    min="0"
                    max="100"
                    {...register('workout_adherence', { valueAsNumber: true })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {errors.workout_adherence && (
                    <p className="mt-1 text-sm text-red-600">{errors.workout_adherence.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Notes */}
            <div className="mt-8">
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                {t('checkIns.notes')}
              </label>
              <textarea
                id="notes"
                rows={4}
                {...register('notes')}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={t('checkIns.notesPlaceholder')}
              />
              {errors.notes && (
                <p className="mt-1 text-sm text-red-600">{errors.notes.message}</p>
              )}
            </div>

            {/* Form Actions */}
            <div className="mt-8 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate(`/clients/${clientId}`)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {t('checkIns.creating')}...
                  </>
                ) : (
                  t('checkIns.createCheckIn')
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
