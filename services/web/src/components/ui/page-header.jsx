import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { Button } from './button';
import { cn } from '../../lib/utils';

const PageHeader = ({ 
  title, 
  description, 
  showBackButton = false, 
  onBack, 
  children,
  className 
}) => {
  return (
    <div className={cn("border-b border-gray-200 bg-white", className)}>
      <div className="px-6 py-6">
        {/* Back button and title */}
        <div className="flex items-center space-x-4 mb-2">
          {showBackButton && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="p-1 h-8 w-8"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          )}
          <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
        </div>
        
        {/* Description */}
        {description && (
          <p className="text-13 text-gray-600 mb-4 max-w-4xl">
            {description}
          </p>
        )}
        
        {/* Action buttons or additional content */}
        {children && (
          <div className="flex items-center justify-between">
            <div></div>
            <div className="flex items-center space-x-3">
              {children}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const PageHeaderTabs = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div className="border-b border-gray-200">
      <nav className="px-6 -mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "py-3 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === tab.id
                ? "border-teal-600 text-teal-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            )}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
};

export { PageHeader, PageHeaderTabs };