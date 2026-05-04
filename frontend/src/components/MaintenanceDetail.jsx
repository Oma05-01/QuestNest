import { useState, useEffect } from 'react';

export default function MaintenanceDetail({ issue, isOpen, onClose, onUpdate }) {
  const [vendors, setVendors] = useState([]);
  const [selectedVendor, setSelectedVendor] = useState('');
  const [assigning, setAssigning] = useState(false);
  
  // 🟢 Messaging States
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isSending, setIsSending] = useState(false);

  // --- Logic: Fetch Comments ---
  const fetchComments = async () => {
    if (!issue) return;
    const token = localStorage.getItem('access_token');
    const res = await fetch(`http://127.0.0.1:8000/api/maintenance/requests/${issue.id}/comments/`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    setComments(data);
  };

  const [payoutAmount, setPayoutAmount] = useState('');
const [isPaying, setIsPaying] = useState(false);

// 🟢 2. Add the payout handler function:
const handlePayout = async () => {
  if (!payoutAmount || isNaN(payoutAmount)) return alert("Please enter a valid amount.");
  if (!window.confirm(`Are you sure you want to transfer ₦${Number(payoutAmount).toLocaleString()} to the vendor?`)) return;

  setIsPaying(true);
  const token = localStorage.getItem('access_token');
  const res = await fetch(`http://127.0.0.1:8000/api/maintenance/requests/${issue.id}/pay/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ cost: payoutAmount })
  });

  const data = await res.json();
  
  if (res.ok) {
    alert("Payment successful! The request is now closed.");
    onUpdate(); // Refresh the list
    onClose();  // Close the drawer
  } else {
    // If they don't have enough money, tell them!
    if (data.error?.includes("Insufficient funds")) {
      alert(`${data.error}. Please fund your wallet first.`);
    } else {
      alert(data.error || "Payment failed.");
    }
  }
  setIsPaying(false);
};

  // --- Logic: Initial Load ---
  useEffect(() => {
    if (isOpen && issue) {
      const token = localStorage.getItem('access_token');
      
      // Fetch Vendors for assignment
      fetch('http://127.0.0.1:8000/api/maintenance/vendors/', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => setVendors(data));

      // Fetch Chat History
      fetchComments();
    }
  }, [isOpen, issue]);

  const handleSendComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setIsSending(true);

    const token = localStorage.getItem('access_token');
    const res = await fetch(`http://127.0.0.1:8000/api/maintenance/requests/${issue.id}/comments/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ body: newComment })
    });

    if (res.ok) {
      setNewComment('');
      fetchComments();
    }
    setIsSending(false);
  };

  const handleAssign = async () => {
    setAssigning(true);
    const token = localStorage.getItem('access_token');
    const res = await fetch(`http://127.0.0.1:8000/api/maintenance/requests/${issue.id}/assign/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ vendor_id: selectedVendor })
    });
    
    if (res.ok) {
      onUpdate(); 
      onClose();  
    }
    setAssigning(false);
  };

  if (!isOpen || !issue) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      
      <div className="absolute inset-y-0 right-0 max-w-full flex">
        <div className="w-screen max-w-md bg-white shadow-2xl animate-in slide-in-from-right duration-300 flex flex-col">
          
          {/* Header */}
          <div className="p-8 border-b border-slate-100 flex justify-between items-center">
            <h2 className="text-2xl font-black text-quest-navy">Request Details</h2>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
          </div>

          {/* Scrollable Body */}
          <div className="flex-1 overflow-y-auto p-8 space-y-8">
            
            {/* Issue Info */}
            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Issue</label>
              <h3 className="text-xl font-bold text-quest-navy">{issue.title}</h3>
              <p className="text-slate-500 mt-2">{issue.description}</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Unit</p>
                <p className="font-bold text-quest-navy text-sm">{issue.unit_name}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Priority</p>
                <p className={`font-bold uppercase text-xs ${issue.priority === 'urgent' ? 'text-red-500' : 'text-orange-500'}`}>
                  {issue.priority}
                </p>
              </div>
            </div>

            {/* Vendor Assignment Section */}
            <div className="space-y-4 pt-4 border-t border-slate-100">
              <h4 className="font-bold text-quest-navy">Assign Professional</h4>
              <div className="flex gap-2">
                <select 
                  value={selectedVendor}
                  onChange={(e) => setSelectedVendor(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-quest-blue text-sm"
                >
                  <option value="">Choose Vendor...</option>
                  {vendors.map(v => (
                    <option key={v.id} value={v.id}>{v.name} ({v.category})</option>
                  ))}
                </select>
                <button 
                  onClick={handleAssign}
                  disabled={!selectedVendor || assigning}
                  className="bg-quest-navy text-white px-6 rounded-xl font-bold disabled:opacity-50"
                >
                  {assigning ? '...' : 'Go'}
                </button>
              </div>
            </div>

            {issue.status === 'resolved' && (
            <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-2xl animate-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xl">
                    ✅
                </div>
                <div>
                    <h4 className="font-bold text-green-900">Work Marked Complete</h4>
                    <p className="text-xs text-green-700">The professional has finished the job. Review and issue final payment.</p>
                </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-green-200/50">
                <div>
                    <label className="block text-xs font-bold text-green-900 mb-1">Final Invoice Amount (₦)</label>
                    <input 
                    type="number" 
                    placeholder="e.g. 15000"
                    value={payoutAmount}
                    onChange={(e) => setPayoutAmount(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border-none outline-none focus:ring-2 focus:ring-green-500 shadow-sm"
                    />
                </div>
                <button 
                    onClick={handlePayout}
                    disabled={isPaying || !payoutAmount}
                    className="w-full py-4 bg-green-600 hover:bg-green-700 text-white font-black rounded-xl shadow-lg transition disabled:opacity-50"
                >
                    {isPaying ? 'Processing Transfer...' : `Pay & Close Request`}
                </button>
                </div>
            </div>
            )}

            {/* 🟢 Messaging Thread Section */}
            <div className="pt-8 border-t border-slate-100">
              <h4 className="font-bold text-quest-navy mb-4">Activity Thread</h4>
              <div className="space-y-4 mb-6">
                {comments.length === 0 ? (
                    <p className="text-center text-xs text-slate-400 italic">No messages yet.</p>
                ) : (
                    comments.map((c) => (
                    <div key={c.id} className={`flex flex-col ${c.is_me ? 'items-end' : 'items-start'}`}>
                        <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                        c.is_me ? 'bg-quest-blue text-quest-navy rounded-tr-none' : 'bg-slate-100 text-slate-700 rounded-tl-none'
                        }`}>
                        {c.body}
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1 uppercase font-bold">
                        {c.author_name} • {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                    </div>
                    ))
                )}
              </div>
            </div>
          </div>

          {/* Sticky Chat Input */}
          <div className="p-6 border-t border-slate-100 bg-white">
            <form onSubmit={handleSendComment} className="relative">
                <input 
                    type="text" placeholder="Type a message..." value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    className="w-full pl-4 pr-12 py-3 bg-slate-50 border-none rounded-xl text-sm outline-none focus:ring-2 focus:ring-quest-blue/20"
                />
                <button 
                    disabled={isSending || !newComment.trim()}
                    className="absolute right-2 top-2 p-1.5 bg-quest-navy text-white rounded-lg hover:bg-quest-blue hover:text-quest-navy transition disabled:opacity-30"
                >
                    ✈️
                </button>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}