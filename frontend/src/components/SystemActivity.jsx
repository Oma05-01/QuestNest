import { useState, useEffect } from 'react';

export default function SystemActivity() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchActivity = async () => {
      const token = localStorage.getItem('access_token');
      
      try {
        // Adjust the URL to match your urls.py for SystemActivityView
        const response = await fetch('http://127.0.0.1:8000/api/dashboard/activity/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error('Failed to fetch activity logs');

        const data = await response.json();
        setEvents(data.results || data); 
      } catch (err) {
        setError('Could not load system activity.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchActivity();
  }, []);

  // Helper to color-code different event types (e.g., PAYMENT_SUCCESS, USER_UPDATED)
  const getEventBadge = (eventType) => {
    if (eventType?.includes('PAYMENT') || eventType?.includes('ESCROW')) {
      return <span className="bg-blue-50 text-quest-blue border border-blue-200 px-2 py-1 rounded text-[10px] font-bold tracking-wider">{eventType}</span>;
    }
    if (eventType?.includes('USER') || eventType?.includes('AUTH')) {
      return <span className="bg-purple-50 text-purple-700 border border-purple-200 px-2 py-1 rounded text-[10px] font-bold tracking-wider">{eventType}</span>;
    }
    if (eventType?.includes('FAIL') || eventType?.includes('ERROR')) {
      return <span className="bg-red-50 text-red-700 border border-red-200 px-2 py-1 rounded text-[10px] font-bold tracking-wider">{eventType}</span>;
    }
    return <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-1 rounded text-[10px] font-bold tracking-wider">{eventType || 'SYSTEM_EVENT'}</span>;
  };

  if (isLoading) {
    return <div className="text-center py-10 text-slate-500 animate-pulse font-mono text-sm">Fetching audit logs...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-500">{error}</div>;
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
        <h3 className="text-lg font-bold text-quest-navy">No activity recorded</h3>
        <p className="text-slate-500 text-sm mt-1">System events will appear here in real-time.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse font-mono text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-[10px] uppercase tracking-widest text-slate-500 bg-slate-50/50">
            <th className="py-4 px-4 rounded-tl-xl">Timestamp</th>
            <th className="py-4 px-4">Event Type</th>
            <th className="py-4 px-4">Actor</th>
            <th className="py-4 px-4">Object Ref</th>
            <th className="py-4 px-4 rounded-tr-xl">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {events.map((event) => (
            <tr key={event.id} className="hover:bg-slate-50 transition duration-150 group">
              <td className="py-3 px-4 text-slate-500 whitespace-nowrap text-xs">
                {new Date(event.created_at).toLocaleString('en-GB', { 
                  month: 'short', day: '2-digit', hour: '2-digit', minute:'2-digit', second:'2-digit'
                })}
              </td>
              <td className="py-3 px-4">
                {getEventBadge(event.event_type)}
              </td>
              <td className="py-3 px-4 text-quest-navy font-semibold text-xs">
                {event.actor?.email || 'System'}
              </td>
              <td className="py-3 px-4 text-slate-500 text-xs">
                {event.object_type}: <span className="text-slate-400">{event.object_id?.substring(0,8)}</span>
              </td>
              <td className="py-3 px-4">
                {/* Assuming there might be a status field, fallback to Success if the event exists */}
                <span className="flex items-center gap-1.5 text-xs text-green-600 font-bold">
                  <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>
                  {event.status || 'OK'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}