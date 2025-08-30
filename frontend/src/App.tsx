import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import BrokersPage from './pages/BrokersPage';
import AuthPage from './pages/AuthPage';
import LoadingSpinner from './components/common/LoadingSpinner';

// Main App Component (inside AuthProvider)
const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show auth page if not authenticated (regardless of loading state during auth flows)
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  // Show loading spinner only for initial app authentication check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <LoadingSpinner message="Loading application..." />
      </div>
    );
  }

  // Render main application with routing
  return (
    <BrowserRouter future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true
    }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="brokers" element={<BrokersPage />} />
          <Route path="strategies" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Strategies</h1><p>Coming Soon</p></div>} />
          <Route path="portfolio" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Portfolio</h1><p>Coming Soon</p></div>} />
          <Route path="analytics" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Analytics</h1><p>Coming Soon</p></div>} />
          <Route path="settings" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Settings</h1><p>Settings configuration will be available here.</p></div>} />
          <Route path="account" element={<div className="space-y-6"><h1 className="text-2xl font-bold">Account</h1><p>Account management features will be available here.</p></div>} />
        </Route>
        
        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

// Root App Component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;