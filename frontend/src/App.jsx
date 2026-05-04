import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import VerifyEmail from './pages/VerifyEmail';
import DashboardLayout from './components/DashboardLayout';
import ProtectedRoute from './components/ProtectedRoute';
import Overview from './pages/Overview';
import Settings from './pages/Settings';
import Properties from './pages/Properties';
import PropertyDetail from './pages/PropertyDetail';
import Leases from './pages/Leases';
import LeaseViewer from './pages/LeaseViewer';
import Wallet from './pages/Wallet';
import PaymentSuccess from './pages/PaymentSuccess';
import Messages from './pages/Messages';
import Maintenance from './pages/Maintenance';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/verify/:uid/:token" element={<VerifyEmail />} />

        {/* 🛡️ The Master Protected Route */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          {/* All these children automatically inherit "/dashboard" and the protection */}
          <Route index element={<Overview />} /> 
          <Route path="settings" element={<Settings />} /> 
          
          <Route path="properties" element={<Properties />} /> 
          <Route path="properties/:id" element={<PropertyDetail />} /> 
          
          <Route path="leases" element={<Leases />} /> 
          <Route path="wallet" element={<Wallet />} /> 

          <Route path="maintenance" element={<Maintenance />} />

          <Route path="messages" element={<Messages />} />
          
          {/* 🟢 Corrected: Nested cleanly inside the dashboard block */}
          <Route path="leases/:id" element={<LeaseViewer />} /> 
        </Route>

        
        <Route path="payment/success" element={<PaymentSuccess />} />
        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}