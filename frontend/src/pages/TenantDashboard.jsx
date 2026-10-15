import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../api/client';
import TenantPaymentHistory from '../components/TenantPaymentHistory';

export default function TenantDashboard({ workspace }) {
  const [stats, setStats] = useState({ total_paid: 0, next_rent_due: null, active_leases: 0 });
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const response = await apiFetch('/api/dashboard/stats/personal/');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        console.warn(`[TenantDashboard] Endpoint returned status ${response.status}. Using fallbacks.`);
      }
    } catch (err) {
      console.error('[TenantDashboard] Fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [workspace?.id]);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-10 w-10 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">

      {/* 1. Header with Resident Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold uppercase tracking-wider mb-2">
            <span>👤 Personal Resident Hub</span>
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Personal Workspace</h2>
          <p className="text-slate-500 text-sm mt-0.5">Manage your tenancy, make rent payments, and report issues.</p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/dashboard/maintenance"
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition shadow-sm flex items-center gap-2"
          >
            <span>🔧</span> Report Issue
          </Link>

          <Link
            to="/dashboard/wallet"
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition shadow-md shadow-blue-600/20 flex items-center gap-2"
          >
            <span>💳</span> Pay Rent / Escrow
          </Link>
        </div>
      </div>

      {/* 2. Key Resident Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Rent Paid</span>
            <span className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl font-bold">💳</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            ₦{Number(stats?.total_paid || 0).toLocaleString()}
          </span>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 border-l-4 border-l-blue-600 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Next Rent Due</span>
            <span className="p-2.5 bg-amber-50 text-amber-600 rounded-xl font-bold">📅</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            {stats?.next_rent_due ? new Date(stats.next_rent_due).toLocaleDateString() : 'No pending rent'}
          </span>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Active Leases</span>
            <span className="p-2.5 bg-blue-50 text-blue-600 rounded-xl font-bold">🏠</span>
          </div>
          <span className="text-3xl font-black text-slate-900">
            {stats?.active_leases || 0}
          </span>
        </div>
      </div>

      {/* 3. Quick Shortcuts Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          to="/dashboard/leases"
          className="p-5 bg-white rounded-2xl border border-slate-200/80 hover:border-blue-500/50 hover:shadow-md transition group flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl font-bold">📄</div>
            <div>
              <h4 className="font-bold text-slate-900 text-sm">Lease Agreements</h4>
              <p className="text-xs text-slate-500">View terms & contract PDFs</p>
            </div>
          </div>
          <span className="text-slate-400 group-hover:text-blue-600 transition">→</span>
        </Link>

        <Link
          to="/dashboard/maintenance"
          className="p-5 bg-white rounded-2xl border border-slate-200/80 hover:border-blue-500/50 hover:shadow-md transition group flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl font-bold">🔧</div>
            <div>
              <h4 className="font-bold text-slate-900 text-sm">Maintenance Hub</h4>
              <p className="text-xs text-slate-500">Track open repair requests</p>
            </div>
          </div>
          <span className="text-slate-400 group-hover:text-blue-600 transition">→</span>
        </Link>

        <Link
          to="/dashboard/messages"
          className="p-5 bg-white rounded-2xl border border-slate-200/80 hover:border-blue-500/50 hover:shadow-md transition group flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl font-bold">💬</div>
            <div>
              <h4 className="font-bold text-slate-900 text-sm">Landlord Chat</h4>
              <p className="text-xs text-slate-500">Direct inbox messages</p>
            </div>
          </div>
          <span className="text-slate-400 group-hover:text-blue-600 transition">→</span>
        </Link>
      </div>

      {/* 4. Payment History Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-900">Recent Payment Transactions</h3>
        </div>
        <div className="p-4">
          <TenantPaymentHistory />
        </div>
      </div>

    </div>
  );
}