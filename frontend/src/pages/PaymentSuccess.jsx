import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const hasVerified = useRef(false); // Prevents double-calling the API in StrictMode

  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [message, setMessage] = useState('Please wait while we verify your payment...');

  useEffect(() => {
    const reference = searchParams.get('reference') || searchParams.get('trxref');

    if (!reference) {
      setStatus('error');
      setMessage('No transaction reference found.');
      return;
    }

    if (hasVerified.current) return;
    hasVerified.current = true;

    const verifyPayment = async () => {
      const token = localStorage.getItem('access_token');
      try {
        const response = await fetch('http://127.0.0.1:8000/api/wallet/fund/verify/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ reference })
        });

        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setMessage('Payment verified! Your wallet has been credited.');
          // Auto-redirect back to wallet after 3 seconds
          setTimeout(() => navigate('/dashboard/wallet'), 3000);
        } else {
          setStatus('error');
          setMessage(data.error || 'Verification failed.');
        }
      } catch (err) {
        setStatus('error');
        setMessage('Network error during verification.');
      }
    };

    verifyPayment();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <div className="bg-white max-w-md w-full p-8 rounded-3xl shadow-xl border border-slate-100 text-center animate-in fade-in zoom-in-95 duration-500">
        
        {status === 'verifying' && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quest-blue mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold text-quest-navy mb-2">Verifying Payment</h2>
            <p className="text-slate-500">{message}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="h-20 w-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-4xl mx-auto mb-6">
              ✅
            </div>
            <h2 className="text-2xl font-bold text-quest-navy mb-2">Payment Successful!</h2>
            <p className="text-slate-500 mb-8">{message}</p>
            <Link to="/dashboard/wallet" className="inline-block px-8 py-3 bg-quest-navy text-white font-bold rounded-xl shadow-md">
              Back to Wallet
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="h-20 w-20 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-4xl mx-auto mb-6">
              ❌
            </div>
            <h2 className="text-2xl font-bold text-quest-navy mb-2">Verification Failed</h2>
            <p className="text-slate-500 mb-8">{message}</p>
            <div className="flex gap-4">
              <Link to="/dashboard/wallet" className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 font-bold rounded-xl">
                Cancel
              </Link>
              <button onClick={() => window.location.reload()} className="flex-1 px-4 py-3 bg-quest-navy text-white font-bold rounded-xl">
                Retry
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}