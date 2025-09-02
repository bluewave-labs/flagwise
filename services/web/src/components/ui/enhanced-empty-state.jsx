import React from 'react';
import { Button } from './button';
import { Card, CardContent } from './card';

export const EnhancedEmptyState = ({
  icon: Icon,
  title,
  description,
  actions = [],
  suggestions = [],
  className = ""
}) => {
  return (
    <div className={`text-center py-12 ${className}`}>
      {Icon && <Icon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />}
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground mb-6 max-w-md mx-auto">
        {description}
      </p>
      
      {actions.length > 0 && (
        <div className="flex flex-wrap justify-center gap-3 mb-6">
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant || "default"}
              onClick={action.onClick}
              disabled={action.disabled}
            >
              {action.icon && <action.icon className="h-4 w-4 mr-2" />}
              {action.label}
            </Button>
          ))}
        </div>
      )}
      
      {suggestions.length > 0 && (
        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <h4 className="text-sm font-semibold mb-4 text-left">What you can do next:</h4>
            <ul className="text-sm text-muted-foreground space-y-2 text-left">
              {suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start">
                  <span className="font-medium text-primary mr-2">{index + 1}.</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Preset empty states for common scenarios
export const NoDataEmptyState = ({ entityName, onCreateClick, createLabel, showSuggestions = true }) => (
  <EnhancedEmptyState
    icon={Database}
    title={`No ${entityName} found`}
    description={`You haven't created any ${entityName} yet. Get started by creating your first one.`}
    actions={onCreateClick ? [{
      label: createLabel || `Create ${entityName}`,
      onClick: onCreateClick,
      variant: "default"
    }] : []}
    suggestions={showSuggestions ? [
      `Create your first ${entityName} to start collecting data`,
      "Configure detection rules to automatically flag suspicious activity",
      "Set up alerts to get notified about important events",
      "Review system settings to optimize performance"
    ] : []}
  />
);

export const NoResultsEmptyState = ({ searchTerm, onClearFilters, onCreateClick, entityName }) => (
  <EnhancedEmptyState
    icon={Search}
    title="No results found"
    description={searchTerm 
      ? `No ${entityName} match your search criteria. Try adjusting your filters or search terms.`
      : `No ${entityName} match your current filters.`
    }
    actions={[
      ...(onClearFilters ? [{
        label: "Clear Filters",
        onClick: onClearFilters,
        variant: "outline"
      }] : []),
      ...(onCreateClick ? [{
        label: `Create ${entityName}`,
        onClick: onCreateClick,
        variant: "default"
      }] : [])
    ]}
    suggestions={[
      "Try using different search terms or filters",
      "Check your spelling and try again",
      "Clear all filters to see all available items",
      "Create new content if you're looking for something specific"
    ]}
  />
);

export const ErrorEmptyState = ({ error, onRetry, onReport }) => (
  <EnhancedEmptyState
    icon={AlertCircle}
    title="Something went wrong"
    description={error || "We encountered an error while loading data. Please try again."}
    actions={[
      ...(onRetry ? [{
        label: "Try Again",
        onClick: onRetry,
        variant: "default"
      }] : []),
      ...(onReport ? [{
        label: "Report Issue",
        onClick: onReport,
        variant: "outline"
      }] : [])
    ]}
    suggestions={[
      "Check your internet connection",
      "Refresh the page and try again",
      "Contact support if the problem persists",
      "Try accessing the data from a different page"
    ]}
  />
);

// Import required icons
import { Database, Search, AlertCircle } from 'lucide-react';