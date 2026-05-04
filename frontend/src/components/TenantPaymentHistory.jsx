import { useState, useEffect } from 'react';

export default function TenantPaymentHistory() {
  const [payments, setPayments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPayments = async () => {
      const token = localStorage.getItem('access_token');
      
      try {
        // Replace with your exact URL from accounts/api/urls.py
        const response = await fetch('http://127.0.0.1:8000/api/wallet/transactions/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error('Failed to fetch payment history');

        const data = await response.json();
        // DRF ListAPIView usually returns paginated data inside a 'results' array
        setPayments(data.results || data); 
      } catch (err) {
        setError('Could not load payment history.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPayments();
  }, []);

  // Status Badge Helper
  const getStatusBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'SUCCESS':
      case 'COMPLETED':
        return <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">SUCCESS</span>;
      case 'PENDING':
        return <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">PENDING</span>;
      case 'FAILED':
        return <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">FAILED</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide">{status || 'UNKNOWN'}</span>;
    }
  };

  if (isLoading) {
    return <div className="text-center py-10 text-slate-500 animate-pulse">Loading transaction data...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-500">{error}</div>;
  }

  if (payments.length === 0) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
        <div className="text-4xl mb-3">🧾</div>
        <h3 className="text-lg font-bold text-quest-navy">No payments yet</h3>
        <p className="text-slate-500 text-sm mt-1">Your rent and service charge history will appear here.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-semibold bg-slate-50/50">
            <th className="py-4 px-4 rounded-tl-xl">Date</th>
            <th className="py-4 px-4">Description</th>
            <th className="py-4 px-4">Reference</th>
            <th className="py-4 px-4 text-right">Amount (₦)</th>
            <th className="py-4 px-4 text-center rounded-tr-xl">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {payments.map((payment) => (
            <tr key={payment.id} className="hover:bg-slate-50 transition duration-150 group">
              <td className="py-4 px-4 text-sm text-slate-600 whitespace-nowrap">
                {new Date(payment.created_at).toLocaleDateString('en-GB', {
                  day: 'numeric', month: 'short', year: 'numeric'
                })}
              </td>
              <td className="py-4 px-4 text-sm font-medium text-quest-navy">
                {/* Assuming nested serializer data, adjust based on your exact fields */}
                {payment.description || `Rent Payment - ${payment.tenancy?.unit?.name || 'Property'}`}
              </td>
              <td className="py-4 px-4 text-sm text-slate-500 font-mono">
                {payment.reference || payment.id.substring(0, 8)}
              </td>
              <td className="py-4 px-4 text-sm font-bold text-quest-navy text-right whitespace-nowrap">
                {Number(payment.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>
              <td className="py-4 px-4 text-center">
                {getStatusBadge(payment.status)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}