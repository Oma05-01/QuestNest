import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

export default function VerifyEmail() {
  // Grab the dynamic parts of the URL (e.g., /verify/:uid/:token)
  const { uid, token } = useParams();
  
  // UI State: 'verifying', 'success', 'error'
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyAccount = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/auth/verify-email/${uid}/${token}/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setMessage(data.message);
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed.');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Network error. Ensure the server is running.');
      }
    };

    // Fire the verification immediately when the page loads
    if (uid && token) {
      verifyAccount();
    }
  }, [uid, token]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-quest-slate px-4">
      <div className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-md border border-slate-100 text-center animate-in fade-in zoom-in-95 duration-300">
        
        {/* Loading State */}
        {status === 'verifying' && (
          <div className="flex flex-col items-center">
            {/* Spinning Icon */}
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quest-blue mb-4"></div>
            <h2 className="text-xl font-bold text-quest-navy">Verifying your email...</h2>
            <p className="text-slate-500 mt-2 text-sm">Please wait a moment while we secure your account.</p>
          </div>
        )}

        {/* Success State */}
        {status === 'success' && (
          <div className="flex flex-col items-center">
            <div className="h-16 w-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-3xl mb-4">
              ✅
            </div>
            <h2 className="text-2xl font-bold text-quest-navy">Email Verified!</h2>
            <p className="text-slate-500 mt-2 mb-8">{message}</p>
            <Link 
              to="/login"
              className="w-full bg-quest-navy text-white font-bold py-3.5 rounded-xl hover:bg-quest-navy/90 transition duration-150 shadow-md inline-block"
            >
              Go to Login
            </Link>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && (
          <div className="flex flex-col items-center">
            <div className="h-16 w-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-3xl mb-4">
              ❌
            </div>
            <h2 className="text-2xl font-bold text-quest-navy">Verification Failed</h2>
            <p className="text-slate-500 mt-2 mb-8">{message}</p>
            <Link 
              to="/login"
              className="text-quest-blue font-bold hover:underline"
            >
              Return to Login
            </Link>
          </div>
        )}

      </div>
    </div>
  );
}