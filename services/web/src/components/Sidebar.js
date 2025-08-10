import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';
import {
  LayoutDashboard,
  Database,
  AlertTriangle,
  Users,
  Activity,
  Shield,
  Settings,
  Bell,
  Target,
  BarChart3
} from 'lucide-react';

const sidebarSections = [
  {
    title: 'Activity',
    items: [
      { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { name: 'LLM Requests', href: '/requests', icon: Database },
      { name: 'Flagged Prompts', href: '/flagged', icon: AlertTriangle },
      { name: 'Sessions', href: '/sessions', icon: Users },
      { name: 'Live Feed', href: '/live', icon: Activity }
    ]
  },
  {
    title: 'Intelligence',
    items: [
      { name: 'Detection Rules', href: '/rules', icon: Shield, adminOnly: true },
      { name: 'Alerts', href: '/alerts', icon: Bell },
      { name: 'Analytics', href: '/analytics', icon: BarChart3 }
    ]
  },
  {
    title: 'Administration',
    items: [
      { name: 'User Management', href: '/users', icon: Users, adminOnly: true },
      { name: 'System Settings', href: '/settings', icon: Settings, adminOnly: true }
    ]
  }
];

const SidebarItem = ({ item, isActive }) => {
  const Icon = item.icon;
  
  return (
    <NavLink
      to={item.href}
      className={({ isActive }) =>
        cn(
          "flex items-center px-3 py-1.5 rounded-lg sidebar-link-text transition-all duration-200 group",
          isActive
            ? "bg-teal-50 text-teal-700"
            : "text-main hover:text-gray-900 hover:bg-gray-100"
        )
      }
    >
      <Icon className={cn(
        "h-4 w-4 mr-3 transition-colors",
        isActive ? "text-teal-600" : "text-gray-400 group-hover:text-gray-600"
      )} />
      {item.name}
    </NavLink>
  );
};

const Sidebar = () => {
  const { isAdmin } = useAuth();
  const location = useLocation();

  return (
    <div className="w-64 bg-white h-full border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center px-6 py-5">
        <NavLink to="/dashboard" className="flex items-center hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 bg-teal-600 rounded-md flex items-center justify-center mr-3">
            <Target className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-lg font-semibold text-gray-900">FlagWise</h1>
        </NavLink>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-8">
        {sidebarSections.map((section) => (
          <div key={section.title}>
            <h3 className="px-3 mb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
              {section.title}
            </h3>
            <div className="space-y-0">
              {section.items
                .filter(item => !item.adminOnly || isAdmin())
                .map((item) => (
                  <SidebarItem
                    key={item.name}
                    item={item}
                    isActive={location.pathname === item.href}
                  />
                ))}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;