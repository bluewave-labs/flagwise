import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { requestsService } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MetricCard, MetricCardContent, MetricCardHeader, MetricCardTitle } from '../components/ui/metric-card';
import { PageHeader } from '../components/ui/page-header';
import { Pagination } from '../components/ui/pagination';
import { EmptySearchResults, LoadingState } from '../components/ui/empty-state';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Loader2, 
  Search, 
  Filter,
  AlertTriangle, 
  Shield, 
  Eye,
  Clock,
  User,
  MapPin,
  Zap,
  AlertCircle
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';

const FlaggedPrompts = () => {
  const { isAdmin } = useAuth();
  const [flaggedRequests, setFlaggedRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Stats
  const [threatStats, setThreatStats] = useState({
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    total: 0
  });
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  
  // Filters
  const [filters, setFilters] = useState({
    search: '',
    risk_level: 'all',
    min_risk_score: '',
    time_range: '24h'
  });

  // Selected request for detail view
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [requestDetail, setRequestDetail] = useState(null);

  const fetchFlaggedRequests = async (page = currentPage) => {
    try {
      setLoading(true);
      setError(null);
      
      // Base parameters for flagged requests only
      const params = {
        page,
        page_size: pageSize,
        flagged: 'true', // Only get flagged requests
        ...Object.fromEntries(
          Object.entries(filters).filter(([key, value]) => {
            if (key === 'risk_level' && value !== 'all') {
              // Convert risk level to min_risk_score
              const riskLevelMap = {
                'critical': 70,
                'high': 40,
                'medium': 10,
                'low': 1
              };
              return false; // We'll handle this separately
            }
            return value !== '' && value !== 'all' && key !== 'time_range';
          })
        )
      };

      // Handle risk level filtering
      if (filters.risk_level !== 'all') {
        const riskLevelMap = {
          'critical': 70,
          'high': 40,
          'medium': 10,
          'low': 1
        };
        params.min_risk_score = riskLevelMap[filters.risk_level];
      }

      // Handle time range filtering
      if (filters.time_range !== 'all') {
        const now = new Date();
        const timeRanges = {
          '1h': new Date(now.getTime() - 60 * 60 * 1000),
          '24h': new Date(now.getTime() - 24 * 60 * 60 * 1000),
          '7d': new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
          '30d': new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        };
        if (timeRanges[filters.time_range]) {
          params.start_date = timeRanges[filters.time_range].toISOString();
        }
      }
      
      const response = await requestsService.getRequests(params);
      const data = response.data;
      
      setFlaggedRequests(data.items || []);
      setCurrentPage(data.page);
      setTotalPages(data.total_pages);
      setTotalCount(data.total_count);
      
      // Calculate threat stats
      calculateThreatStats(data.items || []);
      
    } catch (err) {
      setError('Failed to load flagged requests');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const calculateThreatStats = (requests) => {
    const stats = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      total: requests.length
    };

    requests.forEach(request => {
      const score = request.risk_score || 0;
      if (score >= 70) stats.critical++;
      else if (score >= 40) stats.high++;
      else if (score >= 10) stats.medium++;
      else stats.low++;
    });

    setThreatStats(stats);
  };

  const fetchRequestDetail = async (requestId) => {
    try {
      const response = await requestsService.getRequestById(requestId);
      setRequestDetail(response.data);
    } catch (err) {
      console.error('Failed to load request detail:', err);
    }
  };

  useEffect(() => {
    fetchFlaggedRequests(1);
  }, [filters, pageSize]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      risk_level: 'all',
      min_risk_score: '',
      time_range: '24h'
    });
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    fetchFlaggedRequests(newPage);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
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

  const getThreatType = (flagReason) => {
    if (!flagReason) return 'Unknown';
    
    if (flagReason.toLowerCase().includes('keyword')) return 'Sensitive Data';
    if (flagReason.toLowerCase().includes('email')) return 'Data Exposure';
    if (flagReason.toLowerCase().includes('injection')) return 'Prompt Injection';
    if (flagReason.toLowerCase().includes('model')) return 'Unauthorized Access';
    
    return 'Policy Violation';
  };

  const handleRequestClick = (request) => {
    setSelectedRequest(request);
    fetchRequestDetail(request.id);
  };

  if (loading && flaggedRequests.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Flagged Prompts</h1>
          <p className="text-13 text-gray-600">
            Security threats and policy violations detected by the system
          </p>
        </div>
        <LoadingState 
          title="Loading flagged requests..."
          description="Analyzing security threats and policy violations"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Flagged Prompts</h1>
          <p className="text-muted-foreground">
            Security threats and policy violations detected by the system
          </p>
        </div>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Flagged Prompts</h1>
        <p className="text-13 text-gray-600">
          Security threats and policy violations detected by the system
        </p>
      </div>

      {/* Threat Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard variant="blue">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-13 font-medium">Total Threats</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-gray-700">{threatStats.total.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Flagged requests detected
            </p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="red">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-13 font-medium">Critical</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-red-600">{threatStats.critical}</div>
            <p className="text-xs text-muted-foreground">
              Risk score ≥ 70
            </p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="orange">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-13 font-medium">High</CardTitle>
            <Zap className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-orange-600">{threatStats.high}</div>
            <p className="text-xs text-muted-foreground">
              Risk score 40-69
            </p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="yellow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-13 font-medium">Medium</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-yellow-600">{threatStats.medium}</div>
            <p className="text-xs text-muted-foreground">
              Risk score 10-39
            </p>
          </CardContent>
        </MetricCard>

        <MetricCard variant="blue">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-13 font-medium">Low</CardTitle>
            <Eye className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium text-blue-600">{threatStats.low}</div>
            <p className="text-xs text-muted-foreground">
              Risk score 1-9
            </p>
          </CardContent>
        </MetricCard>
      </div>

      {/* Filters */}
      <Card className="bg-muted/30 border-muted">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Threat Filters</CardTitle>
              <CardDescription>Filter and analyze security threats</CardDescription>
            </div>
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-13 font-medium">Search Threats</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search in prompts..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
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
              <label className="text-13 font-medium">Time Range</label>
              <Select value={filters.time_range} onValueChange={(value) => handleFilterChange('time_range', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Last 24h" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last hour</SelectItem>
                  <SelectItem value="24h">Last 24 hours</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                  <SelectItem value="all">All time</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Min Risk Score</label>
              <Input
                type="number"
                placeholder="0-100"
                min="0"
                max="100"
                value={filters.min_risk_score}
                onChange={(e) => handleFilterChange('min_risk_score', e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Flagged Requests Table */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">Security Threats Detected</h2>
            <p className="text-sm text-muted-foreground">
              {totalCount.toLocaleString()} flagged requests found
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-13 text-muted-foreground">Show:</span>
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
          {flaggedRequests.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Risk</TableHead>
                      <TableHead>Threat Type</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Provider</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Prompt Preview</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {flaggedRequests.map((request) => (
                      <TableRow key={request.id} className="hover:bg-muted/50">
                        <TableCell>
                          <div className="flex flex-col space-y-1">
                            <Badge variant={getRiskBadgeVariant(request.risk_score)}>
                              {request.risk_score}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {getRiskLevel(request.risk_score)}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <div className="flex flex-col">
                              <span className="font-medium text-13">
                                {getThreatType(request.flag_reason)}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {request.flag_reason}
                              </span>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <MapPin className="h-3 w-3 text-muted-foreground" />
                            <span className="text-13">{request.src_ip}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{request.provider}</Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-13 font-mono">{request.model}</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            <span className="text-13">{formatTimestamp(request.timestamp)}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-xs truncate text-13">
                            {request.prompt_preview || 'No preview available'}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => handleRequestClick(request)}
                              >
                                <Eye className="h-3 w-3 mr-1" />
                                View
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                              <DialogHeader>
                                <DialogTitle>Threat Analysis</DialogTitle>
                                <DialogDescription>
                                  Detailed security threat information
                                </DialogDescription>
                              </DialogHeader>
                              {requestDetail && (
                                <div className="space-y-4">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <h4 className="font-semibold mb-2">Risk Assessment</h4>
                                      <div className="space-y-2 text-13">
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Risk Score:</span>
                                          <Badge variant={getRiskBadgeVariant(requestDetail.risk_score)}>
                                            {requestDetail.risk_score}
                                          </Badge>
                                        </div>
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Threat Level:</span>
                                          <span className="text-13 font-medium">{getRiskLevel(requestDetail.risk_score)}</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Detection Rules:</span>
                                          <span className="text-13">{requestDetail.flag_reason}</span>
                                        </div>
                                      </div>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold mb-2">Request Details</h4>
                                      <div className="space-y-2 text-13">
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Source IP:</span>
                                          <span className="text-13 font-mono">{requestDetail.src_ip}</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Provider:</span>
                                          <Badge variant="secondary">{requestDetail.provider}</Badge>
                                        </div>
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Model:</span>
                                          <span className="text-13 font-mono">{requestDetail.model}</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                          <span className="text-13">Timestamp:</span>
                                          <span className="text-13">{formatTimestamp(requestDetail.timestamp)}</span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  {isAdmin() && requestDetail.prompt && (
                                    <div>
                                      <h4 className="font-semibold mb-2">Full Prompt (Admin View)</h4>
                                      <div className="bg-muted p-3 rounded-md">
                                        <pre className="whitespace-pre-wrap text-13">{requestDetail.prompt}</pre>
                                      </div>
                                    </div>
                                  )}
                                  
                                  {requestDetail.response && (
                                    <div>
                                      <h4 className="font-semibold mb-2">Model Response</h4>
                                      <div className="bg-muted p-3 rounded-md">
                                        <pre className="whitespace-pre-wrap text-13">{requestDetail.response}</pre>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </DialogContent>
                          </Dialog>
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
                itemName="threats"
                onPageChange={handlePageChange}
                onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
              />
            </>
          ) : (
            <EmptySearchResults
              icon={Shield}
              searchTerm={filters.search}
              itemType="security threats"
              onClearSearch={clearFilters}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default FlaggedPrompts;