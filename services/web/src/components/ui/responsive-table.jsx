import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './table';
import { Card, CardContent } from './card';
import { Badge } from './badge';
import { Button } from './button';
import { cn } from '../../lib/utils';
import { ChevronDown, ChevronRight } from 'lucide-react';

const ResponsiveTable = ({ 
  data, 
  columns, 
  className,
  mobileCardRenderer,
  showMobileCards = true,
  breakpoint = 768 
}) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < breakpoint);
    };

    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, [breakpoint]);

  // Mobile card view
  if (isMobile && showMobileCards && mobileCardRenderer) {
    return (
      <div className={cn("space-y-3", className)}>
        {data.map((item, index) => (
          <Card key={item.id || index} className="w-full">
            <CardContent className="p-4">
              {mobileCardRenderer(item, index)}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Desktop table view
  return (
    <div className="rounded-md border overflow-x-auto">
      <Table className={className}>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column.key} className={column.headerClassName}>
                {column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((item, index) => (
            <TableRow key={item.id || index}>
              {columns.map((column) => (
                <TableCell key={column.key} className={column.cellClassName}>
                  {column.render ? column.render(item, index) : item[column.key]}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

// Mobile card components for common data types
const UserMobileCard = ({ user, onEdit, onDelete, showActions = true }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium">
            {user.first_name?.charAt(0) || user.username?.charAt(0) || 'U'}
          </div>
          <div>
            <p className="font-medium text-sm">
              {user.first_name && user.last_name 
                ? `${user.first_name} ${user.last_name}` 
                : user.username}
            </p>
            <p className="text-xs text-muted-foreground">{user.username}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
            {user.role === 'admin' ? 'Admin' : 'User'}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Expandable details */}
      {expanded && (
        <div className="space-y-2 pt-2 border-t">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Status:</span>
              <div className="mt-1">
                <Badge variant={user.is_active ? 'default' : 'destructive'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">Created:</span>
              <p className="mt-1">{new Date(user.created_at).toLocaleDateString()}</p>
            </div>
          </div>

          {showActions && (
            <div className="flex space-x-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => onEdit?.(user)} className="flex-1">
                Edit
              </Button>
              <Button size="sm" variant="destructive" onClick={() => onDelete?.(user.id)} className="flex-1">
                Delete
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const RequestMobileCard = ({ request, onView, showDetails = true }) => {
  const [expanded, setExpanded] = useState(false);

  const getRiskBadgeVariant = (score) => {
    if (score >= 70) return 'destructive';
    if (score >= 40) return 'secondary';
    if (score >= 10) return 'outline';
    return 'default';
  };

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0 mr-3">
          <div className="flex items-center space-x-2 mb-1">
            <Badge variant="outline" className="text-xs">
              {request.provider}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {new Date(request.timestamp).toLocaleString()}
            </span>
          </div>
          <p className="text-sm font-medium text-gray-900 truncate">
            {request.model || 'Unknown Model'}
          </p>
          <p className="text-xs text-muted-foreground">
            IP: {request.src_ip}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {request.risk_score && (
            <Badge variant={getRiskBadgeVariant(request.risk_score)}>
              {request.risk_score}%
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Expandable details */}
      {expanded && showDetails && (
        <div className="space-y-3 pt-2 border-t">
          {request.prompt && (
            <div>
              <span className="text-xs font-medium text-muted-foreground">Prompt:</span>
              <p className="text-sm mt-1 p-2 bg-muted rounded text-xs">
                {request.prompt.length > 200 
                  ? `${request.prompt.substring(0, 200)}...` 
                  : request.prompt
                }
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-muted-foreground">Duration:</span>
              <p className="mt-1">{request.duration_ms}ms</p>
            </div>
            <div>
              <span className="text-muted-foreground">Status:</span>
              <p className="mt-1">
                <Badge variant={request.flagged ? 'destructive' : 'default'}>
                  {request.flagged ? 'Flagged' : 'Clean'}
                </Badge>
              </p>
            </div>
          </div>

          {onView && (
            <Button size="sm" variant="outline" onClick={() => onView(request)} className="w-full">
              View Details
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

const RuleMobileCard = ({ rule, onEdit, onDelete, onToggle, showActions = true }) => {
  const [expanded, setExpanded] = useState(false);

  const getSeverityBadgeVariant = (severity) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'secondary';
      case 'medium': return 'outline';
      case 'low': return 'default';
      default: return 'default';
    }
  };

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0 mr-3">
          <div className="flex items-center space-x-2 mb-1">
            <Badge variant={getSeverityBadgeVariant(rule.severity)}>
              {rule.severity}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {rule.rule_type?.replace('_', ' ')}
            </Badge>
          </div>
          <p className="text-sm font-medium text-gray-900">
            {rule.name}
          </p>
          <p className="text-xs text-muted-foreground truncate">
            {rule.description}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={rule.is_active ? 'default' : 'secondary'}>
            {rule.is_active ? 'Active' : 'Inactive'}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Expandable details */}
      {expanded && (
        <div className="space-y-3 pt-2 border-t">
          <div>
            <span className="text-xs font-medium text-muted-foreground">Pattern:</span>
            <p className="text-xs mt-1 p-2 bg-muted rounded font-mono">
              {rule.pattern}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <span className="text-muted-foreground">Points:</span>
              <p className="mt-1 font-medium">{rule.points}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Priority:</span>
              <p className="mt-1 font-medium">{rule.priority}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Category:</span>
              <p className="mt-1 capitalize">{rule.category?.replace('_', ' ')}</p>
            </div>
          </div>

          {showActions && (
            <div className="grid grid-cols-3 gap-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => onEdit?.(rule)}>
                Edit
              </Button>
              <Button 
                size="sm" 
                variant={rule.is_active ? 'secondary' : 'default'}
                onClick={() => onToggle?.(rule.id, !rule.is_active)}
              >
                {rule.is_active ? 'Disable' : 'Enable'}
              </Button>
              <Button size="sm" variant="destructive" onClick={() => onDelete?.(rule.id)}>
                Delete
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export { 
  ResponsiveTable, 
  UserMobileCard, 
  RequestMobileCard, 
  RuleMobileCard 
};