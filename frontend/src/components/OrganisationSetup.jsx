import { useState } from 'react';

export default function OrganisationSetup({ onComplete }) {
  const [name, setName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/organisations/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name })
      });

      if (response.ok) {
        const data = await response.json();
        // Save the newly created Org ID as their active context
        localStorage.setItem('active_org_id', data.id);
        
        // Tell the parent component (Overview) that we are done!
        onComplete(data);
      } else {
        const errData = await response.json();
        setError(errData.detail || errData.name?.[0] || 'Failed to create organisation.');
      }
    } catch (err) {
      setError('Network error. Please check your connection.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center animate-in fade-in zoom-in-95 duration-500">
      <div className="bg-white max-w-md w-full p-8 rounded-3xl shadow-xl border border-slate-100 text-center">
        
        <div className="h-20 w-20 bg-blue-50 rounded-full flex items-center justify-center text-4xl mx-auto mb-6 border border-blue-100 shadow-inner">
          🏢
        </div>
        
        <h2 className="text-2xl font-bold text-quest-navy mb-2">Create your Portfolio</h2>
        <p className="text-slate-500 text-sm mb-8">
          To get started, give your real estate company or property portfolio a name. You can invite team members to this later.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6 text-left">
          {error && (
             <div className="p-3 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100 text-center">
               {error}
             </div>
          )}
          
          <div>
            <label className="block text-sm font-semibold text-quest-navy mb-1.5">
              Organisation Name
            </label>
            <input 
              type="text" 
              required
              placeholder="e.g. Matrix Properties Ltd."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none transition text-slate-700 font-medium shadow-sm"
            />
          </div>

          <button 
            type="submit" 
            disabled={isSubmitting || !name.trim()}
            className="w-full py-4 bg-quest-navy text-white rounded-xl font-bold hover:bg-quest-navy/90 transition shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Setting up...' : 'Continue to Dashboard'}
          </button>
        </form>

      </div>
    </div>
  );
}