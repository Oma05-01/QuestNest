import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LandlordTenancies from '../components/LandlordTenancies'; // 🟢 1. Import it here

export default function LandlordDashboard() {
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
        const response = await fetch('http://127.0.0.1:8000/api/dashboard/landlord/', {
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
        setError('Failed to load dashboard data. Please try again.');
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
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-2xl font-bold text-quest-navy">Portfolio Overview</h2>
        <p className="text-slate-500">Monitor your property performance and escrow balances.</p>
      </div>

      {/* 📊 Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        
        {/* Total Revenue Card */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col hover:shadow-md transition">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Total Revenue</span>
            <span className="h-8 w-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center">📈</span>
          </div>
          <span className="text-3xl font-bold text-quest-navy">
            ₦{Number(stats?.total_revenue || 0).toLocaleString()}
          </span>
        </div>

        {/* Escrow Balance Card (QuestNest's Core Feature) */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col hover:shadow-md transition border-l-4 border-l-quest-blue">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Escrow Balance</span>
            <span className="h-8 w-8 bg-blue-100 text-quest-blue rounded-full flex items-center justify-center">🛡️</span>
          </div>
          <span className="text-3xl font-bold text-quest-blue">
            ₦{Number(stats?.escrow_balance || 0).toLocaleString()}
          </span>
        </div>

        {/* Active Tenants Card */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col hover:shadow-md transition">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Active Tenants</span>
            <span className="h-8 w-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center">🔑</span>
          </div>
          <span className="text-3xl font-bold text-quest-navy">
            {stats?.active_tenants || 0}
          </span>
        </div>
      </div>

      {/* 🏠 Placeholder for Landlord Tenancies Table */}
      <div className="mt-10 bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-quest-navy">Active Tenancies</h3>
          <button className="text-sm font-semibold text-quest-blue hover:text-quest-navy transition">
            Manage Properties
          </button>
        </div>
        <LandlordTenancies />
      </div>
    </div>
  );
}