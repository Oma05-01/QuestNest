import { useState, useEffect } from 'react';
import NewMaintenanceRequest from '../components/NewMaintenanceRequest';

export default function Maintenance() {
  const [issues, setIssues] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch the tenant's maintenance history
  const fetchIssues = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/maintenance/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setIssues(data);
      }
    } catch (err) {
      console.error("Failed to fetch maintenance requests.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { 
    fetchIssues(); 
  }, []);

  return (
    <div className="space-y-6 pb-20 animate-in fade-in duration-500">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-quest-navy">Maintenance</h2>
          <p className="text-slate-500 text-sm">Report issues and track repair progress.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-quest-blue text-quest-navy font-black px-6 py-3 rounded-xl shadow-sm hover:shadow-md transition flex items-center gap-2"
        >
          <span>🔧</span> Report New Issue
        </button>
      </div>

      {/* Issues List */}
      {isLoading ? (
        <div className="text-center p-10 text-slate-400">Loading requests...</div>
      ) : issues.length === 0 ? (
        <div className="bg-white p-12 rounded-3xl border border-slate-100 text-center shadow-sm">
          <div className="text-4xl mb-4">🏠</div>
          <h3 className="text-lg font-bold text-quest-navy mb-2">Everything looks good!</h3>
          <p className="text-slate-500 text-sm">You haven't reported any maintenance issues yet.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {issues.map(issue => (
            <div 
              key={issue.id} 
              className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-quest-blue/30 transition"
            >
              <div className="flex items-start gap-4">
                <div className={`mt-1 h-3 w-3 rounded-full shrink-0 ${
                  issue.priority === 'urgent' ? 'bg-red-500' : 
                  issue.priority === 'high' ? 'bg-orange-500' : 'bg-green-500'
                }`} />
                <div>
                  <h4 className="font-bold text-quest-navy">{issue.title}</h4>
                  <p className="text-sm text-slate-500 mt-1 line-clamp-1">{issue.description}</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase mt-2 tracking-wider">
                    {new Date(issue.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-4 self-end md:self-auto">
                <span className={`text-[10px] font-black uppercase px-4 py-1.5 rounded-full ${
                  issue.status === 'open' ? 'bg-slate-100 text-slate-600' : 
                  issue.status === 'in_progress' ? 'bg-orange-100 text-orange-600' : 
                  'bg-green-100 text-green-600'
                }`}>
                  {issue.status_display || issue.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 🟢 The Modal Component */}
      <NewMaintenanceRequest 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchIssues} 
      />
      
    </div>
  );
}