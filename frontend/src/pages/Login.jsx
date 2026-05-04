import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  
  // UI State
  const [step, setStep] = useState('EMAIL'); 
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Form Data
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const API_BASE = 'http://127.0.0.1:8000/api/auth'; // Ensure this matches your Django port

  // 1. CHECK EMAIL
  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE}/check-email/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const data = await res.json();
      if (data.exists) {
        setStep('PASSWORD');
      } else {
        setStep('REGISTER');
      }
    } catch (err) {
      setErrorMsg('Failed to connect to server. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // 2. LOGIN
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE}/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        // Store JWT tokens securely
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Redirect to dashboard
        navigate('/dashboard');
      } else {
        setErrorMsg(data.detail || 'Invalid email or password.');
      }
    } catch (err) {
      setErrorMsg('Login failed. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // 3. REGISTER
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    const fullName = `${firstName} ${lastName}`.trim();

    try {
      const res = await fetch(`${API_BASE}/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name: fullName, password })
      });
      
      if (res.ok) {
        // 🟢 Show the sleek modal instead of the browser alert
        setShowSuccessModal(true); 
      } else {
        setErrorMsg('Registration failed. Please check your details.');
      }
    } catch (err) {
      setErrorMsg('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-quest-slate px-4 py-12">
      <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">
        
        <div className="flex justify-center mb-8">
          <img src="/logo-full.png" alt="QuestNest Logo" className="h-16 w-auto" />
        </div>

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm text-center font-medium">
            {errorMsg}
          </div>
        )}

        {/* --- STEP 1: EMAIL --- */}
        {step === 'EMAIL' && (
          <form onSubmit={handleEmailSubmit} className="space-y-6 animate-in fade-in">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-quest-navy">Sign in or create an account</h2>
            </div>
            <div>
              <label className="block text-sm font-semibold text-quest-navy mb-1.5">Email Address</label>
              <input 
                type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. adesuwa.bello@live.com" autoFocus required
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none"
              />
            </div>
            <button disabled={isLoading} className="w-full bg-quest-navy text-white font-bold py-3.5 rounded-xl hover:bg-quest-navy/90 disabled:opacity-50">
              {isLoading ? 'Checking...' : 'Continue'}
            </button>
          </form>
        )}

        {/* --- STEP 2: PASSWORD --- */}
        {step === 'PASSWORD' && (
          <form onSubmit={handleLoginSubmit} className="space-y-6 animate-in fade-in">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-quest-navy">Welcome back</h2>
              <div className="inline-flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-full mt-2 border border-slate-200">
                <span className="text-sm font-medium text-slate-700">{email}</span>
                <button type="button" onClick={() => setStep('EMAIL')} className="text-xs text-quest-blue font-bold ml-2">Edit</button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-quest-navy mb-1.5">Password</label>
              <input 
                type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••" autoFocus required
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none"
              />
            </div>
            <button disabled={isLoading} className="w-full bg-quest-navy text-white font-bold py-3.5 rounded-xl hover:bg-quest-navy/90 disabled:opacity-50">
              {isLoading ? 'Signing In...' : 'Sign In to QuestNest'}
            </button>
          </form>
        )}

        {/* --- STEP 3: REGISTER --- */}
        {step === 'REGISTER' && (
          <form onSubmit={handleRegisterSubmit} className="space-y-5 animate-in fade-in relative">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-quest-navy">Create your account</h2>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-500 mb-1.5">Email Address</label>
              <input type="email" value={email} disabled className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-quest-navy mb-1.5">First Name</label>
                <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} required className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-quest-navy mb-1.5">Last Name</label>
                <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} required className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-quest-navy mb-1.5">Create Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-quest-blue outline-none" />
            </div>
            <button disabled={isLoading} className="w-full bg-quest-blue text-white font-bold py-3.5 rounded-xl hover:bg-quest-blue/90 disabled:opacity-50 mt-2">
              {isLoading ? 'Creating Account...' : 'Complete Registration'}
            </button>

            {/* 🟢 The QuestNest Success Modal */}
            {showSuccessModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
                <div className="bg-white max-w-sm w-full p-8 rounded-3xl shadow-2xl text-center zoom-in-95 animate-in duration-300">
                  <div className="h-16 w-16 bg-quest-blue/20 text-quest-blue rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                    ✉️
                  </div>
                  <h3 className="text-2xl font-black text-quest-navy mb-2">Welcome to the Nest!</h3>
                  <p className="text-slate-500 mb-6 text-sm">
                    We've sent a verification link to your email. Please click it to activate your account.
                  </p>
                  <button 
                    onClick={() => {
                      setShowSuccessModal(false);
                      setStep('EMAIL'); // Go back to login start
                      setPassword('');
                    }}
                    type="button"
                    className="w-full bg-quest-navy text-white font-bold py-3 rounded-xl hover:bg-opacity-90 transition"
                  >
                    Got it!
                  </button>
                </div>
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
}