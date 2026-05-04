import { useState, useEffect } from 'react';

export default function LandlordTenancies() {
  const [tenancies, setTenancies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTenancies = async () => {
      const token = localStorage.getItem('access_token');
      
      try {
        // Adjust the URL if your accounts/api/urls.py mapping is different
        const response = await fetch('http://127.0.0.1:8000/api/dashboard/tenancies/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error('Failed to fetch tenancies');

        const data = await response.json();
        // DRF ListAPIView typically paginates into a 'results' array
        setTenancies(data.results || data); 
      } catch (err) {
        setError('Could not load active tenancies.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTenancies();
  }, []);

  // Status Badge Helper
  const getStatusBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">ACTIVE</span>;
      case 'EXPIRING_SOON':
        return <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">EXPIRING SOON</span>;
      case 'OVERDUE':
        return <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">OVERDUE</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">{status || 'UNKNOWN'}</span>;
    }
  };

  if (isLoading) {
    return <div className="text-center py-10 text-slate-500 animate-pulse">Loading tenancy data...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-500">{error}</div>;
  }

  if (tenancies.length === 0) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
        <div className="text-4xl mb-3">🏢</div>
        <h3 className="text-lg font-bold text-quest-navy">No active tenancies</h3>
        <p className="text-slate-500 text-sm mt-1">When you onboard tenants to your properties, they will appear here.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-semibold bg-slate-50/50">
            <th className="py-4 px-4 rounded-tl-xl">Tenant</th>
            <th className="py-4 px-4">Property / Unit</th>
            <th className="py-4 px-4 text-right">Rent Amount (₦)</th>
            <th className="py-4 px-4">Next Payment Date</th>
            <th className="py-4 px-4 text-center rounded-tr-xl">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {tenancies.map((tenancy) => (
            <tr key={tenancy.id} className="hover:bg-slate-50 transition duration-150 group cursor-pointer">
              <td className="py-4 px-4 whitespace-nowrap">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-quest-blue/20 flex items-center justify-center text-quest-blue font-bold text-xs">
                    {/* Generates Initials */}
                    {tenancy.tenant?.name?.substring(0, 2).toUpperCase() || 'T'}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-quest-navy">{tenancy.tenant?.name || 'Unknown Tenant'}</p>
                    <p className="text-xs text-slate-500">{tenancy.tenant?.email}</p>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4 text-sm font-medium text-slate-700">
                {tenancy.unit?.name || 'Unassigned Unit'}
              </td>
              <td className="py-4 px-4 text-sm font-bold text-quest-navy text-right whitespace-nowrap">
                {Number(tenancy.rent_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>
              <td className="py-4 px-4 text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  <span>📅</span>
                  {tenancy.next_payment_date 
                    ? new Date(tenancy.next_payment_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
                    : 'N/A'
                  }
                </div>
              </td>
              <td className="py-4 px-4 text-center">
                {getStatusBadge(tenancy.status || 'ACTIVE')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}