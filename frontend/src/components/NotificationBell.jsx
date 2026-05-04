import { useState, useEffect, useRef } from 'react';

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  
  const dropdownRef = useRef(null);

  // --- 1. Fetch Notifications ---
  useEffect(() => {
    const fetchNotifications = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      try {
        const res = await fetch('http://127.0.0.1:8000/api/dashboard/notifications/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          const data = await res.json();
          // Based on your Django view, it returns unread_count and results
          setUnreadCount(data.unread_count || 0);
          setNotifications(data.results || []);
        }
      } catch (error) {
        console.error("Failed to load notifications", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  // --- 2. Handle Click Outside to Close Dropdown ---
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // --- 3. Mark as Read Action ---
  const handleMarkAsRead = async (id, isAlreadyRead) => {
    if (isAlreadyRead) return; // Don't waste an API call

    const token = localStorage.getItem('access_token');
    
    // Optimistic UI Update: Instantly update UI before server responds to feel ultra-fast
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    setUnreadCount(prev => Math.max(0, prev - 1));

    try {
      await fetch(`http://127.0.0.1:8000/api/dashboard/notifications/${id}/read/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error("Failed to mark notification as read");
      // If it fails, you could revert the optimistic update here
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* 🔔 The Bell Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-400 hover:text-quest-navy transition focus:outline-none"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>

        {/* 🔴 Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 h-4 w-4 bg-red-500 rounded-full border-2 border-white text-[10px] font-bold text-white flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* 📋 The Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border border-slate-100 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <h3 className="font-bold text-quest-navy">Notifications</h3>
            {unreadCount > 0 && (
              <span className="text-xs font-semibold text-quest-blue bg-blue-50 px-2 py-1 rounded-full">
                {unreadCount} new
              </span>
            )}
          </div>

          <div className="max-h-[400px] overflow-y-auto">
            {isLoading ? (
              <div className="p-6 text-center text-sm text-slate-500 animate-pulse">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <div className="text-3xl mb-2">📭</div>
                <p className="text-sm text-slate-500">You're all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.map((notification) => (
                  <div 
                    key={notification.id}
                    onClick={() => handleMarkAsRead(notification.id, notification.is_read)}
                    className={`p-4 hover:bg-slate-50 cursor-pointer transition flex gap-4 ${
                      !notification.is_read ? 'bg-blue-50/30' : ''
                    }`}
                  >
                    {/* Unread dot indicator */}
                    <div className="mt-1.5">
                      <div className={`h-2.5 w-2.5 rounded-full ${!notification.is_read ? 'bg-quest-blue' : 'bg-transparent'}`}></div>
                    </div>
                    
                    <div className="flex-1">
                      {/* Note: Adjust 'message' based on your actual Notification model fields */}
                      <p className={`text-sm ${!notification.is_read ? 'font-semibold text-quest-navy' : 'text-slate-600'}`}>
                        {notification.message || notification.title}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {new Date(notification.created_at).toLocaleString('en-GB', { 
                          hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' 
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-3 border-t border-slate-100 text-center bg-slate-50/50">
            <button className="text-xs font-bold text-quest-blue hover:text-quest-navy transition">
              View All Notifications
            </button>
          </div>
        </div>
      )}
    </div>
  );
}