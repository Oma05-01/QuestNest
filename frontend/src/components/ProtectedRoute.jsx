import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children }) {
  // TODO: We will connect this to your Django backend's JWT later.
  // For now, we simulate a logged-out user (set to true to test the dashboard)
  const isAuthenticated = true; 

  if (!isAuthenticated) {
    // Kick them to login if they have no token
    return <Navigate to="/login" replace />;
  }

  // Let them through if they are authenticated
  return children;
}