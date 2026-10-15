import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import SystemActivity from '../components/SystemActivity';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch('/api/dashboard/stats/admin/');
      if (!response.ok) throw new Error(`HTTP Error ${response.status}`);

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to load system stats.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-10 w-10 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-2xl text-sm font-medium">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">System Administration</h2>
        <p className="text-slate-500 text-sm">Monitor platform-wide activity logs and infrastructure health.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Registered Users</span>
            <span className="p-2.5 bg-purple-50 text-purple-600 rounded-xl font-bold">👥</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            {Number(stats?.total_users || 0).toLocaleString()}
          </span>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Active Escrows</span>
            <span className="p-2.5 bg-blue-50 text-blue-600 rounded-xl font-bold">🛡️</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            {Number(stats?.active_escrows || 0).toLocaleString()}
          </span>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 border-l-4 border-l-emerald-500 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">System Health</span>
            <span className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl font-bold">⚡</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-2xl font-black text-slate-900 uppercase">
              {stats?.system_health || 'OPERATIONAL'}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-900">Live System Activity</h3>
          <button
            onClick={fetchDashboardData}
            className="text-xs font-bold text-slate-500 hover:text-slate-900 transition flex items-center gap-1.5"
          >
            <span>🔄</span> Refresh Logs
          </button>
        </div>
        <div className="p-4">
          <SystemActivity />
        </div>
      </div>
    </div>
  );
}