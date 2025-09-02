import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const DashboardLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Check if screen size is mobile
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
      // Auto-close sidebar on mobile when screen size changes
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      }
    };

    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  // Close sidebar when clicking outside on mobile
  const closeSidebar = () => {
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  };

  return (
    <div className="flex h-screen bg-background relative">
      {/* Mobile Overlay */}
      {isMobile && isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <Sidebar 
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
        isMobile={isMobile}
      />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - positioned to align with logo area */}
        <div className="h-[72px] flex items-center">
          <Header 
            onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
            showMenuButton={isMobile}
          />
        </div>
        
        {/* Page content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-muted/10 p-3 md:p-6">
          <Outlet />
        </main>
      </div>
      
      {/* Full-width line under logo area */}
      <div className="absolute top-[72px] left-0 right-0 h-px bg-gray-200 z-10"></div>
    </div>
  );
};

export default DashboardLayout;