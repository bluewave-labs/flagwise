import React from 'react';
import { Button } from './button';
import { cn } from '../../lib/utils';

const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  action,
  actionLabel,
  onAction,
  variant = 'default',
  className 
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'no-data':
        return 'py-16';
      case 'error':
        return 'py-12 bg-red-50 border border-red-100 rounded-lg';
      case 'loading':
        return 'py-12 bg-blue-50 border border-blue-100 rounded-lg';
      default:
        return 'py-12';
    }
  };

  return (
    <div className={cn(
      'flex flex-col items-center justify-center text-center space-y-4',
      getVariantStyles(),
      className
    )}>
      {Icon && (
        <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gray-100">
          <Icon className="w-8 h-8 text-gray-400" />
        </div>
      )}
      
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-gray-900">
          {title}
        </h3>
        {description && (
          <p className="text-sm text-gray-600 max-w-md">
            {description}
          </p>
        )}
      </div>
      
      {action && onAction && (
        <Button
          onClick={onAction}
          variant="outline"
          size="sm"
          className="mt-4"
        >
          {actionLabel || action}
        </Button>
      )}
    </div>
  );
};

const EmptySearchResults = ({ 
  searchTerm, 
  onClearSearch, 
  icon: Icon,
  itemType = 'results' 
}) => {
  return (
    <EmptyState
      icon={Icon}
      title="No results found"
      description={
        searchTerm 
          ? `We couldn't find any ${itemType} matching "${searchTerm}". Try adjusting your search or filters.`
          : `No ${itemType} match your current filters. Try adjusting your search criteria.`
      }
      action={searchTerm ? "Clear search" : "Reset filters"}
      onAction={onClearSearch}
    />
  );
};

const EmptyTable = ({ 
  icon: Icon, 
  title, 
  description,
  actionLabel,
  onAction,
  showAction = true 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {Icon && (
        <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          <Icon className="w-8 h-8 text-gray-400" />
        </div>
      )}
      
      <div className="text-center space-y-2 mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          {title}
        </h3>
        {description && (
          <p className="text-sm text-gray-600 max-w-md">
            {description}
          </p>
        )}
      </div>
      
      {showAction && onAction && actionLabel && (
        <Button
          onClick={onAction}
          size="sm"
          className="bg-teal-600 hover:bg-teal-700 text-white"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

const LoadingState = ({ 
  title = "Loading...", 
  description,
  icon: Icon 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <div className="flex items-center justify-center w-12 h-12">
        {Icon ? (
          <Icon className="w-8 h-8 text-gray-400 animate-pulse" />
        ) : (
          <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        )}
      </div>
      
      <div className="text-center space-y-1">
        <h3 className="text-sm font-medium text-gray-900">
          {title}
        </h3>
        {description && (
          <p className="text-xs text-gray-600">
            {description}
          </p>
        )}
      </div>
    </div>
  );
};

export { 
  EmptyState, 
  EmptySearchResults, 
  EmptyTable, 
  LoadingState 
};