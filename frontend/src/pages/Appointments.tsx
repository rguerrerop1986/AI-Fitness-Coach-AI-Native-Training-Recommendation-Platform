import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useTranslation } from 'react-i18next';
import { Calendar, Plus, CheckCircle, XCircle, Clock, DollarSign } from 'lucide-react';

interface Appointment {
  id: number;
  client: number;
  client_detail: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
  };
  coach: number;
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

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export default function Appointments() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [formData, setFormData] = useState({
    client: '',
    scheduled_at: '',
    duration_minutes: 60,
    price: '',
    currency: 'MXN',
    notes: '',
  });

  useEffect(() => {
    fetchAppointments();
    fetchClients();
  }, []);

  const fetchAppointments = async () => {
    try {
      const response = await api.get('/appointments/');
      setAppointments(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch appointments');
    } finally {
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients/');
      setClients(response.data.results || response.data);
    } catch (err: any) {
      console.error('Failed to fetch clients:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingAppointment) {
        await api.patch(`/appointments/${editingAppointment.id}/`, formData);
      } else {
        await api.post('/appointments/', formData);
      }
      setShowModal(false);
      setFormData({
        client: '',
        scheduled_at: '',
        duration_minutes: 60,
        price: '',
        currency: 'MXN',
        notes: '',
      });
      setEditingAppointment(null);
      fetchAppointments();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to save appointment');
    }
  };

  const handleMarkCompleted = async (id: number) => {
    try {
      await api.patch(`/appointments/${id}/mark_completed/`);
      fetchAppointments();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to mark as completed');
    }
  };

  const handleMarkPaid = async (id: number, paymentMethod: string) => {
    try {
      await api.patch(`/appointments/${id}/mark_paid/`, {
        payment_method: paymentMethod,
      });
      fetchAppointments();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to mark as paid');
    }
  };

  const handleCancel = async (id: number) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      await api.patch(`/appointments/${id}/cancel/`);
      fetchAppointments();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to cancel appointment');
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Appointments</h1>
              <p className="mt-2 text-sm text-gray-600">
                Manage client consultations and payments
              </p>
            </div>
            <button
              onClick={() => {
                setEditingAppointment(null);
                setFormData({
                  client: '',
                  scheduled_at: '',
                  duration_minutes: 60,
                  price: '',
                  currency: 'MXN',
                  notes: '',
                });
                setShowModal(true);
              }}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              New Appointment
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Appointments Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Scheduled
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Payment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {appointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {appointment.client_detail?.first_name} {appointment.client_detail?.last_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {appointment.client_detail?.email}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDateTime(appointment.scheduled_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {appointment.duration_minutes} min
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(appointment.status)}`}>
                        {appointment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {appointment.currency} {parseFloat(appointment.price).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getPaymentBadge(appointment.payment_status)}`}>
                        {appointment.payment_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        {appointment.status === 'scheduled' && (
                          <button
                            onClick={() => handleMarkCompleted(appointment.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Mark as Completed"
                          >
                            <CheckCircle className="h-5 w-5" />
                          </button>
                        )}
                        {appointment.status === 'completed' && appointment.payment_status === 'unpaid' && (
                          <button
                            onClick={() => {
                              const method = prompt('Enter payment method (cash, transfer, card, other):');
                              if (method) handleMarkPaid(appointment.id, method);
                            }}
                            className="text-blue-600 hover:text-blue-900"
                            title="Mark as Paid"
                          >
                            <DollarSign className="h-5 w-5" />
                          </button>
                        )}
                        {appointment.status === 'scheduled' && (
                          <button
                            onClick={() => handleCancel(appointment.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Cancel"
                          >
                            <XCircle className="h-5 w-5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Create/Edit Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {editingAppointment ? 'Edit Appointment' : 'New Appointment'}
                </h3>
                <form onSubmit={handleSubmit}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client
                    </label>
                    <select
                      required
                      value={formData.client}
                      onChange={(e) => setFormData({ ...formData, client: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select a client</option>
                      {clients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.first_name} {client.last_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Scheduled Date & Time
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={formData.scheduled_at}
                      onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Duration (minutes)
                    </label>
                    <input
                      type="number"
                      required
                      min="15"
                      value={formData.duration_minutes}
                      onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Price
                    </label>
                    <div className="flex">
                      <input
                        type="number"
                        required
                        step="0.01"
                        min="0.01"
                        value={formData.price}
                        onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <select
                        value={formData.currency}
                        onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                        className="px-3 py-2 border border-gray-300 border-l-0 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="MXN">MXN</option>
                        <option value="USD">USD</option>
                      </select>
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        setShowModal(false);
                        setEditingAppointment(null);
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                      {editingAppointment ? 'Update' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
