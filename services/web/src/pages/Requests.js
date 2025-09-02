import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { requestsService } from '../services/api';
import { useDebounce } from '../hooks/useDebounce';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { PageHeader } from '../components/ui/page-header';
import { Pagination } from '../components/ui/pagination';
import { LoadingState } from '../components/ui/empty-state';
import { SkeletonTable } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { AutoRefreshToggle } from '../components/ui/auto-refresh-toggle';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { Loader2, Search, Filter, AlertCircle, Eye } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../components/ui/sheet';

const Requests = () => {
  const { isAdmin } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  
  // Filters
  const [filters, setFilters] = useState({
    search: '',
    flagged: 'all',
    provider: '',
    model: '',
    min_risk_score: ''
  });

  // Debounce search term to avoid excessive API calls
  const debouncedSearch = useDebounce(filters.search, 300);

  // Reset page when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch]);

  // Selected request for detail view
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [requestDetail, setRequestDetail] = useState(null);
  const [showRequestDetail, setShowRequestDetail] = useState(false);

  const fetchRequests = async (page = currentPage) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page,
        page_size: pageSize,
        ...Object.fromEntries(
          Object.entries({
            ...filters,
            search: debouncedSearch
          }).filter(([_, value]) => value !== '' && value !== 'all')
        )
      };
      
      const response = await requestsService.getRequests(params);
      const data = response.data;
      
      setRequests(data.items);
      setCurrentPage(data.page);
      setTotalPages(data.total_pages);
      setTotalCount(data.total_count);
      
    } catch (err) {
      setError('Failed to load requests');
      console.error(err);
      
    } finally {
      setLoading(false);
    }
  };

  const fetchRequestDetail = async (requestId) => {
    try {
      const response = await requestsService.getRequestById(requestId);
      setRequestDetail(response.data);
    } catch (err) {
      console.error('Failed to load request detail:', err);
    }
  };

  // Auto-refresh setup
  const autoRefresh = useAutoRefresh({
    fetchFunction: () => fetchRequests(currentPage),
    defaultInterval: 15000, // 15 seconds - faster for live request monitoring
    defaultEnabled: false,
    dependencies: [filters, pageSize, currentPage]
  });

  useEffect(() => {
    fetchRequests(1);
  }, [filters, pageSize]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      flagged: 'all',
      provider: '',
      model: '',
      min_risk_score: ''
    });
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    fetchRequests(newPage);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getRiskBadgeVariant = (riskScore) => {
    if (riskScore >= 70) return 'destructive';
    if (riskScore >= 40) return 'warning';
    if (riskScore >= 10) return 'secondary';
    return 'default';
  };

  const handleRequestClick = (request) => {
    setSelectedRequest(request);
    fetchRequestDetail(request.id);
    setShowRequestDetail(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">LLM Requests</h1>
          <p className="text-13 text-gray-600">
            Monitor and analyze all intercepted LLM API requests
          </p>
        </div>
        
        <AutoRefreshToggle
          isEnabled={autoRefresh.isEnabled}
          interval={autoRefresh.interval}
          onToggle={autoRefresh.toggleAutoRefresh}
          onIntervalChange={autoRefresh.updateInterval}
          onManualRefresh={autoRefresh.manualRefresh}
          lastRefresh={autoRefresh.lastRefresh}
          compact={true}
        />
      </div>

      {/* Filters */}
      <Card className="bg-muted/30 border-muted">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Filters</CardTitle>
              <CardDescription>Filter and search through requests</CardDescription>
            </div>
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-13 font-medium">Search</label>
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
              <label className="text-13 font-medium">Status</label>
              <Select value={filters.flagged} onValueChange={(value) => handleFilterChange('flagged', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="All requests" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All requests</SelectItem>
                  <SelectItem value="true">Flagged only</SelectItem>
                  <SelectItem value="false">Clean only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Provider</label>
              <Input
                placeholder="e.g. openai, anthropic"
                value={filters.provider}
                onChange={(e) => handleFilterChange('provider', e.target.value)}
              />
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

      {/* Results */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">
              Requests ({totalCount.toLocaleString()})
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm">Page size:</span>
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
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {loading ? (
            <SkeletonTable rows={10} columns={8} />
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Source IP</TableHead>
                      <TableHead>Provider</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead>Prompt Preview</TableHead>
                      <TableHead>Risk Score</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {requests.map((request) => (
                      <TableRow key={request.id}>
                        <TableCell className="text-xs">
                          {formatTimestamp(request.timestamp)}
                        </TableCell>
                        <TableCell className="font-mono text-13">
                          {request.src_ip}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{request.provider}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{request.model}</Badge>
                        </TableCell>
                        <TableCell className="max-w-md">
                          <div className="truncate text-13">
                            {isAdmin() ? request.prompt || request.prompt_preview : request.prompt_preview}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getRiskBadgeVariant(request.risk_score)}>
                            {request.risk_score}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {request.is_flagged ? (
                            <Badge variant="destructive">Flagged</Badge>
                          ) : (
                            <Badge variant="default">Clean</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleRequestClick(request)}
                          >
                            <Eye className="h-4 w-4" />
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
                itemName="requests"
                onPageChange={handlePageChange}
                onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
              />
            </>
          )}
        </div>
      </div>

      {/* Request Detail Sheet */}
      <Sheet open={showRequestDetail} onOpenChange={setShowRequestDetail}>
        <SheetContent className="w-[75%] sm:w-[900px] max-w-none overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Request Details</SheetTitle>
            <SheetDescription>
              Full details for request {selectedRequest?.id}
            </SheetDescription>
          </SheetHeader>
          
          <div className="border-b border-gray-200 mb-6"></div>
          
          {requestDetail && (
            <div className="space-y-6 mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Basic Info</h4>
                  <div className="space-y-2 text-13">
                    <p className="text-13"><strong>ID:</strong> {requestDetail.id}</p>
                    <p className="text-13"><strong>Timestamp:</strong> {formatTimestamp(requestDetail.timestamp)}</p>
                    <p className="text-13"><strong>Source IP:</strong> {requestDetail.src_ip}</p>
                    <p className="text-13"><strong>Provider:</strong> {requestDetail.provider}</p>
                    <p className="text-13"><strong>Model:</strong> {requestDetail.model}</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Risk Assessment</h4>
                  <div className="space-y-2 text-13">
                    <p className="text-13"><strong>Risk Score:</strong> <Badge variant={getRiskBadgeVariant(requestDetail.risk_score)}>{requestDetail.risk_score}</Badge></p>
                    <p className="text-13"><strong>Flagged:</strong> {requestDetail.is_flagged ? 'Yes' : 'No'}</p>
                    {requestDetail.flag_reason && (
                      <p className="text-13"><strong>Reasons:</strong> {requestDetail.flag_reason}</p>
                    )}
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Prompt</h4>
                <div className="bg-muted p-4 rounded text-13 max-h-60 overflow-y-auto">
                  {isAdmin() ? requestDetail.prompt : requestDetail.prompt_preview}
                </div>
              </div>
              
              {isAdmin() && requestDetail.response && (
                <div>
                  <h4 className="font-medium mb-3">Response</h4>
                  <div className="bg-muted p-4 rounded text-13 max-h-60 overflow-y-auto">
                    {requestDetail.response}
                  </div>
                </div>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default Requests;