import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import LandlordTenancies from '../components/LandlordTenancies';

export default function LandlordDashboard({ workspace }) {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await apiFetch('/api/dashboard/stats/business/');
        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);

        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError(err.message || 'Failed to load portfolio stats.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [workspace?.id]);

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
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Portfolio Overview</h2>
        <p className="text-slate-500 text-sm">
          Operating Context: <span className="font-semibold text-slate-800">{workspace?.name || 'Business Workspace'}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Revenue</span>
            <span className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl font-bold">📈</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            ₦{Number(stats?.total_revenue || 0).toLocaleString()}
          </span>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 border-l-4 border-l-blue-600 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Protected Escrow</span>
            <span className="p-2.5 bg-blue-50 text-blue-600 rounded-xl font-bold">🛡️</span>
          </div>
          <span className="text-3xl font-black text-blue-600">
            ₦{Number(stats?.escrow_balance || 0).toLocaleString()}
          </span>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Active Occupancy</span>
            <span className="p-2.5 bg-amber-50 text-amber-600 rounded-xl font-bold">🔑</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            {stats?.active_tenants || 0}
          </span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-slate-900">Active Tenancies</h3>
        </div>
        <LandlordTenancies />
      </div>
    </div>
  );
}