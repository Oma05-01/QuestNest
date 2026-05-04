import { useState, useEffect } from 'react';

export default function Wallet() {
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [escrows, setEscrows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFundModalOpen, setIsFundModalOpen] = useState(false);
  const [fundAmount, setFundAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);


  const handleInitializeFunding = async (e) => {
  e.preventDefault();
  setIsProcessing(true);
  const token = localStorage.getItem('access_token');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/wallet/fund/init/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ amount: fundAmount })
    });

    const data = await response.json();
    if (response.ok) {
      // 🟢 Redirect the user to Paystack's secure checkout
      window.location.href = data.authorization_url;
    } else {
      alert(data.error || "Failed to start payment");
    }
  } catch (err) {
    alert("Network error");
  } finally {
    setIsProcessing(false);
  }
};

  // --- Fetch Financial Data ---
  const fetchFinancials = async () => {
    setIsLoading(true);
    const token = localStorage.getItem('access_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      // We can fetch Wallet, Transactions, and Escrows all at the same time!
      const [walletRes, transRes, escrowRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/wallet/', { headers }),
        fetch('http://127.0.0.1:8000/api/wallet/transactions/', { headers }),
        fetch('http://127.0.0.1:8000/api/escrows/', { headers })
      ]);

      if (!walletRes.ok) throw new Error('Failed to fetch wallet data');

      const walletData = await walletRes.json();
      const transData = await transRes.json();
      const escrowData = await escrowRes.json();

      setWallet(walletData);
      setTransactions(transData.results || transData);
      setEscrows(escrowData.results || escrowData);
    } catch (err) {
      setError('Could not load financial dashboard.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFinancials();
  }, []);

  // Calculate total locked in Escrow (only active ones)
  const totalEscrow = escrows
    .filter(e => e.status !== 'released' && e.status !== 'refunded')
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);

  if (isLoading) return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded-xl">{error}</div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-10">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-quest-navy">Escrow Wallet</h2>
        <p className="text-slate-500">Manage your available funds and track active rent escrows.</p>
      </div>

      {/* 💳 Top Financial Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Available Balance Card */}
        <div className="bg-quest-navy text-white p-8 rounded-3xl shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-10 text-8xl">💳</div>
          <p className="text-slate-300 font-semibold mb-2">Available Balance</p>
          <h3 className="text-4xl md:text-5xl font-black mb-6">
            ₦{Number(wallet?.balance || 0).toLocaleString()}
          </h3>
          <div className="flex gap-4">
            <button 
                onClick={() => setIsFundModalOpen(true)}
                className="bg-quest-blue text-quest-navy font-bold py-2.5 px-6 rounded-xl hover:bg-opacity-90 transition shadow-sm"
                >
                Fund Wallet
            </button>
            <button className="bg-white/10 text-white font-bold py-2.5 px-6 rounded-xl hover:bg-white/20 transition">
              Withdraw
            </button>
          </div>
        </div>

        {/* Locked in Escrow Card */}
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-2">
              <p className="text-slate-500 font-semibold">Protected in Escrow</p>
              <span className="bg-orange-100 text-orange-600 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                🔒 Locked
              </span>
            </div>
            <h3 className="text-4xl md:text-5xl font-black text-slate-800">
              ₦{totalEscrow.toLocaleString()}
            </h3>
          </div>
          <p className="text-sm text-slate-400 mt-6">
            These funds are held securely until lease conditions are met or rent due dates pass.
          </p>
        </div>
      </div>

      {/* 🔒 Active Escrows Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-lg font-bold text-quest-navy">Active Escrow Contracts</h3>
        </div>
        
        {escrows.length === 0 ? (
          <div className="p-10 text-center text-slate-500">No active escrow contracts.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wider text-slate-400 font-semibold bg-white">
                  <th className="py-4 px-6">Property / Unit</th>
                  <th className="py-4 px-6">Tenant</th>
                  <th className="py-4 px-6 text-right">Amount (₦)</th>
                  <th className="py-4 px-6 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {escrows.map((escrow) => (
                  <tr key={escrow.id} className="hover:bg-slate-50 transition">
                    <td className="py-4 px-6 font-bold text-quest-navy">{escrow.unit_name}</td>
                    <td className="py-4 px-6 text-slate-600">{escrow.tenant_name}</td>
                    <td className="py-4 px-6 text-right font-bold text-slate-700">
                      {Number(escrow.amount).toLocaleString()}
                    </td>
                    <td className="py-4 px-6 text-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                        escrow.status === 'held' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {escrow.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 💸 Transaction History Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-lg font-bold text-quest-navy">Recent Transactions</h3>
        </div>
        
        {transactions.length === 0 ? (
          <div className="p-10 text-center text-slate-500">No recent transactions in your wallet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wider text-slate-400 font-semibold bg-white">
                  <th className="py-4 px-6">Date</th>
                  <th className="py-4 px-6">Description</th>
                  <th className="py-4 px-6">Ref</th>
                  <th className="py-4 px-6 text-right">Amount (₦)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50 transition">
                    <td className="py-4 px-6 text-sm text-slate-500">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6">
                      <p className="text-sm font-bold text-quest-navy">{tx.description}</p>
                      <p className="text-xs text-slate-400 uppercase">{tx.transaction_type}</p>
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-400 font-mono">{tx.reference || 'N/A'}</td>
                    <td className={`py-4 px-6 text-right font-bold ${
                      tx.transaction_type === 'credit' || tx.transaction_type === 'deposit' 
                        ? 'text-green-600' 
                        : 'text-slate-700'
                    }`}>
                      {tx.transaction_type === 'credit' ? '+' : '-'}
                      {Number(tx.amount).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isFundModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
            <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl p-6 overflow-hidden zoom-in-95">
            <h3 className="text-xl font-bold text-quest-navy mb-2">Fund your Wallet</h3>
            <p className="text-sm text-slate-500 mb-6">Enter the amount you wish to deposit. You will be redirected to Paystack's secure gateway.</p>
            
            <form onSubmit={handleInitializeFunding} className="space-y-4">
                <div>
                <label className="block text-sm font-semibold mb-1">Amount (₦)</label>
                <input 
                    type="number" required min="100" placeholder="50000"
                    value={fundAmount} onChange={e => setFundAmount(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border outline-none focus:ring-2 focus:ring-quest-blue"
                />
                </div>
                <div className="flex gap-3">
                <button type="button" onClick={() => setIsFundModalOpen(false)} className="flex-1 py-3 bg-slate-100 rounded-xl font-bold">Cancel</button>
                <button type="submit" disabled={isProcessing} className="flex-1 py-3 bg-quest-navy text-white rounded-xl font-bold">
                    {isProcessing ? 'Connecting...' : 'Proceed to Pay'}
                </button>
                </div>
            </form>
            </div>
        </div>
        )}

    </div>
  );
}