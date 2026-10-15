// src/components/ProtectedRoute.jsx
import { Navigate, useLocation } from 'react-router-dom';

function isTokenExpired(token) {
  if (!token) return true;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    // exp is in seconds; Date.now() is in milliseconds
    return payload.exp * 1000 < Date.now();
  } catch (e) {
    return true; // Invalid token format
  }
}

export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const token = localStorage.getItem('access_token');

  // If missing or expired, clear invalid state and redirect
  if (!token || isTokenExpired(token)) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}