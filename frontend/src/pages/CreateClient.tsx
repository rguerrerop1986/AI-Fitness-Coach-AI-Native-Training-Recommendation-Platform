import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { api } from '../lib/api';
import { useTranslation } from 'react-i18next';

// Validation schema for client creation
const createClientSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  date_of_birth: z.string().min(1, 'Date of birth is required'),
  sex: z.enum(['M', 'F', 'O']),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(1, 'Phone number is required'),
  height_cm: z.number().min(100, 'Height must be at least 100cm').max(250, 'Height must be less than 250cm'),
  initial_weight_kg: z.number().min(30, 'Weight must be at least 30kg').max(300, 'Weight must be less than 300kg'),
  notes: z.string().optional(),
  consent_checkbox: z.boolean().refine(val => val === true, 'You must consent to data processing'),
  emergency_contact_name: z.string().min(1, 'Emergency contact name is required'),
  emergency_contact_phone: z.string().min(1, 'Emergency contact phone is required'),
  emergency_contact_relationship: z.string().min(1, 'Emergency contact relationship is required'),
});

type CreateClientFormData = z.infer<typeof createClientSchema>;

export default function CreateClient() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CreateClientFormData>({
    resolver: zodResolver(createClientSchema),
    defaultValues: {
      sex: 'M',
      consent_checkbox: false,
    },
  });

  const onSubmit = async (data: CreateClientFormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // Format emergency contact as a string
      const emergencyContactString = `${data.emergency_contact_name} - ${data.emergency_contact_phone} (${data.emergency_contact_relationship})`;
      
      const response = await api.post('/clients/', {
        first_name: data.first_name,
        last_name: data.last_name,
        date_of_birth: data.date_of_birth,
        sex: data.sex,
        email: data.email,
        phone: data.phone,
        height_cm: data.height_cm,
        initial_weight_kg: data.initial_weight_kg,
        notes: data.notes || '',
        consent_checkbox: data.consent_checkbox,
        emergency_contact: emergencyContactString,
      });

      if (response.status === 201) {
        navigate('/clients');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create client');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-lg rounded-lg">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{t('clients.createNewClient')}</h1>
                <p className="mt-1 text-sm text-gray-600">
                  {t('clients.addNewClientDescription')}
                </p>
              </div>
              <button
                onClick={() => navigate('/clients')}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                ← {t('common.back')} {t('navigation.clients')}
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
              {/* Personal Information */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('clients.personalInformation')}</h3>
                  
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                        {t('clients.firstName')} *
                      </label>
                      <input
                        type="text"
                        id="first_name"
                        {...register('first_name')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                      {errors.first_name && (
                        <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                        {t('clients.lastName')} *
                      </label>
                      <input
                        type="text"
                        id="last_name"
                        {...register('last_name')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                      {errors.last_name && (
                        <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
                      )}
                    </div>
                  </div>

                  <div className="mt-4">
                    <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700">
                      {t('clients.dateOfBirth')} *
                    </label>
                    <input
                      type="date"
                      id="date_of_birth"
                      {...register('date_of_birth')}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                    {errors.date_of_birth && (
                      <p className="mt-1 text-sm text-red-600">{errors.date_of_birth.message}</p>
                    )}
                  </div>

                  <div className="mt-4">
                    <label htmlFor="sex" className="block text-sm font-medium text-gray-700">
                      {t('clients.sex')} *
                    </label>
                    <select
                      id="sex"
                      {...register('sex')}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="M">{t('clients.male')}</option>
                      <option value="F">{t('clients.female')}</option>
                      <option value="O">{t('clients.other')}</option>
                    </select>
                    {errors.sex && (
                      <p className="mt-1 text-sm text-red-600">{errors.sex.message}</p>
                    )}
                  </div>
                </div>

                {/* Contact Information */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('clients.contactInformation')}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                        {t('auth.email')} *
                      </label>
                      <input
                        type="email"
                        id="email"
                        {...register('email')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                      {errors.email && (
                        <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                        {t('clients.phone')} *
                      </label>
                      <input
                        type="tel"
                        id="phone"
                        {...register('phone')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                      {errors.phone && (
                        <p className="mt-1 text-sm text-red-600">{errors.phone.message}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Physical Information & Emergency Contact */}
              <div className="space-y-6">
                {/* Physical Information */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('clients.physicalInformation')}</h3>
                  
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label htmlFor="height_cm" className="block text-sm font-medium text-gray-700">
                        {t('clients.height')} *
                      </label>
                      <input
                        type="number"
                        id="height_cm"
                        {...register('height_cm', { valueAsNumber: true })}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="170"
                      />
                      {errors.height_cm && (
                        <p className="mt-1 text-sm text-red-600">{errors.height_cm.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="initial_weight_kg" className="block text-sm font-medium text-gray-700">
                        {t('clients.initialWeight')} *
                      </label>
                      <input
                        type="number"
                        id="initial_weight_kg"
                        {...register('initial_weight_kg', { valueAsNumber: true })}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="70"
                        step="0.1"
                      />
                      {errors.initial_weight_kg && (
                        <p className="mt-1 text-sm text-red-600">{errors.initial_weight_kg.message}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Emergency Contact */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{t('clients.emergencyContact')}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="emergency_contact_name" className="block text-sm font-medium text-gray-700">
                        {t('clients.emergencyContactName')} *
                      </label>
                      <input
                        type="text"
                        id="emergency_contact_name"
                        {...register('emergency_contact_name')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                      {errors.emergency_contact_name && (
                        <p className="mt-1 text-sm text-red-600">{errors.emergency_contact_name.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="emergency_contact_phone" className="block text-sm font-medium text-gray-700">
                        {t('clients.emergencyContactPhone')} *
                      </label>
                      <input
                        type="tel"
                        id="emergency_contact_phone"
                        {...register('emergency_contact_phone')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                      {errors.emergency_contact_phone && (
                        <p className="mt-1 text-sm text-red-600">{errors.emergency_contact_phone.message}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="emergency_contact_relationship" className="block text-sm font-medium text-gray-700">
                        {t('clients.emergencyContactRelationship')} *
                      </label>
                      <input
                        type="text"
                        id="emergency_contact_relationship"
                        {...register('emergency_contact_relationship')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="e.g., Spouse, Parent, Friend"
                      />
                      {errors.emergency_contact_relationship && (
                        <p className="mt-1 text-sm text-red-600">{errors.emergency_contact_relationship.message}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                    {t('clients.notes')}
                  </label>
                  <textarea
                    id="notes"
                    rows={3}
                    {...register('notes')}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Any additional notes about the client..."
                  />
                  {errors.notes && (
                    <p className="mt-1 text-sm text-red-600">{errors.notes.message}</p>
                  )}
                </div>

                {/* Consent */}
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="consent_checkbox"
                      type="checkbox"
                      {...register('consent_checkbox')}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="consent_checkbox" className="font-medium text-gray-700">
                      {t('clients.consent')} *
                    </label>
                    <p className="text-gray-500">
                      {t('clients.consentText')}
                    </p>
                    {errors.consent_checkbox && (
                      <p className="mt-1 text-sm text-red-600">{errors.consent_checkbox.message}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="mt-8 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/clients')}
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
                    {t('common.loading')}...
                  </>
                ) : (
                  t('clients.createNewClient')
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
