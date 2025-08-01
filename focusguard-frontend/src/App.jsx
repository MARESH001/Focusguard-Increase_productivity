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

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(true);

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
  }, []);

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
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('focusguard_user');
    setCurrentView('dashboard');
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
    </div>
  );
}

export default App;

