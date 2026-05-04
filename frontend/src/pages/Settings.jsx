import { useState, useEffect } from 'react';

export default function Settings() {
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });

  // Load the user data from localStorage when the component mounts
  useEffect(() => {
    const userString = localStorage.getItem('user');
    if (userString) {
      try {
        const user = JSON.parse(userString);
        setFormData({
          name: user.name || '',
          email: user.email || ''
        });
      } catch (e) {
        console.error("Failed to parse user data");
      }
    }
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setStatus({ type: '', message: '' }); // Clear messages when typing
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setStatus({ type: '', message: '' });

    const token = localStorage.getItem('access_token');

    try {
      // Send the PATCH request to your Django UserUpdateView
      const response = await fetch('http://127.0.0.1:8000/api/auth/profile/', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        // Success! Update localStorage so the sidebar reflects the new name
        localStorage.setItem('user', JSON.stringify(data));
        
        setStatus({ 
          type: 'success', 
          message: 'Profile updated successfully.' 
        });
      } else {
        // Handle validation errors from Django (e.g., email already exists)
        setStatus({ 
          type: 'error', 
          message: data.detail || data.email?.[0] || 'Failed to update profile.' 
        });
      }
    } catch (error) {
      setStatus({ 
        type: 'error', 
        message: 'Network error. Please check your connection.' 
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-2xl font-bold text-quest-navy">Account Settings</h2>
        <p className="text-slate-500">Update your personal information and preferences.</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-lg font-bold text-quest-navy">Profile Information</h3>
          <p className="text-sm text-slate-500">This information will be displayed on your dashboard and communications.</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          
          {/* Status Message Banner */}
          {status.message && (
            <div className={`p-4 rounded-xl border text-sm font-medium ${
              status.type === 'success' 
                ? 'bg-green-50 border-green-200 text-green-700' 
                : 'bg-red-50 border-red-200 text-red-600'
            }`}>
              {status.type === 'success' ? '✅ ' : '❌ '} {status.message}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-quest-navy mb-1.5">
                Full Name
              </label>
              <input 
                type="text" 
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none transition duration-150"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-quest-navy mb-1.5">
                Email Address
              </label>
              <input 
                type="email" 
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none transition duration-150"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button 
              type="submit"
              disabled={isSaving}
              className="bg-quest-navy text-white font-bold py-3 px-8 rounded-xl hover:bg-quest-navy/90 transition duration-150 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>

      {/* Placeholder for future security settings */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden opacity-60">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-lg font-bold text-quest-navy">Security (Coming Soon)</h3>
          <p className="text-sm text-slate-500">Update your password and 2FA settings.</p>
        </div>
        <div className="p-6">
           <p className="text-sm text-slate-400 font-medium">Security settings are managed externally or locked during this phase.</p>
        </div>
      </div>

    </div>
  );
}