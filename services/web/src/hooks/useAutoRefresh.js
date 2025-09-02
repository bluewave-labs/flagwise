import { useState, useEffect, useRef, useCallback } from 'react';

export const useAutoRefresh = ({
  fetchFunction,
  defaultInterval = 30000, // 30 seconds
  defaultEnabled = false,
  dependencies = []
}) => {
  const [isEnabled, setIsEnabled] = useState(defaultEnabled);
  const [interval, setInterval] = useState(defaultInterval);
  const [lastRefresh, setLastRefresh] = useState(Date.now());
  const intervalRef = useRef(null);
  const isActiveRef = useRef(true);

  // Handle visibility change to pause/resume when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      isActiveRef.current = !document.hidden;
      if (document.hidden && intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      } else if (!document.hidden && isEnabled) {
        startAutoRefresh();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isEnabled]);

  const startAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    if (isEnabled && isActiveRef.current) {
      intervalRef.current = setInterval(() => {
        fetchFunction();
        setLastRefresh(Date.now());
      }, interval);
    }
  }, [fetchFunction, interval, isEnabled]);

  const stopAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const manualRefresh = useCallback(() => {
    fetchFunction();
    setLastRefresh(Date.now());
    // Restart the interval after manual refresh
    if (isEnabled) {
      startAutoRefresh();
    }
  }, [fetchFunction, isEnabled, startAutoRefresh]);

  const toggleAutoRefresh = useCallback(() => {
    setIsEnabled(prev => !prev);
  }, []);

  const updateInterval = useCallback((newInterval) => {
    setInterval(newInterval);
    if (isEnabled) {
      stopAutoRefresh();
      // Will restart with new interval due to useEffect dependency
    }
  }, [isEnabled, stopAutoRefresh]);

  // Start/stop auto-refresh based on enabled state
  useEffect(() => {
    if (isEnabled) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }

    return () => stopAutoRefresh();
  }, [isEnabled, startAutoRefresh, stopAutoRefresh]);

  // Restart auto-refresh when dependencies change
  useEffect(() => {
    if (isEnabled) {
      startAutoRefresh();
    }
  }, [...dependencies, startAutoRefresh]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopAutoRefresh();
  }, [stopAutoRefresh]);

  return {
    isEnabled,
    interval,
    lastRefresh,
    toggleAutoRefresh,
    updateInterval,
    manualRefresh,
    setIsEnabled,
    setInterval: updateInterval
  };
};

// Predefined intervals in milliseconds
export const REFRESH_INTERVALS = {
  REALTIME: 1000,      // 1 second
  FAST: 5000,          // 5 seconds  
  NORMAL: 30000,       // 30 seconds
  SLOW: 60000,         // 1 minute
  VERY_SLOW: 300000    // 5 minutes
};

// Interval display names
export const INTERVAL_LABELS = {
  1000: '1 second',
  5000: '5 seconds',
  15000: '15 seconds',
  30000: '30 seconds',
  60000: '1 minute',
  120000: '2 minutes',
  300000: '5 minutes'
};