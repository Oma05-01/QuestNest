import { useState, useEffect, useRef } from 'react';

export default function Messages() {
  const [conversations, setConversations] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  
  // New states for actual messages
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);

  const [showNewChat, setShowNewChat] = useState(false);
const [availableContacts, setAvailableContacts] = useState([]); // You'll fetch this from your backend

// 2. Add this function to handle starting a chat
const handleStartChat = async (targetUserId) => {
  const token = localStorage.getItem('access_token');
  const res = await fetch('http://127.0.0.1:8000/api/messages/start/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ user_id: targetUserId })
  });

  if (res.ok) {
    const data = await res.json();
    setShowNewChat(false);
    // Refresh the inbox so the new (or existing) chat appears
    // and ideally set activeChat to this new conversation!
    window.location.reload(); // Quickest way for now, or call fetchInbox() again
  }
};

useEffect(() => {
    const fetchContacts = async () => {
      const token = localStorage.getItem('access_token');
      try {
        const res = await fetch('http://127.0.0.1:8000/api/messages/contacts/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setAvailableContacts(data);
        }
      } catch (err) {
        console.error("Failed to load contacts", err);
      }
    };
    fetchContacts();
  }, []);

  // Auto-scroll ref
  const messagesEndRef = useRef(null);

  // --- 1. Fetch Inbox on Load ---
  useEffect(() => {
    const fetchInbox = async () => {
      const token = localStorage.getItem('access_token');
      try {
        // Adjust this URL to match your user_messages app's inbox endpoint
        const res = await fetch('http://127.0.0.1:8000/api/messages/inbox/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setConversations(data);
        }
      } catch (err) {
        console.error("Failed to load inbox", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchInbox();
  }, []);

  // --- 2. Fetch Chat History when a Conversation is clicked ---
  useEffect(() => {
    if (!activeChat) return;

    const fetchMessages = async () => {
      const token = localStorage.getItem('access_token');
      try {
        // Adjust this URL to match your user_messages app's detail endpoint
        const res = await fetch(`http://127.0.0.1:8000/api/messages/${activeChat.id}/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setMessages(data);
        }
      } catch (err) {
        console.error("Failed to load messages", err);
      }
    };
    
    fetchMessages();
  }, [activeChat]);

  // --- 3. Auto-scroll to bottom of chat ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // --- 4. Send a New Message ---
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeChat) return;
    
    setIsSending(true);
    const token = localStorage.getItem('access_token');

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/messages/${activeChat.id}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ body: newMessage })
      });

      if (res.ok) {
        const sentMsg = await res.json();
        // Append the new message to the UI instantly
        setMessages(prev => [...prev, sentMsg]);
        setNewMessage('');
        
        // Optionally: Update the 'lastMessage' in the sidebar locally so it feels instant
        setConversations(prev => prev.map(conv => 
          conv.id === activeChat.id ? { ...conv, lastMessage: sentMsg.body } : conv
        ));
      }
    } catch (err) {
      alert("Failed to send message.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="bg-white rounded-3xl shadow-sm border border-slate-200 flex h-[75vh] overflow-hidden animate-in fade-in zoom-in-95 duration-500">
      
      {/* --- LEFT PANE: Conversation List --- */}
      <div className="w-1/3 border-r border-slate-100 flex flex-col bg-slate-50/50">
        <div className="p-6 border-b border-slate-100 bg-white flex justify-between items-center">
          <h2 className="text-xl font-black text-quest-navy">Inbox</h2>
          {/* 🟢 The New Message Button */}
          <button 
            onClick={() => setShowNewChat(!showNewChat)}
            className="h-10 w-10 bg-quest-blue text-quest-navy rounded-full flex items-center justify-center text-xl hover:shadow-md transition"
          >
            {showNewChat ? '✕' : '+'}
          </button>
        </div>
        
          {/* 🟢 CONDITIONAL RENDER: Show Contacts OR Show Inbox */}
          {showNewChat ? (
            
            <div className="flex-1 overflow-y-auto p-4 bg-white animate-in slide-in-from-top-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Select Contact</h3>
              
              <div className="space-y-2">
                {availableContacts.length === 0 ? (
                  <p className="text-xs text-slate-400 italic text-center">No contacts available.</p>
                ) : (
                  availableContacts.map(contact => (
                    <div 
                      key={contact.id}
                      onClick={() => handleStartChat(contact.id)} 
                      className="p-3 bg-slate-50 hover:bg-quest-blue/10 rounded-xl cursor-pointer transition flex items-center gap-3 border border-slate-100"
                    >
                      <div className="h-10 w-10 bg-quest-navy text-white rounded-full flex items-center justify-center font-bold shrink-0">
                        {contact.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="overflow-hidden">
                        <p className="font-bold text-quest-navy text-sm truncate">{contact.name}</p>
                        <p className="text-xs text-slate-500 truncate capitalize">{contact.role}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

          ) : (

            <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
              {isLoading ? (
                <p className="text-center text-slate-400 mt-10 text-sm">Loading...</p>
              ) : conversations.length === 0 ? (
                <p className="text-center text-slate-400 mt-10 text-sm italic">No messages yet.</p>
              ) : (
                conversations.map(chat => (
                  <div 
                    key={chat.id}
                    onClick={() => setActiveChat(chat)}
                    className={`p-4 rounded-2xl cursor-pointer transition flex items-center gap-4 ${
                      activeChat?.id === chat.id 
                        ? 'bg-quest-blue/10 border border-quest-blue/20 shadow-sm' 
                        : 'hover:bg-slate-100 border border-transparent'
                    }`}
                  >
                    <div className="h-12 w-12 rounded-full bg-quest-navy text-white flex items-center justify-center font-bold text-lg shrink-0">
                      {chat.avatar || '👤'}
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <div className="flex justify-between items-center mb-1">
                        <h4 className="font-bold text-quest-navy truncate text-sm">{chat.name}</h4>
                        <span className="text-[10px] text-slate-400 font-bold">{chat.time}</span>
                      </div>
                      <div className="flex justify-between items-center mt-0.5">
                        <p className="text-xs text-slate-500 truncate">{chat.lastMessage}</p>
                        {chat.unread > 0 && (
                          <span className="h-5 w-5 bg-quest-blue text-quest-navy flex items-center justify-center rounded-full text-[10px] font-black">
                            {chat.unread}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

          )}
      </div>

      {/* --- RIGHT PANE: Active Chat --- */}
      <div className="flex-1 flex flex-col bg-white">
        {activeChat ? (
          <>
            {/* Chat Header */}
            <div className="p-6 border-b border-slate-100 flex items-center justify-between shadow-sm z-10">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-quest-navy text-white flex items-center justify-center font-bold text-lg">
                  {activeChat.avatar || '👤'}
                </div>
                <div>
                  <h3 className="font-black text-quest-navy text-lg">{activeChat.name}</h3>
                  <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{activeChat.role}</p>
                </div>
              </div>
            </div>

            {/* Chat History (Scrollable) */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-slate-50/30 custom-scrollbar">
              {messages.length === 0 ? (
                <div className="text-center text-slate-400 mt-20 text-sm italic">
                  This is the beginning of your conversation with {activeChat.name}.
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div key={msg.id || index} className={`flex flex-col ${msg.is_me ? 'items-end' : 'items-start'}`}>
                    <div className={`max-w-[70%] p-4 rounded-2xl text-sm shadow-sm ${
                      msg.is_me 
                        ? 'bg-quest-blue text-quest-navy rounded-tr-none font-medium' 
                        : 'bg-slate-100 text-slate-700 rounded-tl-none'
                    }`}>
                      {msg.body}
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 mt-2 uppercase">
                      {msg.is_me ? 'You' : msg.sender_name} • {msg.time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))
              )}
              {/* Invisible div to scroll down to */}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="p-6 border-t border-slate-100 bg-white">
              <form onSubmit={handleSendMessage} className="flex gap-3">
                <input 
                  type="text" 
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Type your message..." 
                  className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-quest-blue focus:bg-white transition text-sm"
                />
                <button 
                  type="submit"
                  disabled={!newMessage.trim() || isSending}
                  className="px-6 py-3 bg-quest-navy text-white font-bold rounded-xl hover:shadow-lg disabled:opacity-50 transition min-w-[100px]"
                >
                  {isSending ? '...' : 'Send ✈️'}
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
            <span className="text-6xl mb-4">💬</span>
            <p className="font-bold">Select a conversation to start messaging</p>
          </div>
        )}
      </div>

    </div>
  );
}