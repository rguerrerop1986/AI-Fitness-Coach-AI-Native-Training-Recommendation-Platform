import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';
import { Calendar, Clock, DollarSign, CheckCircle, XCircle, Moon, Sun } from 'lucide-react';

interface Appointment {
  id: number;
  coach_name: string;
  scheduled_at: string;
  duration_minutes: number;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  notes: string;
  price: string;
  currency: string;
  payment_status: 'unpaid' | 'paid' | 'refunded';
  payment_method?: 'cash' | 'transfer' | 'card' | 'other';
  paid_at?: string;
  created_at: string;
}

export default function ClientAppointments() {
  const { theme, toggleTheme } = useTheme();
  const [appointments, setAppointments] = useState<{
    all: Appointment[];
    upcoming: Appointment[];
    past: Appointment[];
  }>({ all: [], upcoming: [], past: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const response = await api.get('/client/me/appointments/');
      setAppointments(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch appointments');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      scheduled: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
      completed: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      cancelled: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
      no_show: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
    };
    return badges[status as keyof typeof badges] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
  };

  const getPaymentBadge = (paymentStatus: string) => {
    const badges = {
      paid: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      unpaid: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      refunded: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',
    };
    return badges[paymentStatus as keyof typeof badges] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
  };

  if (loading) {
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">My Appointments</h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              View your scheduled consultations and payment status
            </p>
          </div>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
            title={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
          >
            {theme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Upcoming Appointments */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Upcoming Appointments</h2>
          {appointments.upcoming.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 text-center text-gray-500 dark:text-gray-400">
              No upcoming appointments scheduled
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {appointments.upcoming.map((appointment) => (
                  <div key={appointment.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Calendar className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                          <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                            {formatDateTime(appointment.scheduled_at)}
                          </span>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(appointment.status)} dark:opacity-80`}>
                            {appointment.status}
                          </span>
                        </div>
                        <div className="ml-8 space-y-1">
                          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <Clock className="h-4 w-4 mr-2" />
                            Duration: {appointment.duration_minutes} minutes
                          </div>
                          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <DollarSign className="h-4 w-4 mr-2" />
                            Price: {appointment.currency} {parseFloat(appointment.price).toFixed(2)}
                          </div>
                          <div className="flex items-center text-sm">
                            <span className="text-gray-600 dark:text-gray-400 mr-2">Payment:</span>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentBadge(appointment.payment_status)} dark:opacity-80`}>
                              {appointment.payment_status}
                            </span>
                          </div>
                          {appointment.notes && (
                            <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                              <strong>Notes:</strong> {appointment.notes}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Past Appointments */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Past Appointments</h2>
          {appointments.past.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 text-center text-gray-500 dark:text-gray-400">
              No past appointments
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {appointments.past.map((appointment) => (
                  <div key={appointment.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Calendar className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                          <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                            {formatDateTime(appointment.scheduled_at)}
                          </span>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(appointment.status)}`}>
                            {appointment.status}
                          </span>
                        </div>
                        <div className="ml-8 space-y-1">
                          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <Clock className="h-4 w-4 mr-2" />
                            Duration: {appointment.duration_minutes} minutes
                          </div>
                          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <DollarSign className="h-4 w-4 mr-2" />
                            Price: {appointment.currency} {parseFloat(appointment.price).toFixed(2)}
                          </div>
                          <div className="flex items-center text-sm">
                            <span className="text-gray-600 dark:text-gray-400 mr-2">Payment:</span>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentBadge(appointment.payment_status)}`}>
                              {appointment.payment_status}
                            </span>
                            {appointment.payment_method && (
                              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                                ({appointment.payment_method})
                              </span>
                            )}
                          </div>
                          {appointment.paid_at && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Paid on: {formatDateTime(appointment.paid_at)}
                            </div>
                          )}
                          {appointment.notes && (
                            <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                              <strong>Notes:</strong> {appointment.notes}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
