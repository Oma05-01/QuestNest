import { useState, useEffect } from 'react';

export default function NewMaintenanceRequest({ isOpen, onClose, onSuccess }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [images, setImages] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // We need to know which unit/org the tenant belongs to
  const [activeLease, setActiveLease] = useState(null);

  useEffect(() => {
    if (isOpen) {
      // Fetch the tenant's active lease to automatically get the unit_id and org_id
      const fetchLease = async () => {
        const token = localStorage.getItem('access_token');
        const res = await fetch('http://127.0.0.1:8000/api/leases/', { // Adjust to your actual leases endpoint
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        // Assuming the tenant has at least one active lease
        if (data.length > 0) {
            setActiveLease(data[0]); 
        }
      };
      fetchLease();
    }
  }, [isOpen]);

  const handleImageChange = (e) => {
    // Convert FileList to Array and add to state
    const files = Array.from(e.target.files);
    setImages(prev => [...prev, ...files]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!activeLease) return alert("No active lease found to attach this request to.");
    
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    // 🟢 Critical: Because we are sending files, we MUST use FormData, not JSON.stringify
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('priority', priority);
    
    // Send the routing data your Django view expects
    formData.append('unit', activeLease.tenancy.unit.id); // Adjust based on your lease serializer
    formData.append('unit_org', activeLease.tenancy.unit.asset.organisation); // Adjust based on your lease serializer

    // Append multiple files
    images.forEach(image => {
      formData.append('images', image);
    });

    try {
      const res = await fetch('http://127.0.0.1:8000/api/maintenance/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // DO NOT set 'Content-Type': 'multipart/form-data'. 
          // Browser sets it automatically with the correct boundary when using FormData!
        },
        body: formData
      });

      if (res.ok) {
        onSuccess(); // Refresh the list
        onClose(); // Close modal
        
        // Reset form
        setTitle('');
        setDescription('');
        setPriority('medium');
        setImages([]);
      } else {
        const errData = await res.json();
        console.error(errData);
        alert("Failed to submit request.");
      }
    } catch (err) {
      alert("Network error.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
      <div className="bg-white max-w-lg w-full p-8 rounded-3xl shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black text-quest-navy">Report an Issue</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1.5">Issue Title</label>
            <input 
              type="text" required placeholder="e.g., Leaking pipe under sink"
              value={title} onChange={e => setTitle(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-quest-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1.5">Description</label>
            <textarea 
              required placeholder="Please describe the issue in detail..." rows="4"
              value={description} onChange={e => setDescription(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-quest-blue resize-none"
            ></textarea>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Priority</label>
              <select 
                value={priority} onChange={e => setPriority(e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-quest-blue"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Upload Photos</label>
              <div className="relative w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl hover:bg-slate-100 transition cursor-pointer text-center text-sm text-slate-500 font-bold overflow-hidden">
                <span>{images.length > 0 ? `${images.length} file(s) selected` : 'Choose Files...'}</span>
                <input 
                  type="file" multiple accept="image/*"
                  onChange={handleImageChange}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
              </div>
            </div>
          </div>

          <button 
            type="submit" disabled={isSubmitting}
            className="w-full bg-quest-navy text-white font-bold py-4 rounded-xl hover:bg-opacity-90 disabled:opacity-50 mt-4 transition shadow-lg"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Request'}
          </button>
        </form>
      </div>
    </div>
  );
}