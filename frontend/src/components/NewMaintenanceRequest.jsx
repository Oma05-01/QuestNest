import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

export default function NewMaintenanceRequest({ isOpen, onClose, onSuccess }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [images, setImages] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeLease, setActiveLease] = useState(null);

  useEffect(() => {
    if (isOpen) {
      const fetchLease = async () => {
        try {
          const res = await apiFetch('/api/leases/');
          if (res.ok) {
            const data = await res.json();
            const leases = Array.isArray(data) ? data : data.results || [];
            if (leases.length > 0) {
              setActiveLease(leases[0]);
            }
          }
        } catch (err) {
          console.error("Failed to fetch lease details:", err);
        }
      };
      fetchLease();
    }
  }, [isOpen]);

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    setImages((prev) => [...prev, ...files]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const unitId = activeLease?.unit?.id || activeLease?.tenancy?.unit?.id || activeLease?.unit;
    if (!unitId) {
      alert("No active lease or unit found to attach this request to.");
      return;
    }

    setIsSubmitting(true);

    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('priority', priority);
    formData.append('unit', unitId);

    images.forEach((image) => {
      formData.append('images', image);
    });

    try {
      const res = await apiFetch('/api/maintenance/', {
        method: 'POST',
        body: formData, // apiFetch handles omitting Content-Type for FormData
      });

      if (res.ok) {
        onSuccess();
        onClose();
        setTitle('');
        setDescription('');
        setPriority('medium');
        setImages([]);
      } else {
        const errData = await res.json();
        console.error("Maintenance submit error:", errData);
        alert("Failed to submit maintenance request.");
      }
    } catch (err) {
      console.error(err);
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
              type="text"
              required
              placeholder="e.g., Leaking pipe under sink"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-quest-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1.5">Description</label>
            <textarea
              required
              placeholder="Please describe the issue in detail..."
              rows="4"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-quest-blue resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
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
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleImageChange}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-quest-navy text-white font-bold py-4 rounded-xl hover:bg-opacity-90 disabled:opacity-50 mt-4 transition shadow-lg"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Request'}
          </button>
        </form>
      </div>
    </div>
  );
}