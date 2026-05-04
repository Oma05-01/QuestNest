import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

export default function LeaseViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isFunding, setIsFunding] = useState(false);
  
  const [lease, setLease] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSigning, setIsSigning] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState(null);

  const handleFundEscrow = async (escrowId) => {
    if (!window.confirm("This will transfer funds from your wallet to the escrow. Proceed?")) return;
    
    setIsFunding(true);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/escrows/${escrowId}/fund/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok) {
        alert("Lease funded successfully!");
        fetchLease(); // Refresh to update status from 'pending' to 'funded'
      } else {
        // If they have insufficient funds, we can redirect them to the wallet
        if (data.error?.includes("Insufficient funds")) {
          if (window.confirm(`${data.error}. Would you like to fund your wallet now?`)) {
            navigate('/dashboard/wallet');
          }
        } else {
          alert(data.error || "Failed to fund escrow.");
        }
      }
    } catch (err) {
      alert("Network error. Please try again.");
    } finally {
      setIsFunding(false);
    }
  };

  // --- Fetch Lease Details ---
  const fetchLease = async () => {
    setIsLoading(true);
    const token = localStorage.getItem('access_token');
    const userString = localStorage.getItem('user');
    
    if (userString) {
      setCurrentUserRole(JSON.parse(userString).role);
    }
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/leases/${id}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.status === 404) {
        navigate('/dashboard/leases');
        return;
      }
      if (!response.ok) throw new Error('Failed to load document');

      const data = await response.json();
      setLease(data);
    } catch (err) {
      setError('Could not load the lease document.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLease();
  }, [id]);

  // --- Handle Signing ---
  const handleSign = async () => {
    if (!window.confirm("By clicking OK, you are legally signing this document. Proceed?")) return;
    
    setIsSigning(true);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/leases/${id}/sign/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        alert('Document signed successfully!');
        fetchLease(); // Refresh to show the new signature
      } else {
        const errData = await response.json();
        alert(errData.error || 'Failed to sign the document.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    } finally {
      setIsSigning(false);
    }
  };

  if (isLoading) return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div></div>;
  if (error || !lease) return <div className="p-4 bg-red-50 text-red-600 rounded-xl">{error || 'Lease not found'}</div>;

  // Check if the current user needs to sign
  const expectedRoleToSign = currentUserRole === 'tenant' ? 'tenant' : 'landlord';
  const hasSigned = lease.signatures?.some(sig => sig.role.toLowerCase() === expectedRoleToSign);
  const canSign = (lease.status === 'sent' || lease.status === 'signed') && !hasSigned;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500 pb-20">
      
      <Link to="/dashboard/leases" className="text-sm font-semibold text-slate-500 hover:text-quest-navy transition flex items-center gap-2 w-max">
        &larr; Back to Leases
      </Link>

      {/* 📄 DOCUMENT CONTAINER */}
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        
        {/* Document Header */}
        <div className="bg-slate-50 p-8 border-b border-slate-200 text-center">
          <div className="h-16 w-16 bg-quest-navy text-white rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4 shadow-md">
            ⚖️
          </div>
          <h1 className="text-2xl font-black text-quest-navy uppercase tracking-widest mb-2">Residential Lease Agreement</h1>
          <p className="text-slate-500 font-medium">For the property located at: <span className="text-slate-800">{lease.unit_name}</span></p>
          
          <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm">
            <span className="bg-white border border-slate-200 px-4 py-2 rounded-lg shadow-sm">
              <span className="text-slate-400">Rent:</span> <strong className="text-quest-navy">₦{Number(lease.rent_amount).toLocaleString()}/yr</strong>
            </span>
            <span className="bg-white border border-slate-200 px-4 py-2 rounded-lg shadow-sm">
              <span className="text-slate-400">Deposit:</span> <strong className="text-quest-navy">₦{Number(lease.deposit_amount).toLocaleString()}</strong>
            </span>
            <span className="bg-white border border-slate-200 px-4 py-2 rounded-lg shadow-sm">
              <span className="text-slate-400">Term:</span> <strong className="text-quest-navy">{new Date(lease.start_date).toLocaleDateString()} - {new Date(lease.end_date).toLocaleDateString()}</strong>
            </span>
          </div>
        </div>

        {/* Document Clauses */}
        <div className="p-8 md:p-12 space-y-8 bg-white font-serif text-slate-800 leading-relaxed">
          {(!lease.clauses || lease.clauses.length === 0) ? (
            <p className="text-center text-slate-400 italic font-sans">No clauses found for this agreement.</p>
          ) : (
            lease.clauses.map((clause, index) => (
              <div key={clause.id} className="space-y-2">
                <h3 className="text-lg font-bold uppercase tracking-wide">
                  {index + 1}. {clause.title || 'Standard Clause'}
                </h3>
                <p className="text-justify">{clause.body}</p>
              </div>
            ))
          )}
        </div>

        {/* Signatures Section */}
        <div className="bg-slate-50 p-8 border-t border-slate-200">
          <h3 className="text-lg font-bold text-quest-navy mb-6">Execution & Signatures</h3>
          
          {/* 1. SIGNATURE GRID (Keep this just for the two boxes) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Landlord Signature Block */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 bg-white relative">
              <span className="absolute -top-3 left-4 bg-slate-50 px-2 text-xs font-bold text-slate-400 uppercase">Landlord</span>
              {lease.signatures?.find(s => s.role === 'landlord') ? (
                <div className="text-center space-y-2 pt-2">
                  <div className="font-[Signature] text-4xl text-quest-blue select-none font-style: italic">
                    {lease.signatures.find(s => s.role === 'landlord').signed_name}
                  </div>
                  <p className="text-xs text-slate-400">Signed on {new Date(lease.signatures.find(s => s.role === 'landlord').signed_at).toLocaleString()}</p>
                </div>
              ) : (
                <div className="h-20 flex items-center justify-center text-slate-400 italic text-sm">Awaiting Signature</div>
              )}
            </div>

            {/* Tenant Signature Block */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 bg-white relative">
              <span className="absolute -top-3 left-4 bg-slate-50 px-2 text-xs font-bold text-slate-400 uppercase">Tenant</span>
              {lease.signatures?.find(s => s.role === 'tenant') ? (
                <div className="text-center space-y-2 pt-2">
                  <div className="font-[Signature] text-4xl text-quest-blue select-none font-style: italic">
                    {lease.signatures.find(s => s.role === 'tenant').signed_name}
                  </div>
                  <p className="text-xs text-slate-400">Signed on {new Date(lease.signatures.find(s => s.role === 'tenant').signed_at).toLocaleString()}</p>
                </div>
              ) : (
                <div className="h-20 flex items-center justify-center text-slate-400 italic text-sm">Awaiting Signature</div>
              )}
            </div>
          </div> {/* End Grid */}

          {/* 🟢 2. FINANCIAL COMMITMENT (Moved outside grid to span full width) */}
          {lease.status === 'signed' && (
            <div className="mt-8 p-6 bg-quest-blue/10 border border-quest-blue/20 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 animate-in slide-in-from-bottom-4 duration-500">
              <div>
                <h4 className="text-lg font-bold text-quest-navy">Step 2: Financial Commitment</h4>
                <p className="text-sm text-slate-600">The lease is signed. Now, fund the escrow to secure your tenancy.</p>
              </div>
              
              {lease.escrow_status === 'pending' ? (
                <button
                  onClick={() => handleFundEscrow(lease.escrow_id)}
                  disabled={isFunding}
                  className="bg-quest-navy text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition disabled:opacity-50 whitespace-nowrap"
                >
                  {isFunding ? "Processing..." : `Pay ₦${Number(lease.rent_amount + lease.deposit_amount).toLocaleString()}`}
                </button>
              ) : (
                <div className="flex items-center gap-2 text-green-600 font-bold bg-white px-6 py-2 rounded-lg shadow-sm">
                  <span>✅</span> Escrow Fully Funded
                </div>
              )}
            </div>
          )}

          {/* 3. Action Button for Current User */}
          {canSign && (
            <div className="mt-8 flex justify-center">
              <button 
                onClick={handleSign}
                disabled={isSigning}
                className="bg-quest-blue text-quest-navy font-black text-lg py-4 px-10 rounded-xl hover:bg-opacity-90 transition shadow-xl disabled:opacity-50 flex items-center gap-2"
              >
                <span>✍️</span> {isSigning ? 'Processing...' : 'I Agree & Sign Document'}
              </button>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}