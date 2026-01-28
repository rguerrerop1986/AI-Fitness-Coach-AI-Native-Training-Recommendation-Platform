import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Calendar, Clock, DollarSign, CheckCircle, XCircle } from 'lucide-react';

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
      scheduled: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      no_show: 'bg-yellow-100 text-yellow-800',
    };
    return badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800';
  };

  const getPaymentBadge = (paymentStatus: string) => {
    const badges = {
      paid: 'bg-green-100 text-green-800',
      unpaid: 'bg-yellow-100 text-yellow-800',
      refunded: 'bg-gray-100 text-gray-800',
    };
    return badges[paymentStatus as keyof typeof badges] || 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold text-gray-900">My Appointments</h1>
          <p className="mt-2 text-sm text-gray-600">
            View your scheduled consultations and payment status
          </p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Upcoming Appointments */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upcoming Appointments</h2>
          {appointments.upcoming.length === 0 ? (
            <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
              No upcoming appointments scheduled
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="divide-y divide-gray-200">
                {appointments.upcoming.map((appointment) => (
                  <div key={appointment.id} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Calendar className="h-5 w-5 text-gray-400" />
                          <span className="text-lg font-medium text-gray-900">
                            {formatDateTime(appointment.scheduled_at)}
                          </span>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(appointment.status)}`}>
                            {appointment.status}
                          </span>
                        </div>
                        <div className="ml-8 space-y-1">
                          <div className="flex items-center text-sm text-gray-600">
                            <Clock className="h-4 w-4 mr-2" />
                            Duration: {appointment.duration_minutes} minutes
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <DollarSign className="h-4 w-4 mr-2" />
                            Price: {appointment.currency} {parseFloat(appointment.price).toFixed(2)}
                          </div>
                          <div className="flex items-center text-sm">
                            <span className="text-gray-600 mr-2">Payment:</span>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentBadge(appointment.payment_status)}`}>
                              {appointment.payment_status}
                            </span>
                          </div>
                          {appointment.notes && (
                            <div className="text-sm text-gray-600 mt-2">
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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Past Appointments</h2>
          {appointments.past.length === 0 ? (
            <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
              No past appointments
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="divide-y divide-gray-200">
                {appointments.past.map((appointment) => (
                  <div key={appointment.id} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Calendar className="h-5 w-5 text-gray-400" />
                          <span className="text-lg font-medium text-gray-900">
                            {formatDateTime(appointment.scheduled_at)}
                          </span>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(appointment.status)}`}>
                            {appointment.status}
                          </span>
                        </div>
                        <div className="ml-8 space-y-1">
                          <div className="flex items-center text-sm text-gray-600">
                            <Clock className="h-4 w-4 mr-2" />
                            Duration: {appointment.duration_minutes} minutes
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <DollarSign className="h-4 w-4 mr-2" />
                            Price: {appointment.currency} {parseFloat(appointment.price).toFixed(2)}
                          </div>
                          <div className="flex items-center text-sm">
                            <span className="text-gray-600 mr-2">Payment:</span>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentBadge(appointment.payment_status)}`}>
                              {appointment.payment_status}
                            </span>
                            {appointment.payment_method && (
                              <span className="ml-2 text-xs text-gray-500">
                                ({appointment.payment_method})
                              </span>
                            )}
                          </div>
                          {appointment.paid_at && (
                            <div className="text-xs text-gray-500">
                              Paid on: {formatDateTime(appointment.paid_at)}
                            </div>
                          )}
                          {appointment.notes && (
                            <div className="text-sm text-gray-600 mt-2">
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
