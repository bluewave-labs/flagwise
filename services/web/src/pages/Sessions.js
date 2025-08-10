import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { sessionsService } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MetricCard, MetricCardContent, MetricCardHeader, MetricCardTitle } from '../components/ui/metric-card';
import { PageHeader } from '../components/ui/page-header';
import { Pagination } from '../components/ui/pagination';
import { EmptySearchResults, LoadingState } from '../components/ui/empty-state';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Loader2, 
  Search, 
  Filter, 
  AlertTriangle, 
  Clock,
  User,
  MapPin,
  Zap,
  AlertCircle,
  Eye,
  Activity,
  TrendingUp,
  Target,
  DollarSign,
  Users,
  Timer
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../components/ui/sheet';

const Sessions = () => {
  const { isAdmin } = useAuth();
  const { toast } = useToast();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Stats
  const [sessionStats, setSessionStats] = useState({
    totalSessions: 0,
    highRiskSessions: 0,
    avgDuration: 0,
    avgRequests: 0,
    mostActiveIP: null,
    longestSession: null
  });
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(10); // Start with smaller page size for better performance
  
  // Filters
  const [filters, setFilters] = useState({
    src_ip: '',
    risk_level: 'all',
    min_duration: '',
    max_duration: '',
    min_requests: '',
    max_requests: '',
    min_risk_score: ''
  });

  // Selected session for detail view
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionDetail, setSessionDetail] = useState(null);
  const [sessionDetailLoading, setSessionDetailLoading] = useState(false);
  const [showSessionDetail, setShowSessionDetail] = useState(false);

  const fetchSessions = async (page = currentPage) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page,
        page_size: pageSize,
        ...Object.fromEntries(
          Object.entries(filters).filter(([key, value]) => {
            if (key === 'risk_level' && value !== 'all') {
              return false; // We'll handle this separately
            }
            return value !== '' && value !== 'all';
          })
        )
      };

      // Handle risk level filtering
      if (filters.risk_level !== 'all') {
        params.risk_level = filters.risk_level;
      }
      
      const response = await sessionsService.getSessions(params);
      const data = response.data;
      
      setSessions(data.items || []);
      setCurrentPage(data.page);
      setTotalPages(data.total_pages);
      setTotalCount(data.total_count);
      
      // Calculate session stats
      calculateSessionStats(data.items || []);
      
    } catch (err) {
      console.error('Sessions loading error:', err);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to load sessions';
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out - the sessions query is taking too long. Try reducing the date range or adding more filters.';
      } else if (err.response?.status === 500) {
        errorMessage = 'Database error - the sessions query might be too complex. Try adding filters to narrow down the results.';
      } else if (err.response?.status === 404) {
        errorMessage = 'Sessions endpoint not found';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const calculateSessionStats = (sessionData) => {
    if (!sessionData || !Array.isArray(sessionData) || !sessionData.length) {
      setSessionStats({
        totalSessions: 0,
        highRiskSessions: 0,
        avgDuration: 0,
        avgRequests: 0,
        mostActiveIP: null,
        longestSession: null
      });
      return;
    }

    const stats = {
      totalSessions: sessionData.length,
      highRiskSessions: sessionData.filter(s => s.avg_risk_score >= 40).length,
      avgDuration: Math.round(sessionData.reduce((sum, s) => sum + s.duration_minutes, 0) / sessionData.length),
      avgRequests: Math.round(sessionData.reduce((sum, s) => sum + s.request_count, 0) / sessionData.length)
    };

    // Find most active IP
    const ipCounts = {};
    sessionData.forEach(s => {
      ipCounts[s.src_ip] = (ipCounts[s.src_ip] || 0) + s.request_count;
    });
    stats.mostActiveIP = Object.keys(ipCounts).reduce((a, b) => ipCounts[a] > ipCounts[b] ? a : b, null);

    // Find longest session
    stats.longestSession = sessionData.reduce((longest, current) => 
      current.duration_minutes > (longest?.duration_minutes || 0) ? current : longest, null);

    setSessionStats(stats);
  };

  const fetchSessionDetail = async (sessionId) => {
    try {
      setSessionDetailLoading(true);
      setSessionDetail(null);
      
      console.log('Fetching session detail for ID:', sessionId);
      const response = await sessionsService.getSessionById(sessionId);
      console.log('Session detail response:', response.data);
      
      setSessionDetail(response.data);
    } catch (err) {
      console.error('Failed to load session detail:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      
      const errorMessage = err.response?.data?.detail || err.message || "Failed to load session details. Please try again.";
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage,
      });
    } finally {
      setSessionDetailLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions(1);
  }, [filters, pageSize]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      src_ip: '',
      risk_level: 'all',
      min_duration: '',
      max_duration: '',
      min_requests: '',
      max_requests: '',
      min_risk_score: ''
    });
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    fetchSessions(newPage);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (minutes) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  const getRiskBadgeVariant = (riskScore) => {
    if (riskScore >= 70) return 'destructive';
    if (riskScore >= 40) return 'secondary';
    if (riskScore >= 10) return 'outline';
    return 'default';
  };

  const getRiskLevel = (riskScore) => {
    if (riskScore >= 70) return 'Critical';
    if (riskScore >= 40) return 'High';
    if (riskScore >= 10) return 'Medium';
    return 'Low';
  };

  const getUnusualPatternsDisplay = (patterns) => {
    if (!patterns || !Array.isArray(patterns) || patterns.length === 0) return 'None';
    return patterns.slice(0, 2).join(', ') + (patterns.length > 2 ? '...' : '');
  };

  const handleSessionClick = (session) => {
    console.log('Session clicked:', session);
    console.log('Session ID:', session.id);
    
    setSelectedSession(session);
    fetchSessionDetail(session.id);
    setShowSessionDetail(true);
  };

  if (loading && sessions.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">User Sessions</h1>
          <p className="text-13 text-gray-600">
            Analyze user activity grouped by IP and time windows (30-min inactivity, 1-hour max)
          </p>
        </div>
        <LoadingState 
          title="Loading user sessions..."
          description="Analyzing user activity patterns and session data. This may take a few moments for large datasets."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">User Sessions</h1>
          <p className="text-13 text-gray-600">
            Analyze user activity grouped by IP and time windows
          </p>
        </div>
        <div className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          
          {error.includes('timed out') || error.includes('Database error') ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Performance Tip:</strong> Sessions are computed from large datasets. To improve loading speed:
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Use the Source IP filter to focus on specific users</li>
                  <li>Reduce the page size to 10 or 25 items</li>
                  <li>Filter by Risk Level to see only high-priority sessions</li>
                </ul>
              </AlertDescription>
            </Alert>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">User Sessions</h1>
        <p className="text-13 text-gray-600">
          Analyze user activity grouped by IP and time windows (30-min inactivity, 1-hour max)
        </p>
      </div>

      {/* Session Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <MetricCard variant="blue">
          <MetricCardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <MetricCardTitle className="text-sm font-medium">Total Sessions</MetricCardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </MetricCardHeader>
          <MetricCardContent>
            <div className="text-xl font-medium text-gray-700">{sessionStats.totalSessions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Active user sessions
            </p>
          </MetricCardContent>
        </MetricCard>

        <MetricCard variant="red">
          <MetricCardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <MetricCardTitle className="text-sm font-medium">High Risk</MetricCardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </MetricCardHeader>
          <MetricCardContent>
            <div className="text-xl font-medium text-red-600">{sessionStats.highRiskSessions}</div>
            <p className="text-xs text-muted-foreground">
              Risk score ≥ 40
            </p>
          </MetricCardContent>
        </MetricCard>

        <MetricCard variant="blue">
          <MetricCardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <MetricCardTitle className="text-sm font-medium">Avg Duration</MetricCardTitle>
            <Timer className="h-4 w-4 text-blue-500" />
          </MetricCardHeader>
          <MetricCardContent>
            <div className="text-xl font-medium text-blue-600">{formatDuration(sessionStats.avgDuration)}</div>
            <p className="text-xs text-muted-foreground">
              Per session
            </p>
          </MetricCardContent>
        </MetricCard>

        <MetricCard variant="green">
          <MetricCardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <MetricCardTitle className="text-sm font-medium">Avg Requests</MetricCardTitle>
            <Activity className="h-4 w-4 text-green-500" />
          </MetricCardHeader>
          <MetricCardContent>
            <div className="text-xl font-medium text-green-600">{sessionStats.avgRequests}</div>
            <p className="text-xs text-muted-foreground">
              Per session
            </p>
          </MetricCardContent>
        </MetricCard>

        <MetricCard variant="purple">
          <MetricCardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <MetricCardTitle className="text-sm font-medium">Most Active IP</MetricCardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </MetricCardHeader>
          <MetricCardContent>
            <div className="text-xl font-medium text-purple-600">
              {sessionStats.mostActiveIP || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              By request volume
            </p>
          </MetricCardContent>
        </MetricCard>

        <MetricCard variant="orange">
          <MetricCardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <MetricCardTitle className="text-sm font-medium">Longest Session</MetricCardTitle>
            <Clock className="h-4 w-4 text-orange-500" />
          </MetricCardHeader>
          <MetricCardContent>
            <div className="text-xl font-medium text-orange-600">
              {sessionStats.longestSession ? formatDuration(sessionStats.longestSession.duration_minutes) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Maximum duration
            </p>
          </MetricCardContent>
        </MetricCard>
      </div>

      {/* Filters */}
      <Card className="bg-muted/30 border-muted">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Session Filters</CardTitle>
              <CardDescription>Filter and analyze user sessions</CardDescription>
            </div>
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-13 font-medium">Source IP</label>
              <div className="relative">
                <MapPin className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="192.168.1.100"
                  value={filters.src_ip}
                  onChange={(e) => handleFilterChange('src_ip', e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            
            <div>
              <label className="text-13 font-medium">Risk Level</label>
              <Select value={filters.risk_level} onValueChange={(value) => handleFilterChange('risk_level', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="All levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All levels</SelectItem>
                  <SelectItem value="critical">Critical (≥70)</SelectItem>
                  <SelectItem value="high">High (40-69)</SelectItem>
                  <SelectItem value="medium">Medium (10-39)</SelectItem>
                  <SelectItem value="low">Low (1-9)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Duration Range (minutes)</label>
              <div className="grid grid-cols-2 gap-1">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.min_duration}
                  onChange={(e) => handleFilterChange('min_duration', e.target.value)}
                />
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.max_duration}
                  onChange={(e) => handleFilterChange('max_duration', e.target.value)}
                />
              </div>
            </div>
            
            <div>
              <label className="text-13 font-medium">Request Count</label>
              <div className="grid grid-cols-2 gap-1">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.min_requests}
                  onChange={(e) => handleFilterChange('min_requests', e.target.value)}
                />
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.max_requests}
                  onChange={(e) => handleFilterChange('max_requests', e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sessions Table */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">User Sessions</h2>
            <p className="text-sm text-muted-foreground">
              {totalCount.toLocaleString()} sessions found
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Show:</span>
            <Select value={pageSize.toString()} onValueChange={(value) => setPageSize(parseInt(value))}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div>
          {sessions.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Source IP</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Requests</TableHead>
                      <TableHead>Risk Score</TableHead>
                      <TableHead>Flagged</TableHead>
                      <TableHead>Top Providers</TableHead>
                      <TableHead>Unusual Patterns</TableHead>
                      <TableHead>Started</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sessions.map((session) => (
                      <TableRow key={session.id} className="hover:bg-muted/50">
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <MapPin className="h-3 w-3 text-muted-foreground" />
                            <span className="font-mono text-13">{session.src_ip}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            <Timer className="h-3 w-3 text-muted-foreground" />
                            <span className="text-13">{formatDuration(session.duration_minutes)}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            <Activity className="h-3 w-3 text-muted-foreground" />
                            <span className="text-13 font-medium">{session.request_count}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Badge variant={getRiskBadgeVariant(session.avg_risk_score)} className="px-2 py-0.5 text-xs min-w-0 w-fit">
                              {session.avg_risk_score}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {getRiskLevel(session.avg_risk_score)}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            {session.flagged_count > 0 ? (
                              <>
                                <AlertTriangle className="h-3 w-3 text-red-500" />
                                <span className="text-13 font-medium text-red-600">{session.flagged_count}</span>
                              </>
                            ) : (
                              <span className="text-13 text-muted-foreground">0</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {(session.top_providers || []).slice(0, 2).map(provider => (
                              <Badge key={provider} variant="outline" className="text-xs">
                                {provider}
                              </Badge>
                            ))}
                            {(session.top_providers || []).length > 2 && (
                              <span className="text-xs text-muted-foreground">+{(session.top_providers || []).length - 2}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-xs">
                            <span className="text-xs text-muted-foreground">
                              {getUnusualPatternsDisplay(session.unusual_patterns)}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs">{formatTimestamp(session.start_time)}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleSessionClick(session)}
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              {/* Pagination */}
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalCount={totalCount}
                pageSize={pageSize}
                itemName="sessions"
                onPageChange={handlePageChange}
                onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
              />
            </>
          ) : (
            <EmptySearchResults
              icon={Users}
              searchTerm={Object.values(filters).some(v => v && v !== 'all') ? 'filtered' : ''}
              itemType="user sessions"
              onClearSearch={clearFilters}
            />
          )}
        </div>
      </div>

      {/* Session Detail Sheet */}
      <Sheet open={showSessionDetail} onOpenChange={setShowSessionDetail}>
        <SheetContent className="w-[75%] sm:w-[900px] max-w-none overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Session Details</SheetTitle>
            <SheetDescription>
              Detailed analysis for session from {selectedSession?.src_ip}
            </SheetDescription>
          </SheetHeader>
          
          <div className="border-b border-gray-200 mb-6"></div>
          
          {sessionDetailLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="flex flex-col items-center space-y-4">
                <Loader2 className="h-8 w-8 animate-spin" />
                <p className="text-muted-foreground">Loading session details...</p>
              </div>
            </div>
          ) : sessionDetail ? (
            <div className="space-y-6 mt-6">
              {/* Session Overview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Session Info</h4>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-13">
                      <span>Duration:</span>
                      <span className="font-medium">{formatDuration(sessionDetail.duration_minutes)}</span>
                    </div>
                    <div className="flex items-center justify-between text-13">
                      <span>Requests:</span>
                      <span className="font-medium">{sessionDetail.request_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-13">
                      <span>Started:</span>
                      <span className="text-xs">{formatTimestamp(sessionDetail.start_time)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Risk Assessment</h4>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-13">
                      <span>Avg Risk:</span>
                      <Badge variant={getRiskBadgeVariant(sessionDetail.avg_risk_score)}>
                        {sessionDetail.avg_risk_score}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-13">
                      <span>Flagged:</span>
                      <span className="font-medium text-red-600">{sessionDetail.flagged_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-13">
                      <span>Level:</span>
                      <span className="font-medium">{getRiskLevel(sessionDetail.avg_risk_score)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Usage Stats</h4>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-13">
                      <span>Providers:</span>
                      <span className="text-xs">{sessionDetail.top_providers.length}</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Patterns</h4>
                  <div className="space-y-1">
                    {sessionDetail.unusual_patterns.length > 0 ? (
                      sessionDetail.unusual_patterns.map((pattern, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs mb-1">
                          {pattern}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">No unusual patterns</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Risk Breakdown Chart */}
              <div>
                <h4 className="font-semibold mb-3">Risk Breakdown</h4>
                <div className="grid grid-cols-4 gap-2">
                  <div className="bg-red-50 border border-red-200 rounded p-2 text-center">
                    <div className="text-lg font-bold text-red-600">{sessionDetail.risk_breakdown.critical}</div>
                    <div className="text-xs text-red-500">Critical</div>
                  </div>
                  <div className="bg-orange-50 border border-orange-200 rounded p-2 text-center">
                    <div className="text-lg font-bold text-orange-600">{sessionDetail.risk_breakdown.high}</div>
                    <div className="text-xs text-orange-500">High</div>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-center">
                    <div className="text-lg font-bold text-yellow-600">{sessionDetail.risk_breakdown.medium}</div>
                    <div className="text-xs text-yellow-500">Medium</div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded p-2 text-center">
                    <div className="text-lg font-bold text-blue-600">{sessionDetail.risk_breakdown.low}</div>
                    <div className="text-xs text-blue-500">Low</div>
                  </div>
                </div>
              </div>

              {/* Request Timeline */}
              <div>
                <h4 className="font-semibold mb-3">Request Timeline ({sessionDetail.requests.length} requests)</h4>
                <div className="max-h-60 overflow-y-auto space-y-2">
                  {sessionDetail.requests.map((request, idx) => (
                    <div key={request.id} className="flex items-center space-x-3 p-2 border rounded text-13">
                      <span className="text-xs text-muted-foreground w-16">
                        {new Date(request.timestamp).toLocaleTimeString()}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {request.provider}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {request.model}
                      </Badge>
                      <Badge variant={getRiskBadgeVariant(request.risk_score)} className="text-xs">
                        {request.risk_score}
                      </Badge>
                      {request.is_flagged && (
                        <AlertTriangle className="h-3 w-3 text-red-500" />
                      )}
                      <div className="flex-1 truncate text-xs text-muted-foreground">
                        {request.prompt_preview}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No session details available</p>
                <p className="text-sm text-muted-foreground">Please try clicking the Details button again</p>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default Sessions;