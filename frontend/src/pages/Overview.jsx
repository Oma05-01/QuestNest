import { useEffect, useState } from 'react';
import TenantDashboard from './TenantDashboard';
import LandlordDashboard from './LandlordDashboard';
import AdminDashboard from './AdminDashboard';
import OrganisationSetup from '../components/OrganisationSetup';
import { apiFetch } from '../api/client';

export default function Overview() {
  const [user, setUser] = useState(null);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  const fetchWorkspaces = async () => {
    try {
      const response = await apiFetch('/api/workspaces/');
      if (response.ok) {
        const data = await response.json();
        const workspaces = Array.isArray(data) ? data : data.results || [];

        const activeOrgId = localStorage.getItem('active_org_id');
        let current = workspaces.find((w) => w.id === activeOrgId);

        if (!current && workspaces.length > 0) {
          current = workspaces.find((w) => w.workspace_type === 'personal') || workspaces[0];
          if (current) localStorage.setItem('active_org_id', current.id);
        }

        setActiveWorkspace(current || null);
      }
    } catch (error) {
      console.error('Failed to load workspace context:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const userString = localStorage.getItem('user');
    if (userString) {
      try {
        setUser(JSON.parse(userString));
      } catch (e) {
        console.error('Error parsing stored user data:', e);
      }
    }

    fetchWorkspaces();

    const handleWorkspaceChange = () => {
      fetchWorkspaces();
    };

    window.addEventListener('workspaceChanged', handleWorkspaceChange);
    return () => window.removeEventListener('workspaceChanged', handleWorkspaceChange);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <div className="h-10 w-10 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider animate-pulse">
          Loading Workspace Context...
        </p>
      </div>
    );
  }

  if (needsOnboarding) {
    return (
      <OrganisationSetup
        onComplete={(newOrg) => {
          if (newOrg?.id) localStorage.setItem('active_org_id', newOrg.id);
          setNeedsOnboarding(false);
          fetchWorkspaces();
        }}
      />
    );
  }

  // 1. Business Workspace Context -> Landlord Dashboard
  if (activeWorkspace?.workspace_type === 'business') {
    return <LandlordDashboard workspace={activeWorkspace} />;
  }

  // 2. Personal Workspace Context -> Resident / Tenant Dashboard
  if (activeWorkspace?.workspace_type === 'personal') {
    return <TenantDashboard workspace={activeWorkspace} />;
  }

  // 3. Fallback for System Staff without workspace context
  if (user?.is_staff || user?.is_superuser) {
    return <AdminDashboard />;
  }

  return <TenantDashboard workspace={activeWorkspace} />;
}