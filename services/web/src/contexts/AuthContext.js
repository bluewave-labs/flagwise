import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/api';

const AuthContext = createContext({});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      const savedToken = localStorage.getItem('auth_token');
      const savedUser = localStorage.getItem('auth_user');

      if (savedToken && savedUser) {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        
        // Set token in API client
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
        
        // Skip token verification for performance - trust stored token
        // try {
        //   // Verify token with API
        //   const response = await apiClient.get('/auth/me');
        //   setUser(response.data);
        // } catch (error) {
        //   console.error('Token verification failed:', error);
        //   // Token is invalid, clear auth state
        //   logout();
        // }
      }
      
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (username, password) => {
    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password
      });

      const { access_token, role } = response.data;
      const userData = { username, role };

      // Save to state
      setToken(access_token);
      setUser(userData);

      // Save to localStorage
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('auth_user', JSON.stringify(userData));

      // Set default auth header
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      
      // Handle validation errors properly
      let errorMessage = 'Login failed';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map(err => err.msg).join(', ');
        } else {
          errorMessage = error.response.data.detail;
        }
      }
      
      return { 
        success: false, 
        error: errorMessage
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    delete apiClient.defaults.headers.common['Authorization'];
  };

  const isAdmin = () => {
    return user?.role === 'admin' || user?.role === 'ADMIN';
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const updateUser = (updatedUserData) => {
    const newUserData = { ...user, ...updatedUserData };
    setUser(newUserData);
    localStorage.setItem('auth_user', JSON.stringify(newUserData));
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAdmin,
    isAuthenticated,
    updateUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};