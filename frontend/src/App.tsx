import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { OAuthProvider } from './context/OAuthContext';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import BrokersPage from './pages/BrokersPage';
import BasketsPage from './pages/BasketsPage';
import AuthPage from './pages/AuthPage';
import LoadingSpinner from './components/common/LoadingSpinner';
import OAuthCallback from './components/oauth/OAuthCallback';


// Main App Component (inside AuthProvider)
const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <BrowserRouter future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true
    }}>
      <Routes>
        {/* OAuth callback route - accessible without authentication */}
        <Route path="/oauth/callback" element={<OAuthCallback />} />
        
        {/* Auth page route - redirect to dashboard if already authenticated */}
        <Route 
          path="/auth" 
          element={
            isLoading && !window.location.pathname.includes('/auth') ? (
              <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <LoadingSpinner message="Loading application..." />
              </div>
            ) : isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <AuthPage />
            )
          } 
        />
        
        {/* Protected routes with Layout */}
        <Route
          path="/*"
          element={
            isLoading ? (
              <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <LoadingSpinner message="Loading application..." />
              </div>
            ) : !isAuthenticated ? (
              <Navigate to="/auth" replace />
            ) : (
              <Layout />
            )
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="brokers" element={<BrokersPage />} />
          <Route path="baskets" element={<BasketsPage />} />
          <Route path="strategies" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Strategies</h1><p>Coming Soon</p></div>} />
          <Route path="portfolio" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Portfolio</h1><p>Coming Soon</p></div>} />
          <Route path="analytics" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Analytics</h1><p>Coming Soon</p></div>} />
          <Route path="settings" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Settings</h1><p>Settings configuration will be available here.</p></div>} />
          <Route path="account" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Account</h1><p>Account management features will be available here.</p></div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

// Root App Component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <OAuthProvider>
        <AppContent />
      </OAuthProvider>
    </AuthProvider>
  );
};

export default App;