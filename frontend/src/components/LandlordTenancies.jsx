import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

export default function LandlordTenancies({ workspace }) {
  const [tenancies, setTenancies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTenancies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiFetch('/api/dashboard/tenancies/');

      if (!response.ok) throw new Error(`HTTP Error ${response.status}`);

      const data = await response.json();
      const list = Array.isArray(data) ? data : data.results || [];
      setTenancies(list);
    } catch (err) {
      console.error('Failed to fetch tenancies:', err);
      setError('Could not load active tenancies for this portfolio.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTenancies();
  }, [workspace?.id]);

  // Status Badge Helper
  const getStatusBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border border-emerald-200/60">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Active
          </span>
        );
      case 'EXPIRING_SOON':
        return (
          <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-700 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border border-amber-200/60">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
            Expiring Soon
          </span>
        );
      case 'OVERDUE':
        return (
          <span className="inline-flex items-center gap-1.5 bg-rose-50 text-rose-700 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border border-rose-200/60">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
            Overdue
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider">
            {status || 'Pending'}
          </span>
        );
    }
  };

  const getInitials = (name) => {
    if (!name) return 'TN';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  if (isLoading) {
    return (
      <div className="py-12 flex flex-col items-center justify-center gap-3">
        <div className="h-8 w-8 rounded-full border-3 border-slate-200 border-t-blue-600 animate-spin" />
        <span className="text-xs font-semibold text-slate-400">Loading active tenancies...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200/80 rounded-2xl text-xs font-semibold text-red-600 text-center">
        {error}
      </div>
    );
  }

  if (tenancies.length === 0) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50 p-6">
        <div className="text-4xl mb-3">🏢</div>
        <h3 className="text-base font-bold text-slate-900">No active tenancies in this workspace</h3>
        <p className="text-slate-500 text-xs mt-1 max-w-md mx-auto">
          When you add tenants and issue leases in this business workspace, active tenancy records will appear here automatically.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto custom-scrollbar">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-200/80 text-[11px] uppercase tracking-wider text-slate-400 font-extrabold bg-slate-50/50">
            <th className="py-3.5 px-4 rounded-tl-xl">Tenant</th>
            <th className="py-3.5 px-4">Property / Unit</th>
            <th className="py-3.5 px-4 text-right">Rent Amount</th>
            <th className="py-3.5 px-4">Next Payment</th>
            <th className="py-3.5 px-4 text-center rounded-tr-xl">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-xs">
          {tenancies.map((tenancy) => (
            <tr
              key={tenancy.id}
              className="hover:bg-slate-50/80 transition-colors duration-150 group"
            >
              <td className="py-4 px-4 whitespace-nowrap">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-xl bg-blue-50 text-blue-600 font-bold flex items-center justify-center shrink-0 border border-blue-100 text-xs">
                    {getInitials(tenancy.tenant?.name || tenancy.tenant_name)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-slate-900 truncate">
                      {tenancy.tenant?.name || tenancy.tenant_name || 'Resident'}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate">
                      {tenancy.tenant?.email || tenancy.tenant_email || 'No email on file'}
                    </p>
                  </div>
                </div>
              </td>

              <td className="py-4 px-4 whitespace-nowrap">
                <span className="font-semibold text-slate-800">
                  {tenancy.unit?.name || tenancy.unit_name || 'Unassigned Unit'}
                </span>
                {tenancy.property_name && (
                  <p className="text-[11px] text-slate-400 truncate">{tenancy.property_name}</p>
                )}
              </td>

              <td className="py-4 px-4 text-right font-black text-slate-900 whitespace-nowrap">
                ₦{Number(tenancy.rent_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>

              <td className="py-4 px-4 whitespace-nowrap font-medium text-slate-600">
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-400">📅</span>
                  {tenancy.next_payment_date
                    ? new Date(tenancy.next_payment_date).toLocaleDateString('en-GB', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })
                    : 'N/A'}
                </div>
              </td>

              <td className="py-4 px-4 text-center whitespace-nowrap">
                {getStatusBadge(tenancy.status || 'ACTIVE')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}