import React, { createContext, useContext, useEffect } from 'react';

// Fixed blue theme as default
const blueTheme = {
  name: 'Blue',
  description: 'Professional blue theme',
  color: '#3b82f6', // Blue-500
  cssVars: {
    '--primary': '221.2 83.2% 53.3%',
    '--primary-foreground': '210 40% 98%',
    '--secondary': '214 31.8% 91.4%',
    '--secondary-foreground': '222.2 84% 4.9%',
    '--accent': '214 31.8% 91.4%',
    '--accent-foreground': '222.2 84% 4.9%',
    '--muted': '214 31.8% 91.4%',
    '--muted-foreground': '215.4 16.3% 46.9%',
    '--border': '214.3 31.8% 91.4%',
    '--ring': '221.2 83.2% 53.3%'
  }
};

const ThemeContext = createContext({
  currentTheme: 'blue',
  getCurrentThemeData: () => blueTheme
});

export const ThemeProvider = ({ children }) => {
  // Apply blue theme CSS variables on mount
  useEffect(() => {
    const root = document.documentElement;
    Object.entries(blueTheme.cssVars).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });
    
    // Clear any old theme preference from localStorage
    localStorage.removeItem('flagwise-theme');
  }, []);

  const value = {
    currentTheme: 'blue',
    getCurrentThemeData: () => blueTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};