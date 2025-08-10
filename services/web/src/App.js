import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Toaster } from './components/ui/toaster';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './components/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Requests from './pages/Requests';
import FlaggedPrompts from './pages/FlaggedPrompts';
import Sessions from './pages/Sessions';
import LiveFeed from './pages/LiveFeed';
import DetectionRules from './pages/DetectionRules';
import Anomalies from './pages/Anomalies';
import ReviewQueue from './pages/ReviewQueue';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import UserManagement from './pages/UserManagement';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
        <div className="App">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes with dashboard layout */}
            <Route path="/" element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              {/* Activity section */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="requests" element={<Requests />} />
              <Route path="flagged" element={<FlaggedPrompts />} />
              <Route path="sessions" element={<Sessions />} />
              <Route path="live" element={<LiveFeed />} />
              
              {/* Intelligence section */}
              <Route path="rules" element={<DetectionRules />} />
              <Route path="anomalies" element={<Anomalies />} />
              <Route path="review" element={<ReviewQueue />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="analytics" element={<Analytics />} />
              
              {/* Administration section */}
              <Route path="users" element={<UserManagement />} />
              <Route path="settings" element={<Settings />} />
              
              {/* Profile section (dropdown only) */}
              <Route path="profile" element={<Profile />} />
            </Route>
          </Routes>
          <Toaster />
        </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;