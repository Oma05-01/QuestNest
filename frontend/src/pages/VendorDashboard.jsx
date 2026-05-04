import { useState, useEffect } from 'react';

export default function VendorDashboard() {
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    fetch('http://127.0.0.1:8000/api/maintenance/my-tasks/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      setTasks(data);
      setIsLoading(false);
    });
  }, []);

  const handleMarkComplete = async (taskId) => {
    // Logic to update status to RESOLVED
    alert("Task marked as completed!");
  };

  if (isLoading) return <div className="p-10 text-center">Loading Tasks...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black text-quest-navy italic">WORK ORDERS</h1>
          <p className="text-slate-500">Your assigned maintenance tasks</p>
        </div>
        <div className="bg-quest-blue px-4 py-2 rounded-lg text-quest-navy font-bold text-sm">
          {tasks.length} Active Jobs
        </div>
      </header>

      <div className="grid gap-6">
        {tasks.length === 0 ? (
          <div className="bg-slate-50 rounded-2xl p-20 text-center text-slate-400">
            No active work orders. Kick back and relax! ☕
          </div>
        ) : (
          tasks.map(task => (
            <div key={task.id} className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm hover:shadow-md transition">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Job #{task.id.slice(0, 5)}</span>
                  <h3 className="text-xl font-bold text-quest-navy">{task.request_title}</h3>
                  <p className="text-slate-500 text-sm mt-1">{task.unit_name} • {task.property_name}</p>
                </div>
                <button 
                  onClick={() => handleMarkComplete(task.id)}
                  className="bg-green-100 text-green-700 px-6 py-2 rounded-xl font-bold text-sm hover:bg-green-600 hover:text-white transition"
                >
                  Mark Finished
                </button>
              </div>

              <div className="bg-slate-50 p-4 rounded-2xl">
                 <p className="text-xs text-slate-600 italic">" {task.notes || 'No special instructions provided.'} "</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}