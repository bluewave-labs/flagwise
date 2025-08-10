import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const DashboardLayout = () => {
  return (
    <div className="flex h-screen bg-background relative">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - positioned to align with logo area */}
        <div className="h-[72px] flex items-center">
          <Header />
        </div>
        
        {/* Page content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-muted/10 p-6">
          <Outlet />
        </main>
      </div>
      
      {/* Full-width line under logo area */}
      <div className="absolute top-[72px] left-0 right-0 h-px bg-gray-200 z-10"></div>
    </div>
  );
};

export default DashboardLayout;