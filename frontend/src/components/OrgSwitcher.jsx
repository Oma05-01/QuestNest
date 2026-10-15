import { useState, useEffect, useRef } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function OrgSwitcher() {
  const [organisations, setOrganisations] = useState([]);
  const [activeOrg, setActiveOrg] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const dropdownRef = useRef(null);

  useEffect(() => {
    const fetchOrgs = async () => {
      const token = localStorage.getItem('access_token');
      const user = JSON.parse(localStorage.getItem('user') || '{}');

      if (user.role === 'tenant') {
        setIsLoading(false);
        return;
      }

      if (!token) {
        setError('Not authenticated');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.status === 401) {
          setError('Session expired');
          return;
        }

        if (response.ok) {
          const orgs = await response.json();
          setOrganisations(orgs);

          const savedOrgId = localStorage.getItem('active_org_id');
          const current = orgs.find((o) => o.id === savedOrgId) || orgs[0];

          if (current) {
            setActiveOrg(current);
            localStorage.setItem('active_org_id', current.id);
          }
        } else {
          setError(`Error ${response.status}`);
        }
      } catch (err) {
        console.error('Failed to load organisations:', err);
        setError('Server unreachable');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrgs();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSwitch = (org) => {
    if (org.id === activeOrg?.id) {
      setIsOpen(false);
      return;
    }

    localStorage.setItem('active_org_id', org.id);
    setActiveOrg(org);
    setIsOpen(false);
    window.location.href = '/dashboard';
  };

  if (isLoading) return <div className="p-3 text-xs text-slate-400">Loading workspaces...</div>;
  if (error) return <div className="p-3 text-xs text-red-500">Workspace error: {error}</div>;
  if (organisations.length === 0) return null;

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

        {organisations.length > 1 && <span className="text-slate-400 text-xs ml-2">▼</span>}
      </button>

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
                  org.id === activeOrg?.id ? 'bg-blue-50 text-quest-blue font-bold' : 'text-slate-700 hover:bg-slate-50 font-medium'
                }`}
              >
                <span className="truncate pr-4">{org.name}</span>
                {org.id === activeOrg?.id && <span>✓</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}