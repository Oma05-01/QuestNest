import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import NotificationBell from './NotificationBell';
import OrgSwitcher from './OrgSwitcher';
import { apiFetch } from '../api/client';

// --- Inline Clean Vector Icons ---
const Icons = {
  Overview: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
  Properties: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
  Leases: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
  Wallet: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>,
  Maintenance: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 100-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>,
  Messages: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>,
  Settings: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  ChevronLeft: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>,
  ChevronRight: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>,
  Menu: () => <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>,
  Close: () => <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>,
  LogOut: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>,
};

// Route title helper
const getPageTitle = (pathname) => {
  if (pathname === '/dashboard') return 'Overview';
  if (pathname.startsWith('/dashboard/properties/')) return 'Property Details';
  if (pathname === '/dashboard/properties') return 'My Properties';
  if (pathname.startsWith('/dashboard/leases/')) return 'Lease Document';
  if (pathname === '/dashboard/leases') return 'Leases';
  if (pathname === '/dashboard/wallet') return 'Escrow Wallet';
  if (pathname === '/dashboard/maintenance') return 'Maintenance Requests';
  if (pathname === '/dashboard/messages') return 'Messages';
  if (pathname === '/dashboard/settings') return 'Settings & Security';
  return 'Dashboard';
};

export default function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [activeWorkspace, setActiveWorkspace] = useState(null);

  const loadContext = async () => {
    // 1. Load User data
    const userString = localStorage.getItem('user');
    if (userString) {
      try {
        setUser(JSON.parse(userString));
      } catch (e) {
        console.error("Failed to parse user data", e);
      }
    }

    // 2. Load Active Workspace Context
    try {
      const response = await apiFetch('/api/workspaces/');
      if (response.ok) {
        const data = await response.json();
        const list = Array.isArray(data) ? data : data.results || [];
        const savedOrgId = localStorage.getItem('active_org_id');
        const current = list.find((w) => w.id === savedOrgId) || list[0];
        if (current) {
          setActiveWorkspace(current);
        }
      }
    } catch (err) {
      console.error("Failed to fetch workspaces in layout:", err);
    }
  };

  useEffect(() => {
    loadContext();

    // Listen for workspace switch events from OrgSwitcher
    const handleWorkspaceChange = () => {
      loadContext();
    };

    window.addEventListener('workspaceChanged', handleWorkspaceChange);
    return () => window.removeEventListener('workspaceChanged', handleWorkspaceChange);
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setIsMobileOpen(false);
  }, [location.pathname]);

  const getInitials = (name) => {
    if (!name) return 'QN';
    return name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_org_id');
    navigate('/login');
  };

  // 🟢 Dynamic Navigation based on Active Workspace Type
  const isBusinessContext = activeWorkspace?.workspace_type === 'business' || user?.is_staff || user?.is_superuser;

  const navLinks = [
    { name: 'Overview', path: '/dashboard', icon: Icons.Overview },
    ...(isBusinessContext
      ? [{ name: 'My Properties', path: '/dashboard/properties', icon: Icons.Properties }]
      : []),
    { name: 'Leases', path: '/dashboard/leases', icon: Icons.Leases },
    { name: 'Escrow Wallet', path: '/dashboard/wallet', icon: Icons.Wallet },
    { name: 'Maintenance', path: '/dashboard/maintenance', icon: Icons.Maintenance },
    { name: 'Messages', path: '/dashboard/messages', icon: Icons.Messages },
    { name: 'Settings', path: '/dashboard/settings', icon: Icons.Settings },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900 font-sans antialiased">

      {/* =========================================
          1. MOBILE SIDEBAR OVERLAY DRAWER
          ========================================= */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-200"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* =========================================
          2. THE SIDEBAR (Desktop & Mobile)
          ========================================= */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col bg-slate-900 text-white border-r border-slate-800 shadow-xl transition-all duration-300 ease-in-out ${
          isCollapsed ? 'md:w-20' : 'md:w-64'
        } ${isMobileOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0'}`}
      >
        {/* Brand/Logo Area */}
        <div className="h-20 flex items-center justify-between px-5 border-b border-slate-800 bg-slate-950/50">
          <Link to="/dashboard" className="flex items-center gap-3 overflow-hidden">
            <div className="h-10 w-10 bg-gradient-to-tr from-blue-600 to-indigo-500 text-white rounded-xl flex items-center justify-center font-black shrink-0 shadow-lg shadow-blue-500/20">
              QN
            </div>
            {(!isCollapsed || isMobileOpen) && (
              <span className="font-extrabold text-lg tracking-tight text-white truncate">
                Quest<span className="text-blue-400">Nest</span>
              </span>
            )}
          </Link>

          {/* Desktop Collapse Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:flex p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? <Icons.ChevronRight /> : <Icons.ChevronLeft />}
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <Icons.Close />
          </button>
        </div>

        {/* Scrollable Navigation Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 custom-scrollbar">

          {/* Workspace Switcher */}
          {(!isCollapsed || isMobileOpen) ? (
            <OrgSwitcher />
          ) : (
            <div className="flex justify-center mb-4">
              <div
                className="h-10 w-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300 cursor-pointer hover:border-blue-500 transition"
                title="Active Workspace"
              >
                {activeWorkspace?.workspace_type === 'personal' ? '👤' : '🏢'}
              </div>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path || (link.path !== '/dashboard' && location.pathname.startsWith(link.path));
              const Icon = link.icon;

              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`group relative flex items-center gap-3.5 px-3.5 py-3 rounded-xl font-medium text-sm transition-all duration-150 ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/80'
                  } ${isCollapsed && !isMobileOpen ? 'justify-center px-0' : ''}`}
                >
                  <Icon />

                  {(!isCollapsed || isMobileOpen) && (
                    <span className="truncate">{link.name}</span>
                  )}

                  {/* Tooltip for Desktop Collapsed State */}
                  {isCollapsed && !isMobileOpen && (
                    <div className="absolute left-full ml-3 px-3 py-1.5 bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50 border border-slate-800">
                      {link.name}
                    </div>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom User Quick Profile */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/30">
          <div className={`flex items-center justify-between gap-3 ${isCollapsed && !isMobileOpen ? 'justify-center' : ''}`}>
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold flex items-center justify-center shrink-0">
                {getInitials(user?.name)}
              </div>

              {(!isCollapsed || isMobileOpen) && (
                <div className="overflow-hidden text-left">
                  <p className="text-sm font-semibold text-white truncate">{user?.name || 'User'}</p>
                  <p className="text-xs text-slate-400 capitalize truncate">
                    {user?.is_staff
                      ? 'System Admin'
                      : activeWorkspace?.workspace_type === 'business'
                      ? (activeWorkspace?.my_role || 'Portfolio Manager')
                      : 'Resident'}
                  </p>
                </div>
              )}
            </div>

            {(!isCollapsed || isMobileOpen) && (
              <button
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition"
                title="Log out"
              >
                <Icons.LogOut />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* =========================================
          3. MAIN CONTENT WRAPPER
          ========================================= */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ease-in-out ${
          isCollapsed ? 'md:ml-20' : 'md:ml-64'
        }`}
      >
        {/* Sticky Header Top Bar */}
        <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-200/80 flex items-center justify-between px-6 sm:px-8 sticky top-0 z-30 shadow-xs">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsMobileOpen(true)}
              className="md:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100 transition"
            >
              <Icons.Menu />
            </button>

            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                {getPageTitle(location.pathname)}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <NotificationBell />
          </div>
        </header>

        {/* Dynamic Outlet Page Container */}
        <main className="flex-1 p-6 sm:p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>

    </div>
  );
}