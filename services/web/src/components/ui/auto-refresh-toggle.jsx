import React, { useState } from 'react';
import { Button } from './button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
import { Switch } from './switch';
import { Card, CardContent } from './card';
import { RefreshCw, Pause, Play, Settings } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { INTERVAL_LABELS } from '../../hooks/useAutoRefresh';

export const AutoRefreshToggle = ({
  isEnabled,
  interval,
  onToggle,
  onIntervalChange,
  onManualRefresh,
  lastRefresh,
  className = "",
  showLastRefresh = true,
  compact = false
}) => {
  const [showSettings, setShowSettings] = useState(false);

  const formatLastRefresh = (timestamp) => {
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 60000) {
      return `${Math.floor(diff / 1000)}s ago`;
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}m ago`;
    } else {
      return new Date(timestamp).toLocaleTimeString();
    }
  };

  const intervalOptions = [
    { value: 1000, label: '1 second' },
    { value: 5000, label: '5 seconds' },
    { value: 15000, label: '15 seconds' },
    { value: 30000, label: '30 seconds' },
    { value: 60000, label: '1 minute' },
    { value: 120000, label: '2 minutes' },
    { value: 300000, label: '5 minutes' }
  ];

  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Button
          variant="outline"
          size="sm"
          onClick={onManualRefresh}
          className="h-8"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
        
        <Popover open={showSettings} onOpenChange={setShowSettings}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="h-8">
              {isEnabled ? (
                <Play className="h-3 w-3 text-green-600" />
              ) : (
                <Pause className="h-3 w-3 text-gray-400" />
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-72">
            <div className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Auto-refresh</h4>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Enable auto-refresh</span>
                  <Switch checked={isEnabled} onCheckedChange={onToggle} />
                </div>
              </div>
              
              {isEnabled && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Refresh interval</label>
                  <Select value={interval.toString()} onValueChange={(value) => onIntervalChange(parseInt(value))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {intervalOptions.map(option => (
                        <SelectItem key={option.value} value={option.value.toString()}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              {showLastRefresh && lastRefresh && (
                <div className="text-xs text-muted-foreground">
                  Last updated: {formatLastRefresh(lastRefresh)}
                </div>
              )}
            </div>
          </PopoverContent>
        </Popover>
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h4 className="font-medium text-sm">Auto-refresh</h4>
              <p className="text-xs text-muted-foreground">
                Automatically refresh data every {INTERVAL_LABELS[interval] || `${interval/1000}s`}
              </p>
            </div>
            <Switch checked={isEnabled} onCheckedChange={onToggle} />
          </div>
          
          {isEnabled && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Refresh interval</label>
              <Select value={interval.toString()} onValueChange={(value) => onIntervalChange(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {intervalOptions.map(option => (
                    <SelectItem key={option.value} value={option.value.toString()}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="text-xs text-muted-foreground">
              {showLastRefresh && lastRefresh && `Last updated: ${formatLastRefresh(lastRefresh)}`}
            </div>
            <Button variant="outline" size="sm" onClick={onManualRefresh}>
              <RefreshCw className="h-3 w-3 mr-1" />
              Refresh now
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};