import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

export default function PropertyDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  // Property State
  const [asset, setAsset] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Units State
  const [units, setUnits] = useState([]);
  const [isUnitsLoading, setIsUnitsLoading] = useState(true);

  // Modal States
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isUnitModalOpen, setIsUnitModalOpen] = useState(false);
  
  // Form States
  const [formData, setFormData] = useState({ name: '', location: '' });
  const [unitFormData, setUnitFormData] = useState({ name: '', rent_amount: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [unitFormError, setUnitFormError] = useState(null);

  // --- Fetch Data ---
  const fetchPropertyAndUnits = useCallback(async () => {
    setIsLoading(true);
    setIsUnitsLoading(true);
    const token = localStorage.getItem('access_token');
    
    try {
      // 1. Fetch Property Info
      const propRes = await fetch(`http://127.0.0.1:8000/api/assets/${id}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (propRes.status === 404) {
        navigate('/dashboard/properties');
        return;
      }
      if (!propRes.ok) throw new Error('Failed to fetch property details');

      const propData = await propRes.json();
      setAsset(propData);
      setFormData({ name: propData.name, location: propData.location });

      // 2. Fetch Units
      const unitRes = await fetch(`http://127.0.0.1:8000/api/assets/${id}/units/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (unitRes.ok) {
        const unitData = await unitRes.json();
        setUnits(unitData.results || unitData);
      }
    } catch (err) {
      setError('Could not load property data.');
    } finally {
      setIsLoading(false);
      setIsUnitsLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    fetchPropertyAndUnits();
  }, [fetchPropertyAndUnits]);

  // --- Handle Property Update ---
  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/assets/${id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setIsEditModalOpen(false);
        fetchPropertyAndUnits(); 
      }
    } catch (err) {
      alert('Network error.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Handle Property Delete ---
  const handleDelete = async () => {
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/assets/${id}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok || response.status === 204) {
        navigate('/dashboard/properties');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Handle Add Unit ---
  const handleCreateUnit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setUnitFormError(null);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/assets/${id}/units/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: unitFormData.name,
            rent_amount: unitFormData.rent_amount ? parseFloat(unitFormData.rent_amount) : null
        })
      });

      if (response.ok) {
        setIsUnitModalOpen(false);
        setUnitFormData({ name: '', rent_amount: '' });
        fetchPropertyAndUnits(); // Refresh the data to show the new unit
      } else {
        const errData = await response.json();
        setUnitFormError(errData.detail || 'Failed to create unit.');
      }
    } catch (err) {
      setUnitFormError('Network error.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- UI Helpers ---
  const getUnitBadge = (status) => {
    switch (status) {
      case 'available': return <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold uppercase">Available</span>;
      case 'reserved': return <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-bold uppercase">Reserved</span>;
      case 'occupied': return <span className="bg-blue-100 text-quest-blue px-3 py-1 rounded-full text-xs font-bold uppercase">Occupied</span>;
      case 'maintenance': return <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs font-bold uppercase">Maintenance</span>;
      default: return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold uppercase">{status}</span>;
    }
  };

  if (isLoading) return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div></div>;
  if (error || !asset) return <div className="p-4 bg-red-50 text-red-600 rounded-xl">{error || 'Property not found'}</div>;

  return (
    <div className="space-y-6 animate-in fade-in duration-500 relative">
      
      {/* 🔙 Back Button */}
      <Link to="/dashboard/properties" className="text-sm font-semibold text-slate-500 hover:text-quest-navy transition flex items-center gap-2 w-max">
        &larr; Back to Portfolio
      </Link>

      {/* 🏢 Property Header */}
      <div className="bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="h-16 w-16 bg-blue-50 text-3xl flex items-center justify-center rounded-xl border border-blue-100">🏠</div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-2xl font-bold text-quest-navy">{asset.name}</h2>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                asset.status === 'listed' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'
              }`}>{asset.status}</span>
            </div>
            <p className="text-slate-500 flex items-center gap-1.5">
              <span>📍</span> {asset.location}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button onClick={() => setIsEditModalOpen(true)} className="flex-1 md:flex-none px-4 py-2.5 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition">Edit</button>
          <button onClick={() => setIsDeleteModalOpen(true)} className="flex-1 md:flex-none px-4 py-2.5 bg-red-50 text-red-600 font-bold rounded-xl hover:bg-red-100 transition">Delete</button>
        </div>
      </div>

      {/* 🚪 Units Management Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
          <div>
            <h3 className="text-lg font-bold text-quest-navy">Property Units</h3>
            <p className="text-sm text-slate-500">Manage individual apartments or spaces.</p>
          </div>
          <button 
            onClick={() => setIsUnitModalOpen(true)}
            className="text-sm font-bold bg-white border border-slate-200 text-quest-navy px-4 py-2.5 rounded-xl shadow-sm hover:bg-slate-50 transition flex items-center gap-2 justify-center"
          >
            <span>+</span> Add Unit
          </button>
        </div>

        {isUnitsLoading ? (
           <div className="p-10 text-center text-slate-500 animate-pulse">Loading units...</div>
        ) : units.length === 0 ? (
          <div className="p-10 text-center border-2 border-dashed border-slate-200 m-6 rounded-xl">
            <div className="text-4xl mb-3">🚪</div>
            <p className="text-slate-500 font-medium">No units have been added to this property yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500 font-semibold bg-white">
                  <th className="py-4 px-6">Unit Name</th>
                  <th className="py-4 px-6 text-right">Rent Amount (₦)</th>
                  <th className="py-4 px-6 text-center">Status</th>
                  <th className="py-4 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {units.map((unit) => (
                  <tr key={unit.id} className="hover:bg-slate-50 transition duration-150">
                    <td className="py-4 px-6 font-bold text-quest-navy">{unit.name}</td>
                    <td className="py-4 px-6 text-right text-slate-600 font-medium">
                      {unit.rent_amount ? Number(unit.rent_amount).toLocaleString() : '-'}
                    </td>
                    <td className="py-4 px-6 text-center">{getUnitBadge(unit.status)}</td>
                    <td className="py-4 px-6 text-right">
                      <button className="text-xs font-bold text-quest-blue hover:underline">Manage</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 🟢 ADD UNIT MODAL */}
      {isUnitModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden zoom-in-95">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <h3 className="font-bold text-quest-navy">Add New Unit</h3>
              <button onClick={() => setIsUnitModalOpen(false)} className="text-slate-400 font-bold">&times;</button>
            </div>
            <form onSubmit={handleCreateUnit} className="p-6 space-y-4">
              {unitFormError && <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">{unitFormError}</div>}
              <div>
                <label className="block text-sm font-semibold mb-1">Unit Name</label>
                <input 
                  type="text" required placeholder="e.g. Apt 4B"
                  value={unitFormData.name} onChange={e => setUnitFormData({...unitFormData, name: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border outline-none focus:ring-2 focus:ring-quest-blue"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Rent Amount (₦) <span className="text-slate-400 font-normal">- Optional</span></label>
                <input 
                  type="number" min="0" step="0.01" placeholder="e.g. 500000"
                  value={unitFormData.rent_amount} onChange={e => setUnitFormData({...unitFormData, rent_amount: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border outline-none focus:ring-2 focus:ring-quest-blue"
                />
              </div>
              <div className="pt-2 flex gap-3">
                <button type="button" onClick={() => setIsUnitModalOpen(false)} className="flex-1 py-3 bg-slate-100 rounded-xl font-bold text-slate-700">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="flex-1 py-3 bg-quest-navy text-white rounded-xl font-bold shadow-md disabled:opacity-50">
                  {isSubmitting ? 'Saving...' : 'Save Unit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Existing Edit Property Modal... */}
      {isEditModalOpen && (
         <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
         {/* ... (Keep your existing Edit Modal Code here) ... */}
         <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden zoom-in-95">
           <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
             <h3 className="font-bold text-quest-navy">Edit Property</h3>
             <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 font-bold">&times;</button>
           </div>
           <form onSubmit={handleUpdateSubmit} className="p-6 space-y-4">
             <div>
               <label className="block text-sm font-semibold mb-1">Name</label>
               <input type="text" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-4 py-3 rounded-xl border outline-none focus:ring-2 focus:ring-quest-blue"/>
             </div>
             <div>
               <label className="block text-sm font-semibold mb-1">Location</label>
               <input type="text" required value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} className="w-full px-4 py-3 rounded-xl border outline-none focus:ring-2 focus:ring-quest-blue"/>
             </div>
             <div className="pt-2 flex gap-3">
               <button type="button" onClick={() => setIsEditModalOpen(false)} className="flex-1 py-3 bg-slate-100 rounded-xl font-bold">Cancel</button>
               <button type="submit" disabled={isSubmitting} className="flex-1 py-3 bg-quest-navy text-white rounded-xl font-bold">{isSubmitting ? 'Saving...' : 'Save'}</button>
             </div>
           </form>
         </div>
       </div>
      )}

      {/* Existing Delete Property Modal... */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
        {/* ... (Keep your existing Delete Modal Code here) ... */}
        <div className="bg-white w-full max-w-sm rounded-2xl shadow-2xl p-6 text-center zoom-in-95">
          <div className="h-16 w-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">⚠️</div>
          <h3 className="text-lg font-bold text-quest-navy mb-2">Delete Property?</h3>
          <p className="text-slate-500 text-sm mb-6">This action cannot be undone. All data associated with this property will be permanently removed.</p>
          <div className="flex gap-3">
            <button onClick={() => setIsDeleteModalOpen(false)} className="flex-1 py-3 bg-slate-100 rounded-xl font-bold">Cancel</button>
            <button onClick={handleDelete} disabled={isSubmitting} className="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold">Delete</button>
          </div>
        </div>
      </div>
      )}

    </div>
  );
}