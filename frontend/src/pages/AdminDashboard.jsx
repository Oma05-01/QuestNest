import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SystemActivity from '../components/SystemActivity'; // We will build this next!

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        navigate('/login');
        return;
      }

      try {
        const response = await fetch('http://127.0.0.1:8000/api/dashboard/admin/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.status === 401) {
          localStorage.removeItem('access_token');
          navigate('/login');
          return;
        }

        if (!response.ok) throw new Error('Failed to load data');

        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError('Failed to load system stats.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [navigate]);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div>
      </div>
    );
  }

  if (error) {
    return <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl">{error}</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-2xl font-bold text-quest-navy">System Administration</h2>
        <p className="text-slate-500">Monitor platform health and global activity logs.</p>
      </div>

      {/* 📊 Global Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        
        {/* Total Users Card */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col hover:shadow-md transition">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Total Users</span>
            <span className="h-8 w-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center">👥</span>
          </div>
          <span className="text-3xl font-bold text-quest-navy">
            {Number(stats?.total_users || 0).toLocaleString()}
          </span>
        </div>

        {/* Active Escrows Card */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col hover:shadow-md transition">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Active Escrows</span>
            <span className="h-8 w-8 bg-blue-100 text-quest-blue rounded-full flex items-center justify-center">🛡️</span>
          </div>
          <span className="text-3xl font-bold text-quest-navy">
            {Number(stats?.active_escrows || 0).toLocaleString()}
          </span>
        </div>

        {/* System Health Card */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col hover:shadow-md transition border-l-4 border-l-green-500">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 text-sm font-semibold uppercase tracking-wider">System Health</span>
            <span className="h-8 w-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center">⚡</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-2xl font-bold text-quest-navy uppercase">
              {stats?.system_health || 'OPERATIONAL'}
            </span>
          </div>
        </div>
      </div>

      {/* 📡 System Activity Table Injector */}
      <div className="mt-10 bg-white rounded-2xl shadow-sm border border-slate-100">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-lg font-bold text-quest-navy">Live System Activity</h3>
          <button className="text-sm font-semibold flex items-center gap-2 text-slate-500 hover:text-quest-navy transition">
            <span>🔄</span> Refresh Log
          </button>
        </div>
        <div className="p-2">
          <SystemActivity />
        </div>
      </div>
    </div>
  );
}