import { useState, useEffect, useRef } from 'react';

export default function OrgSwitcher() {
  const [organisations, setOrganisations] = useState([]);
  const [activeOrg, setActiveOrg] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const dropdownRef = useRef(null);

  // --- Fetch Organisations ---
  useEffect(() => {
    const fetchOrgs = async () => {
      const token = localStorage.getItem('access_token');
      // If user is a tenant, they might not have orgs, so we handle gracefully
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      if (user.role === 'tenant') {
        setIsLoading(false);
        return; 
      }

      try {
        const response = await fetch('http://127.0.0.1:8000/api/organisations/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const orgs = await response.json();
          setOrganisations(orgs);

          // Find the active org based on localStorage, or default to the first one
          const savedOrgId = localStorage.getItem('active_org_id');
          const current = orgs.find(o => o.id === savedOrgId) || orgs[0];
          
          if (current) {
            setActiveOrg(current);
            localStorage.setItem('active_org_id', current.id);
          }
        }
      } catch (err) {
        console.error("Failed to load organisations", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrgs();
  }, []);

  // --- Handle Click Outside to Close ---
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // --- Handle Org Switch ---
  const handleSwitch = (org) => {
    if (org.id === activeOrg.id) {
      setIsOpen(false);
      return;
    }
    
    // Update local storage
    localStorage.setItem('active_org_id', org.id);
    setActiveOrg(org);
    setIsOpen(false);
    
    // Force a hard reload so all dashboard components refetch data for the new org
    window.location.href = '/dashboard'; 
  };

  // Don't render for tenants or if no orgs are loaded yet
  if (isLoading || organisations.length === 0) return null;

  return (
    <div className="relative mb-6" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between p-3 rounded-xl border transition-all duration-200 ${
          isOpen ? 'bg-slate-50 border-quest-blue shadow-sm' : 'bg-white border-slate-200 hover:bg-slate-50'
        }`}
      >
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="h-8 w-8 bg-blue-100 text-quest-blue rounded-lg flex items-center justify-center flex-shrink-0 text-sm">
            🏢
          </div>
          <div className="text-left truncate">
            <p className="text-sm font-bold text-quest-navy truncate">{activeOrg?.name}</p>
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              {activeOrg?.my_role || 'Member'}
            </p>
          </div>
        </div>
        
        {/* Only show dropdown arrow if they have more than 1 org */}
        {organisations.length > 1 && (
          <span className="text-slate-400 text-xs ml-2">▼</span>
        )}
      </button>

      {/* The Dropdown Menu */}
      {isOpen && organisations.length > 1 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-100 rounded-xl shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="p-2 text-xs font-bold text-slate-400 uppercase tracking-wider bg-slate-50">
            Switch Portfolio
          </div>
          <div className="max-h-48 overflow-y-auto">
            {organisations.map((org) => (
              <button
                key={org.id}
                onClick={() => handleSwitch(org)}
                className={`w-full text-left px-4 py-3 text-sm flex items-center justify-between transition-colors ${
                  org.id === activeOrg.id ? 'bg-blue-50 text-quest-blue font-bold' : 'text-slate-700 hover:bg-slate-50 font-medium'
                }`}
              >
                <span className="truncate pr-4">{org.name}</span>
                {org.id === activeOrg.id && <span>✓</span>}
              </button>
            ))}
          </div>
          {/* Optional: Future button to create a new org */}
          <div className="border-t border-slate-100 p-2">
            <button className="w-full text-left px-2 py-2 text-xs font-bold text-slate-500 hover:text-quest-navy transition flex items-center gap-2">
              <span>+</span> Create new portfolio
            </button>
          </div>
        </div>
      )}
    </div>
  );
}