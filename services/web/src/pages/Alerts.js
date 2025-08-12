import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { alertsService, rulesService } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MetricCard, MetricCardContent, MetricCardHeader, MetricCardTitle } from '../components/ui/metric-card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Checkbox } from '../components/ui/checkbox';
import { 
  Loader2, 
  Bell, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Eye,
  Search,
  Filter,
  Settings,
  Plus,
  Edit,
  Trash2,
  AlertCircle,
  Shield,
  Activity,
  Zap,
  Target,
  Check,
  X,
  Archive,
  Play,
  Pause,
  MoreHorizontal,
  MapPin,
  Timer,
  User,
  Mail,
  Slack as SlackIcon,
  Smartphone
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../components/ui/sheet';

const Alerts = () => {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState({
    total_alerts: 0,
    new_alerts: 0,
    acknowledged_alerts: 0,
    resolved_alerts: 0,
    critical_alerts: 0,
    high_alerts: 0
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAlerts, setSelectedAlerts] = useState(new Set());
  const [isRunning, setIsRunning] = useState(true);
  
  // Filter states
  const [filters, setFilters] = useState({
    severity: 'all',
    status: 'all',
    alert_type: '',
    source_type: 'all',
    search: ''
  });
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(200);
  
  // Alert Rules Configuration
  const [showRulesConfig, setShowRulesConfig] = useState(false);
  const [rules, setRules] = useState([]);
  const [detectionRules, setDetectionRules] = useState([]);
  const [editingRule, setEditingRule] = useState(null);
  
  const [ruleForm, setRuleForm] = useState({
    name: '',
    description: '',
    rule_type: 'threshold',
    severity: 'medium',
    is_active: true,
    threshold_config: {
      risk_score: 80,
      requests_per_minute: 100
    },
    detection_rule_ids: [],
    notifications: {
      slack: true,
      email: true,
      in_app: true
    }
  });
  
  // Refs for scroll management
  const alertsContainerRef = useRef(null);
  const intervalRef = useRef(null);
  const isUserScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef(null);

  // Track user scrolling behavior
  const handleScroll = () => {
    if (alertsContainerRef.current) {
      const { scrollTop } = alertsContainerRef.current;
      isUserScrollingRef.current = scrollTop > 50;
      
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      scrollTimeoutRef.current = setTimeout(() => {
        if (alertsContainerRef.current && alertsContainerRef.current.scrollTop <= 50) {
          isUserScrollingRef.current = false;
        }
      }, 3000);
    }
  };

  const fetchAlerts = async (page = currentPage, forceUpdate = false) => {
    try {
      // Allow API calls when filters are applied or when forced, even if not running
      const hasActiveFilters = Object.entries(filters).some(([key, value]) => value !== '' && value !== 'all');
      
      if (!isRunning && !hasActiveFilters && !forceUpdate) return;
      
      setLoading(alerts.length === 0);
      setError(null);
      
      const params = {
        page: 1, // Always get fresh data for live feed
        page_size: pageSize,
        ...Object.fromEntries(
          Object.entries(filters).filter(([key, value]) => value !== '' && value !== 'all')
        )
      };
      
      const [alertsResponse, statsResponse] = await Promise.all([
        alertsService.getAlerts(params),
        alertsService.getStats()
      ]);
      
      const newAlerts = alertsResponse.data.items || [];
      
      if (hasActiveFilters) {
        // When filtering, replace all alerts with filtered results
        setAlerts(newAlerts);
      } else {
        // When not filtering, combine new and existing alerts for live feed
        setAlerts(prevAlerts => {
          // Combine new and existing alerts
          const combinedAlerts = [...newAlerts, ...prevAlerts];
          
          // Remove duplicates based on ID
          const uniqueAlerts = combinedAlerts.filter((alert, index, self) => 
            index === self.findIndex(t => t.id === alert.id)
          );
          
          // Sort by timestamp (newest first)
          uniqueAlerts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
          
          // Limit to pageSize items
          return uniqueAlerts.slice(0, pageSize);
        });
      }
      
      setAlertStats(statsResponse.data);
      setTotalCount(alertsResponse.data.total_count || 0);
      setTotalPages(alertsResponse.data.total_pages || 1);
      
    } catch (err) {
      setError('Failed to load alerts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetectionRules = async () => {
    try {
      const response = await rulesService.getRules();
      setDetectionRules(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Failed to load detection rules:', err);
      setDetectionRules([]);
    }
  };

  // Auto-scroll to top for new alerts (only if user hasn't scrolled)
  useEffect(() => {
    if (!isUserScrollingRef.current && alertsContainerRef.current && alerts.length > 0) {
      alertsContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [alerts]);

  // Start/stop polling
  useEffect(() => {
    if (isRunning) {
      fetchAlerts();
      intervalRef.current = setInterval(fetchAlerts, 2000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, filters]);

  useEffect(() => {
    fetchDetectionRules();
  }, []);

  // Trigger fetchAlerts when filters change
  useEffect(() => {
    if (isRunning) {
      fetchAlerts();
    }
  }, [filters]);

  const handleAlertAction = async (alertId, action) => {
    try {
      await alertsService.updateAlert(alertId, { status: action });
      fetchAlerts();
    } catch (err) {
      setError(`Failed to ${action} alert`);
      console.error(err);
    }
  };

  const handleBulkOperation = async (operation) => {
    if (selectedAlerts.size === 0) return;
    
    try {
      await alertsService.bulkOperation({
        alert_ids: Array.from(selectedAlerts),
        operation,
        user: user?.username
      });
      setSelectedAlerts(new Set());
      fetchAlerts();
    } catch (err) {
      setError(`Failed to ${operation} alerts`);
      console.error(err);
    }
  };

  const toggleAlertSelection = (alertId) => {
    const newSelection = new Set(selectedAlerts);
    if (newSelection.has(alertId)) {
      newSelection.delete(alertId);
    } else {
      newSelection.add(alertId);
    }
    setSelectedAlerts(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedAlerts.size === alerts.length) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set(alerts.map(alert => alert.id)));
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'high': return <Zap className="h-4 w-4 text-orange-500" />;
      case 'medium': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'low': return <Eye className="h-4 w-4 text-blue-500" />;
      default: return <Shield className="h-4 w-4" />;
    }
  };

  const getSeverityBadgeVariant = (severity) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'secondary';
      case 'medium': return 'outline';
      case 'low': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'new': return <Bell className="h-4 w-4 text-blue-500" />;
      case 'acknowledged': return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'resolved': return <CheckCircle className="h-4 w-4 text-green-500" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case 'new': return 'default';
      case 'acknowledged': return 'secondary';
      case 'resolved': return 'outline';
      default: return 'default';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    const alertTime = new Date(timestamp);
    const diffMs = now - alertTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getSourceTypeIcon = (sourceType) => {
    switch (sourceType) {
      case 'detection_rule': return <Shield className="h-3 w-3" />;
      case 'threshold': return <Target className="h-3 w-3" />;
      case 'system': return <Settings className="h-3 w-3" />;
      default: return <Activity className="h-3 w-3" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Alerts</h1>
          <p className="text-13 text-gray-600">
            Real-time security alerts with status management and rule configuration
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => setShowRulesConfig(true)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Alert Rules
          </Button>
          
          <Button
            variant={isRunning ? "outline" : "default"}
            onClick={() => setIsRunning(!isRunning)}
            className="flex items-center space-x-2"
          >
            {isRunning ? (
              <><Pause className="h-4 w-4" /> Pause Feed</>
            ) : (
              <><Play className="h-4 w-4" /> Start Feed</>
            )}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Alert Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <MetricCard variant="blue">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-gray-700">{alertStats.total_alerts.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="blue">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New</CardTitle>
            <Bell className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-blue-600">{alertStats.new_alerts}</div>
            <p className="text-xs text-muted-foreground">Unacknowledged</p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="yellow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Acknowledged</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-yellow-600">{alertStats.acknowledged_alerts}</div>
            <p className="text-xs text-muted-foreground">In progress</p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="green">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-green-600">{alertStats.resolved_alerts}</div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="red">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-red-600">{alertStats.critical_alerts}</div>
            <p className="text-xs text-muted-foreground">High priority</p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="orange">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Severity</CardTitle>
            <Zap className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-orange-600">{alertStats.high_alerts}</div>
            <p className="text-xs text-muted-foreground">Needs attention</p>
          </CardContent>
        </MetricCard>
      </div>


      {/* Filters */}
      <Card className="bg-muted/30 border-muted">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Alert Filters</CardTitle>
              <CardDescription>Filter and search alerts</CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`h-2 w-2 rounded-full ${isRunning ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium">
                {isRunning ? 'Live' : 'Paused'} • {alerts.length} alerts
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <div>
              <label className="text-13 font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search alerts..."
                  value={filters.search}
                  onChange={(e) => setFilters({...filters, search: e.target.value})}
                  className="pl-8"
                />
              </div>
            </div>
            
            <div>
              <label className="text-13 font-medium">Severity</label>
              <Select value={filters.severity} onValueChange={(value) => setFilters({...filters, severity: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Status</label>
              <Select value={filters.status} onValueChange={(value) => setFilters({...filters, status: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="acknowledged">Acknowledged</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Source</label>
              <Select value={filters.source_type} onValueChange={(value) => setFilters({...filters, source_type: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sources</SelectItem>
                  <SelectItem value="detection_rule">Detection Rules</SelectItem>
                  <SelectItem value="threshold">Thresholds</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Alert Type</label>
              <Input
                placeholder="e.g., Security Threat"
                value={filters.alert_type}
                onChange={(e) => setFilters({...filters, alert_type: e.target.value})}
              />
            </div>
            
            <div>
              <label className="text-13 font-medium">Actions</label>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => setFilters({ severity: 'all', status: 'all', alert_type: '', source_type: 'all', search: '' })}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedAlerts.size > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {selectedAlerts.size} alert(s) selected
              </span>
              <div className="flex items-center space-x-2">
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkOperation('acknowledge')}
                >
                  <Check className="h-4 w-4 mr-1" />
                  Acknowledge
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkOperation('resolve')}
                >
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Resolve
                </Button>
                <Button 
                  size="sm" 
                  variant="destructive"
                  onClick={() => handleBulkOperation('archive')}
                >
                  <Archive className="h-4 w-4 mr-1" />
                  Archive
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts Timeline */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              Alert Timeline
            </h2>
            <p className="text-sm text-muted-foreground">
              Real-time feed of security alerts (auto-refreshes every 2 seconds)
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox 
              checked={selectedAlerts.size === alerts.length && alerts.length > 0}
              onCheckedChange={toggleSelectAll}
            />
            <span className="text-sm text-muted-foreground">Select All</span>
          </div>
        </div>
        
        <div>
          {loading && alerts.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center space-y-4">
                <Loader2 className="h-8 w-8 animate-spin" />
                <p className="text-muted-foreground">Loading alerts...</p>
              </div>
            </div>
          ) : (
            <div 
              ref={alertsContainerRef}
              onScroll={handleScroll}
              className="max-h-[600px] overflow-y-auto space-y-0 pr-2"
            >
              {alerts.length > 0 ? (
                <div className="relative">
                  {/* Timeline vertical line */}
                  <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border"></div>
                  
                  {alerts.map((alert, index) => (
                    <div key={alert.id} className="relative flex items-start space-x-4 pb-6">
                      {/* Timeline node */}
                      <div className="flex flex-col items-center">
                        <div className="text-xs text-muted-foreground mb-1 w-16 text-center">
                          {getTimeAgo(alert.created_at)}
                        </div>
                        <div className={`h-6 w-6 rounded-full border-2 bg-background flex items-center justify-center ${alert.severity === 'critical' ? 'border-red-500 text-red-500' : alert.severity === 'high' ? 'border-orange-500 text-orange-500' : alert.severity === 'medium' ? 'border-yellow-500 text-yellow-500' : 'border-blue-500 text-blue-500'}`}>
                          {getSeverityIcon(alert.severity)}
                        </div>
                      </div>
                      
                      {/* Timeline content */}
                      <div className="flex-1 min-w-0 pb-2">
                        <div className={`bg-card border rounded-lg p-4 transition-colors ${selectedAlerts.has(alert.id) ? 'bg-accent/50' : 'hover:bg-accent/20'}`}>
                          <div className="flex items-start justify-between space-x-2">
                            <div className="flex items-start space-x-3 flex-1 min-w-0">
                              <Checkbox 
                                checked={selectedAlerts.has(alert.id)}
                                onCheckedChange={() => toggleAlertSelection(alert.id)}
                                className="mt-1"
                              />
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-2 mb-2">
                                  <h4 className="font-semibold text-sm">{alert.title}</h4>
                                  <Badge variant={getSeverityBadgeVariant(alert.severity)}>
                                    {alert.severity}
                                  </Badge>
                                  <Badge variant={getStatusBadgeVariant(alert.status)}>
                                    {alert.status}
                                  </Badge>
                                </div>
                                
                                <p className="text-sm text-muted-foreground mb-3">
                                  {alert.description}
                                </p>
                                
                                <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                                  <div className="flex items-center space-x-1">
                                    <Timer className="h-3 w-3" />
                                    <span>{formatTimestamp(alert.created_at)}</span>
                                  </div>
                                  
                                  <div className="flex items-center space-x-1">
                                    {getSourceTypeIcon(alert.source_type)}
                                    <span className="capitalize">{alert.source_type.replace('_', ' ')}</span>
                                  </div>
                                  
                                  <div className="flex items-center space-x-1">
                                    <Target className="h-3 w-3" />
                                    <span>{alert.alert_type}</span>
                                  </div>
                                  
                                  {alert.metadata?.src_ip && (
                                    <div className="flex items-center space-x-1">
                                      <MapPin className="h-3 w-3" />
                                      <span className="font-mono">{alert.metadata.src_ip}</span>
                                    </div>
                                  )}
                                  
                                  {alert.acknowledged_by && (
                                    <div className="flex items-center space-x-1">
                                      <User className="h-3 w-3" />
                                      <span>{alert.acknowledged_by}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                {alert.status === 'new' && (
                                  <DropdownMenuItem onClick={() => handleAlertAction(alert.id, 'acknowledged')}>
                                    <Check className="h-4 w-4 mr-2" />
                                    Acknowledge
                                  </DropdownMenuItem>
                                )}
                                {alert.status !== 'resolved' && (
                                  <DropdownMenuItem onClick={() => handleAlertAction(alert.id, 'resolved')}>
                                    <CheckCircle className="h-4 w-4 mr-2" />
                                    Resolve
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="text-red-600">
                                  <Archive className="h-4 w-4 mr-2" />
                                  Archive
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">
                    {isRunning ? 'No alerts found' : 'Alert feed paused'}
                  </h3>
                  <p className="text-muted-foreground">
                    {isRunning 
                      ? (Object.values(filters).some(v => v && v !== 'all' && v !== '')
                          ? 'Try adjusting your filters to see more results.'
                          : 'Great news! No security alerts have been detected recently.')
                      : 'Click "Start Feed" to begin monitoring alerts.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Alert Rules Sheet */}
      <AlertRulesSheet 
        showRulesConfig={showRulesConfig} 
        setShowRulesConfig={setShowRulesConfig} 
        detectionRules={detectionRules} 
      />
    </div>
  );
};

// AlertRulesSheet Component
const AlertRulesSheet = ({ showRulesConfig, setShowRulesConfig, detectionRules }) => {
  return (
    <Sheet open={showRulesConfig} onOpenChange={setShowRulesConfig}>
      <SheetContent side="right" className="w-full sm:max-w-4xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Alert Rules Configuration</SheetTitle>
          <SheetDescription>
            Configure threshold-based and rule-based alert triggers
          </SheetDescription>
        </SheetHeader>
        
        <div className="border-t my-6"></div>
        
        <div className="space-y-6">
          <div className="flex justify-end">
            <Button size="sm" variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add Rule
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-semibold">Threshold-Based Rules</h4>
              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">High Risk Score Alert</span>
                  <Switch defaultChecked />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-muted-foreground">Risk Score Threshold</label>
                    <Input type="number" defaultValue="80" min="0" max="100" className="h-8" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Severity</label>
                    <Select defaultValue="high">
                      <SelectTrigger className="h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              
              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Request Rate Limit</span>
                  <Switch defaultChecked />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-muted-foreground">Requests/Minute</label>
                    <Input type="number" defaultValue="100" min="1" className="h-8" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Severity</label>
                    <Select defaultValue="medium">
                      <SelectTrigger className="h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold">Detection Rule-Based Alerts</h4>
              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Security Rule Matches</span>
                  <Switch defaultChecked />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-2 block">Monitored Rules</label>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {(detectionRules || []).filter(rule => rule.category === 'security').slice(0, 5).map(rule => (
                      <div key={rule.id} className="flex items-center space-x-2">
                        <Checkbox defaultChecked className="h-3 w-3" />
                        <span className="text-xs">{rule.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="border rounded-lg p-4 space-y-3">
                <h5 className="text-sm font-medium">Notification Settings</h5>
                <div className="grid grid-cols-3 gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox defaultChecked />
                    <SlackIcon className="h-4 w-4" />
                    <span className="text-xs">Slack</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox defaultChecked />
                    <Mail className="h-4 w-4" />
                    <span className="text-xs">Email</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox defaultChecked />
                    <Smartphone className="h-4 w-4" />
                    <span className="text-xs">In-App</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default Alerts;