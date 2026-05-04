import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function Leases() {
  const [leases, setLeases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- Fetch Leases ---
  const fetchLeases = async () => {
    setIsLoading(true);
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/leases/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch leases');

      const data = await response.json();
      setLeases(data.results || data);
    } catch (err) {
      setError('Could not load your lease agreements.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLeases();
  }, []);

  // --- Handle Send Lease ---
  const handleSendLease = async (id) => {
    if (!window.confirm("Are you sure you want to send this lease to the tenant for signature?")) return;
    
    setIsProcessing(true);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/leases/${id}/send/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Refresh the list to show the new "Sent" status
        fetchLeases();
      } else {
        const data = await response.json();
        alert(data.error || 'Failed to send lease.');
      }
    } catch (err) {
      alert('Network error while sending lease.');
    } finally {
      setIsProcessing(false);
    }
  };

  // --- UI Helpers ---
  const getStatusBadge = (status) => {
    switch (status) {
      case 'signed': 
      case 'active': 
        return <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">Signed</span>;
      case 'sent': 
        return <span className="bg-blue-100 text-quest-blue px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">Pending Signature</span>;
      case 'draft': 
        return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">Draft</span>;
      default: 
        return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-quest-navy">Lease Agreements</h2>
          <p className="text-slate-500">Manage and send legal documents to your tenants.</p>
        </div>
        <button className="bg-quest-navy text-white font-bold py-2.5 px-6 rounded-xl hover:bg-quest-navy/90 transition shadow-sm flex items-center gap-2 opacity-50 cursor-not-allowed" title="Generated from the Tenancies page">
          <span>+</span> Generate Lease
        </button>
      </div>

      {/* Main Content Area */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div>
          </div>
        ) : error ? (
          <div className="p-6 bg-red-50 text-red-600">{error}</div>
        ) : leases.length === 0 ? (
          <div className="text-center py-20 border-2 border-dashed border-slate-200 m-6 rounded-2xl">
            <div className="text-5xl mb-4">📄</div>
            <h3 className="text-xl font-bold text-quest-navy">No leases found</h3>
            <p className="text-slate-500 mt-2">When you convert a Tenancy into a Lease, it will appear here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500 font-semibold bg-slate-50/50">
                  <th className="py-4 px-6">Tenant & Unit</th>
                  <th className="py-4 px-6">Terms</th>
                  <th className="py-4 px-6">Signatures</th>
                  <th className="py-4 px-6 text-center">Status</th>
                  <th className="py-4 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {leases.map((lease) => (
                  <tr key={lease.id} className="hover:bg-slate-50 transition duration-150">
                    
                    {/* Tenant & Unit Info */}
                    <td className="py-4 px-6 whitespace-nowrap">
                      <p className="text-sm font-bold text-quest-navy">{lease.tenant_name || 'Tenant Name'}</p>
                      <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                        <span>🚪</span> {lease.unit_name}
                      </p>
                    </td>

                    {/* Lease Terms */}
                    <td className="py-4 px-6 whitespace-nowrap">
                      <p className="text-sm font-semibold text-slate-700">₦{Number(lease.rent_amount || 0).toLocaleString()}</p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {new Date(lease.start_date).toLocaleDateString()} - {new Date(lease.end_date).toLocaleDateString()}
                      </p>
                    </td>

                    {/* Signatures Progress */}
                    <td className="py-4 px-6">
                      <div className="flex -space-x-2">
                        {/* Mocking avatars based on signature count */}
                        {lease.signatures && lease.signatures.map((sig, idx) => (
                          <div key={idx} className="h-8 w-8 rounded-full border-2 border-white bg-green-100 text-green-700 flex items-center justify-center text-[10px] font-bold" title={`${sig.role} signed`}>
                            ✓
                          </div>
                        ))}
                        {(!lease.signatures || lease.signatures.length === 0) && (
                          <span className="text-xs text-slate-400 italic">No signatures yet</span>
                        )}
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-4 px-6 text-center">
                      {getStatusBadge(lease.status)}
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-6 text-right whitespace-nowrap space-x-3">
                      {lease.status === 'draft' && (
                        <button 
                          onClick={() => handleSendLease(lease.id)}
                          disabled={isProcessing}
                          className="text-xs font-bold text-quest-blue hover:text-quest-navy transition disabled:opacity-50"
                        >
                          Send to Tenant
                        </button>
                      )}
                      
                      <Link 
                        to={`/dashboard/leases/${lease.id}`}
                        className="text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition"
                      >
                        View Document
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}