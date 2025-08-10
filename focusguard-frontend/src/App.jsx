import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import LoginScreen from './components/LoginScreen';
import Dashboard from './components/Dashboard';
import FocusTimer from './components/FocusTimer';
import Statistics from './components/Statistics';
import DailyPlan from './components/DailyPlan';
import ParticleBackground from './components/ParticleBackground';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(true);
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);

  // Check for stored user on app load
  useEffect(() => {
    const storedUser = localStorage.getItem('focusguard_user');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setCurrentUser(userData);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('focusguard_user');
      }
    }
    setIsLoading(false);
    
    // Check backend health on app start
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/`, { 
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
      });
      if (response.ok) {
        setIsBackendAvailable(true);
      } else {
        setIsBackendAvailable(false);
      }
    } catch (error) {
      console.log('Backend not available on app start:', error.message);
      setIsBackendAvailable(false);
    }
  };

  const handleLogin = async (username) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username }),
      });

      if (response.ok) {
        const userData = await response.json();
        setCurrentUser(userData);
        localStorage.setItem('focusguard_user', JSON.stringify(userData));
        setIsBackendAvailable(true); // Backend is working if login succeeded
        
        // Handle username modification feedback
        if (userData.username_modified) {
          // Show notification about username change
          toast.info(
            `Username "${userData.original_username}" was already taken. Your username is now "${userData.username}"`,
            {
              duration: 5000,
              action: {
                label: 'OK',
                onClick: () => console.log('Username change acknowledged')
              }
            }
          );
        } else if (userData.message) {
          // Show welcome message
          toast.success(userData.message, {
            duration: 3000
          });
        }
        
        return { success: true, userData };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      setIsBackendAvailable(false);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('focusguard_user');
    setCurrentView('dashboard');
    // Clear any stored notifications
    localStorage.removeItem('notifications');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <ParticleBackground />
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading FocusGuard...</p>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen">
        <ParticleBackground />
        <LoginScreen onLogin={handleLogin} />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <ParticleBackground />
      <div className="relative z-10">
        <Router>
          <Routes>
            <Route 
              path="/" 
              element={
                <Dashboard 
                  user={currentUser}
                  currentView={currentView}
                  setCurrentView={setCurrentView}
                  onLogout={handleLogout}
                  apiBaseUrl={API_BASE_URL}
                  isBackendAvailable={isBackendAvailable}
                  onBackendStatusChange={setIsBackendAvailable}
                />
              } 
            />
            <Route 
              path="/timer" 
              element={
                <FocusTimer 
                  user={currentUser}
                  onBack={() => setCurrentView('dashboard')}
                  apiBaseUrl={API_BASE_URL}
                />
              } 
            />
            <Route 
              path="/stats" 
              element={
                <Statistics 
                  user={currentUser}
                  onBack={() => setCurrentView('dashboard')}
                  apiBaseUrl={API_BASE_URL}
                />
              } 
            />
            <Route 
              path="/plan" 
              element={
                <DailyPlan 
                  user={currentUser}
                  onBack={() => setCurrentView('dashboard')}
                  apiBaseUrl={API_BASE_URL}
                />
              } 
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </div>
      <Toaster />
    </div>
  );
}

export default App;

