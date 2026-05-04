import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import NotificationBell from './NotificationBell';
import OrgSwitcher from './OrgSwitcher';

export default function DashboardLayout() {
  const location = useLocation(); 
  
  // 🟢 1. State for Sidebar Toggle
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  // 🟢 2. State for Dynamic User Details
  const [user, setUser] = useState({ name: 'User', role: 'tenant' });

  useEffect(() => {
    const userString = localStorage.getItem('user');
    if (userString) {
      setUser(JSON.parse(userString));
    }
  }, []);

  // Helper to get initials
  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const getNavLinks = (role) => {
    // These are the links EVERYONE shares
    const baseLinks = [
      { name: 'Overview', path: '/dashboard', icon: '📊' },
      { name: 'Leases', path: '/dashboard/leases', icon: '📄' },
      { name: 'Escrow Wallet', path: '/dashboard/wallet', icon: '💳' },
      { name: 'Maintenance', path: '/dashboard/maintenance', icon: '🔧' }, // 👈 Added Maintenance!
      { name: 'Messages', path: '/dashboard/messages', icon: '💬' },
      { name: 'Settings', path: '/dashboard/settings', icon: '⚙️' },
    ];

    // If they are a landlord, slide "My Properties" into the 2nd slot
    if (role === 'landlord' || role === 'agent') {
      baseLinks.splice(1, 0, { name: 'My Properties', path: '/dashboard/properties', icon: '🏢' });
    }

    return baseLinks;
  };

  const navLinks = getNavLinks(user.role);

  return (
    <div className="min-h-screen flex bg-quest-slate">
      
      {/* =========================================
          1. THE SIDEBAR (Collapsible)
          ========================================= */}
      <aside 
        className={`${
          isCollapsed ? 'w-20' : 'w-64'
        } bg-quest-navy text-white flex flex-col hidden md:flex fixed h-full shadow-2xl z-20 transition-all duration-300 ease-in-out`}
      >
        {/* Brand/Logo Area & Toggle */}
        <div className="h-20 flex items-center justify-between border-b border-white/10 px-4 bg-white">
          {!isCollapsed ? (
            <img src="/logo-full.png" alt="QuestNest" className="h-10 w-auto ml-2" />
          ) : (
             <div className="h-10 w-10 bg-quest-blue text-quest-navy rounded-lg flex items-center justify-center font-black mx-auto">
               QN
             </div>
          )}
          {/* Toggle Button */}
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-slate-400 hover:text-quest-navy transition p-1"
          >
            {isCollapsed ? '▶' : '◀'}
          </button>
        </div>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 custom-scrollbar">
          
          {/* THE ORG SWITCHER - Hide if collapsed */}
          {!isCollapsed && <OrgSwitcher />}

          {/* Navigation Links */}
          <nav className={`space-y-1 ${!isCollapsed ? 'mt-4' : 'mt-0'}`}>
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  title={isCollapsed ? link.name : ''} // Tooltip for collapsed mode
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium ${
                    isActive 
                      ? 'bg-quest-blue text-quest-navy shadow-md' 
                      : 'text-slate-300 hover:bg-white/10 hover:text-white'
                  } ${isCollapsed ? 'justify-center' : ''}`}
                >
                  <span className="text-xl">{link.icon}</span>
                  {!isCollapsed && <span>{link.name}</span>}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Quick Profile */}
        <div className="p-4 border-t border-white/10">
          <div className={`flex items-center gap-3 px-2 py-2 hover:bg-white/5 rounded-xl cursor-pointer transition ${isCollapsed ? 'justify-center' : ''}`}>
            <div className="h-10 w-10 rounded-full bg-quest-blue/20 flex items-center justify-center text-quest-blue font-bold border border-quest-blue/30 shrink-0">
              {getInitials(user.name)}
            </div>
            {!isCollapsed && (
              <div className="overflow-hidden">
                <p className="text-sm font-semibold truncate">{user.name}</p>
                <p className="text-xs text-slate-400 truncate capitalize">{user.role}</p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* =========================================
          2. THE MAIN CONTENT WRAPPER
          ========================================= */}
      <div 
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ease-in-out ${
          isCollapsed ? 'md:ml-20' : 'md:ml-64'
        }`}
      >
        {/* TOP BAR */}
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm">
          <div>
            <h1 className="text-xl font-bold text-quest-navy capitalize">
              {location.pathname.split('/').pop() || 'Dashboard'}
            </h1>
          </div>

          <div className="flex items-center gap-6">
            <NotificationBell />
            <button className="md:hidden text-2xl">🍔</button>
          </div>
        </header>

        {/* DYNAMIC PAGE CONTENT */}
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet /> 
          </div>
        </main>
      </div>

    </div>
  );
}