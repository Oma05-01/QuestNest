import { useState, useEffect } from 'react';

export default function Properties() {
  // Data State
  const [assets, setAssets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({ name: '', location: '' });
  const [formError, setFormError] = useState(null);

  // --- Fetch Properties ---
  const fetchProperties = async () => {
    setIsLoading(true);
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/assets/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch properties');

      const data = await response.json();
      setAssets(data.results || data);
    } catch (err) {
      setError('Could not load your property portfolio.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProperties();
  }, []);

  // --- Handle Create Property ---
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/assets/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        // Success! Close modal, clear form, and refresh the list
        setIsModalOpen(false);
        setFormData({ name: '', location: '' });
        fetchProperties(); 
      } else {
        const data = await response.json();
        setFormError(data.detail || 'Failed to create property. Check your inputs.');
      }
    } catch (err) {
      setFormError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- UI Helpers ---
  const getStatusBadge = (status) => {
    switch(status) {
      case 'listed': return <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">Listed</span>;
      case 'draft': return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">Draft</span>;
      default: return <span className="bg-blue-100 text-quest-blue px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 relative">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-quest-navy">Properties</h2>
          <p className="text-slate-500">Manage your buildings, estates, and individual units.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-quest-navy text-white font-bold py-2.5 px-6 rounded-xl hover:bg-quest-navy/90 transition shadow-sm flex items-center gap-2"
        >
          <span>+</span> Add Property
        </button>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl">{error}</div>
      ) : assets.length === 0 ? (
        <div className="text-center py-20 bg-white border-2 border-dashed border-slate-200 rounded-2xl">
          <div className="text-5xl mb-4">🏢</div>
          <h3 className="text-xl font-bold text-quest-navy">No properties yet</h3>
          <p className="text-slate-500 mt-2 mb-6">Add your first property to start accepting tenants and payments.</p>
          <button onClick={() => setIsModalOpen(true)} className="text-quest-blue font-bold hover:underline">
            + Create your first asset
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assets.map((asset) => (
            <div key={asset.id} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition cursor-pointer group">
              <div className="flex justify-between items-start mb-4">
                <div className="h-12 w-12 bg-blue-50 rounded-xl flex items-center justify-center text-2xl group-hover:scale-105 transition">
                  🏠
                </div>
                {getStatusBadge(asset.status || 'draft')}
              </div>
              <h3 className="text-lg font-bold text-quest-navy line-clamp-1">{asset.name}</h3>
              <p className="text-sm text-slate-500 mt-1 flex items-center gap-1.5 line-clamp-1">
                <span>📍</span> {asset.location}
              </p>
              
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">
                  {asset.is_verified ? '✅ Verified' : '⏳ Pending Verification'}
                </span>
                <span className="text-sm font-bold text-quest-blue group-hover:text-quest-navy transition">
                  Manage &rarr;
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 🟢 Slide-Over Modal for Creating a Property */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h3 className="font-bold text-quest-navy text-lg">Add New Property</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-xl font-bold">&times;</button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-5">
              {formError && (
                <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-sm font-semibold text-quest-navy mb-1.5">Property Name</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. The Matrix Apartments"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none transition"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-quest-navy mb-1.5">Full Location Address</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. 12 Admiralty Way, Lekki Phase 1"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none transition"
                />
              </div>

              <div className="pt-4 flex gap-3">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-3 px-4 font-bold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200 transition"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="flex-1 py-3 px-4 font-bold text-white bg-quest-navy rounded-xl hover:bg-quest-navy/90 transition shadow-md disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save Property'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}