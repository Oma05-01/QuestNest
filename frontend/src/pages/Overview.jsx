import { useEffect, useState } from 'react';
import TenantDashboard from './TenantDashboard';
import LandlordDashboard from './LandlordDashboard';
import AdminDashboard from './AdminDashboard';
import OrganisationSetup from '../components/OrganisationSetup';

export default function Overview() {
  const [userRole, setUserRole] = useState(null);
  
  // New States for Organisation Flow
  const [hasCheckedOrgs, setHasCheckedOrgs] = useState(false);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  useEffect(() => {
    const userString = localStorage.getItem('user');
    if (userString) {
      try {
        const user = JSON.parse(userString);
        setUserRole(user.role);

        // 🟢 2. If they are a Landlord, check their organisations before letting them through
        if (user.role === 'landlord' || user.role === 'agent') {
          checkOrganisations();
        } else {
          // Tenants and Admins don't need this check
          setHasCheckedOrgs(true); 
        }
      } catch (e) {
        console.error("Failed to parse user data");
      }
    }
  }, []);

  const checkOrganisations = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/organisations/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const orgs = await response.json();
        
        if (orgs.length === 0) {
          // They have no companies! Intercept them.
          setNeedsOnboarding(true);
        } else {
          // They have a company. Make sure the active one is set in localStorage.
          if (!localStorage.getItem('active_org_id')) {
            localStorage.setItem('active_org_id', orgs[0].id);
          }
        }
      }
    } catch (error) {
      console.error("Failed to check orgs", error);
    } finally {
      setHasCheckedOrgs(true);
    }
  };

  // --- Render Logic ---

  if (!userRole || !hasCheckedOrgs) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue"></div>
      </div>
    );
  }

  // 🟢 3. Show the Setup Modal if they have no organisations
  if (needsOnboarding) {
    return (
      <OrganisationSetup 
        onComplete={(newOrg) => {
          setNeedsOnboarding(false); // Once done, clear the flag to reveal the dashboard!
        }} 
      />
    );
  }

  // Otherwise, proceed to their normal dashboards
  if (userRole === 'tenant') return <TenantDashboard />;
  if (userRole === 'landlord') return <LandlordDashboard />;
  if (userRole === 'admin') return <AdminDashboard />;

  return null;
}