import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { requestsService } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PageHeader } from '../components/ui/page-header';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Activity,
  AlertTriangle,
  Shield,
  Eye,
  Clock,
  User,
  MapPin,
  Zap,
  AlertCircle,
  Play,
  Pause,
  FileText,
  Key,
  DollarSign,
  Target
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';

const LiveFeed = () => {
  const { isAdmin } = useAuth();
  const [feedItems, setFeedItems] = useState([]);
  const [isRunning, setIsRunning] = useState(true);
  const [showThreatsOnly, setShowThreatsOnly] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [requestDetail, setRequestDetail] = useState(null);
  
  const feedContainerRef = useRef(null);
  const intervalRef = useRef(null);
  const isUserScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef(null);

  // Track user scrolling behavior
  const handleScroll = () => {
    if (feedContainerRef.current) {
      const { scrollTop } = feedContainerRef.current;
      isUserScrollingRef.current = scrollTop > 50; // User has scrolled down from top
      
      // Reset scroll tracking after 3 seconds of no scrolling
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      scrollTimeoutRef.current = setTimeout(() => {
        if (feedContainerRef.current && feedContainerRef.current.scrollTop <= 50) {
          isUserScrollingRef.current = false;
        }
      }, 3000);
    }
  };

  // Fetch latest requests
  const fetchLatestRequests = async () => {
    try {
      const params = {
        page: 1,
        page_size: 50, // Get more recent items
        ...(showThreatsOnly && { flagged: 'true' })
      };
      
      const response = await requestsService.getRequests(params);
      const newItems = response.data.items || [];
      
      setFeedItems(prevItems => {
        // Combine new and existing items
        const combinedItems = [...newItems, ...prevItems];
        
        // Remove duplicates based on ID
        const uniqueItems = combinedItems.filter((item, index, self) => 
          index === self.findIndex(t => t.id === item.id)
        );
        
        // Sort by timestamp (newest first)
        uniqueItems.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Apply time-based removal (10 minutes)
        const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
        const filteredItems = uniqueItems.filter(item => 
          new Date(item.timestamp) > tenMinutesAgo
        );
        
        // Limit to 200 items
        return filteredItems.slice(0, 200);
      });
      
      setLastUpdate(new Date());
      setError(null);
      
    } catch (err) {
      setError('Failed to fetch live feed data');
      console.error('Live feed error:', err);
    }
  };

  // Auto-scroll to top for new items (only if user hasn't scrolled)
  useEffect(() => {
    if (!isUserScrollingRef.current && feedContainerRef.current && feedItems.length > 0) {
      feedContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [feedItems]);

  // Start/stop polling
  useEffect(() => {
    if (isRunning) {
      // Initial fetch
      fetchLatestRequests();
      
      // Set up polling every 2 seconds
      intervalRef.current = setInterval(fetchLatestRequests, 2000);
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
  }, [isRunning, showThreatsOnly]);

  // Fetch request detail
  const fetchRequestDetail = async (requestId) => {
    try {
      const response = await requestsService.getRequestById(requestId);
      setRequestDetail(response.data);
    } catch (err) {
      console.error('Failed to load request detail:', err);
    }
  };

  const handleRequestClick = (request) => {
    setSelectedRequest(request);
    fetchRequestDetail(request.id);
  };

  const toggleFeed = () => {
    setIsRunning(prev => !prev);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getRiskColor = (riskScore) => {
    if (riskScore >= 70) return 'text-red-500 border-red-500';
    if (riskScore >= 40) return 'text-orange-500 border-orange-500';
    if (riskScore >= 10) return 'text-yellow-500 border-yellow-500';
    return 'text-blue-500 border-blue-500';
  };

  const getRiskBadgeVariant = (riskScore) => {
    if (riskScore >= 70) return 'destructive';
    if (riskScore >= 40) return 'secondary';
    if (riskScore >= 10) return 'outline';
    return 'default';
  };

  const getThreatIcon = (flagReason, riskScore) => {
    if (!flagReason && riskScore < 10) return <Shield className="h-3 w-3" />;
    
    if (flagReason?.toLowerCase().includes('keyword')) return <FileText className="h-3 w-3" />;
    if (flagReason?.toLowerCase().includes('email')) return <User className="h-3 w-3" />;
    if (flagReason?.toLowerCase().includes('injection')) return <AlertTriangle className="h-3 w-3" />;
    if (flagReason?.toLowerCase().includes('model')) return <Key className="h-3 w-3" />;
    
    return <Target className="h-3 w-3" />;
  };

  const getThreatType = (flagReason) => {
    if (!flagReason) return 'Clean';
    
    if (flagReason.toLowerCase().includes('keyword')) return 'Sensitive Data';
    if (flagReason.toLowerCase().includes('email')) return 'Data Exposure';
    if (flagReason.toLowerCase().includes('injection')) return 'Prompt Injection';
    if (flagReason.toLowerCase().includes('model')) return 'Unauthorized Access';
    
    return 'Policy Violation';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Live Feed</h1>
          <p className="text-13 text-gray-600">
            Real-time stream of LLM requests and security events (auto-refreshes every 2 seconds)
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Threats Only</span>
            <Switch 
              checked={showThreatsOnly} 
              onCheckedChange={setShowThreatsOnly}
            />
          </div>
          
          <Button
            variant={isRunning ? "outline" : "default"}
            onClick={toggleFeed}
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

      {/* Status Bar */}
      <Card className="bg-muted/60 border-muted">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isRunning ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium">
                  {isRunning ? 'Live' : 'Paused'}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {feedItems.length} items
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Updated: {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
            
            {showThreatsOnly && (
              <Badge variant="secondary" className="flex items-center space-x-1">
                <AlertTriangle className="h-3 w-3" />
                <span>Threats Only</span>
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Live Feed Timeline */}
      <Card>
        <CardHeader>
        </CardHeader>
        <CardContent>
          <div 
            ref={feedContainerRef}
            onScroll={handleScroll}
            className="max-h-[600px] overflow-y-auto space-y-0 pr-2"
          >
            {feedItems.length > 0 ? (
              <div className="relative">
                {/* Timeline vertical line */}
                <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border"></div>
                
                {feedItems.map((item, index) => (
                  <div key={item.id} className="relative flex items-start space-x-4 pb-6">
                    {/* Timeline node */}
                    <div className="flex flex-col items-center">
                      <div className="text-xs text-muted-foreground mb-1 w-16 text-center">
                        {formatTimestamp(item.timestamp)}
                      </div>
                      <div className={`h-6 w-6 rounded-full border-2 bg-background flex items-center justify-center ${getRiskColor(item.risk_score)}`}>
                        {getThreatIcon(item.flag_reason, item.risk_score)}
                      </div>
                    </div>
                    
                    {/* Timeline content */}
                    <div className="flex-1 min-w-0 pb-2">
                      <div 
                        className="bg-card border rounded-lg p-4 hover:bg-accent/50 cursor-pointer transition-colors"
                        onClick={() => handleRequestClick(item)}
                      >
                        <div className="flex items-start justify-between space-x-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <Badge variant="outline" className="text-xs">
                                {item.provider}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                {item.model}
                              </Badge>
                              <Badge variant={getRiskBadgeVariant(item.risk_score)} className="text-xs">
                                Risk: {item.risk_score}
                              </Badge>
                              {item.is_flagged && (
                                <Badge variant="destructive" className="text-xs">
                                  {getThreatType(item.flag_reason)}
                                </Badge>
                              )}
                            </div>
                            
                            <div className="flex items-center space-x-3 text-sm text-muted-foreground mb-2">
                              <div className="flex items-center space-x-1">
                                <MapPin className="h-3 w-3" />
                                <span className="font-mono">{item.src_ip}</span>
                              </div>
                              
                              
                            </div>
                            
                            <div className="text-sm truncate">
                              <span className="text-muted-foreground">Prompt: </span>
                              <span>{item.prompt_preview || 'No preview available'}</span>
                            </div>
                          </div>
                          
                          <Button variant="ghost" size="sm" className="flex-shrink-0">
                            <Eye className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">
                  {isRunning ? 'Waiting for activity...' : 'Feed paused'}
                </h3>
                <p className="text-muted-foreground">
                  {isRunning 
                    ? (showThreatsOnly 
                        ? 'No security threats detected recently.' 
                        : 'No LLM requests detected recently.')
                    : 'Click "Start Feed" to begin monitoring activity.'}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Request Detail Modal */}
      <Dialog open={!!selectedRequest} onOpenChange={() => setSelectedRequest(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Request Details</DialogTitle>
            <DialogDescription>
              Full details for request from {selectedRequest?.src_ip}
            </DialogDescription>
          </DialogHeader>
          {requestDetail && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-2">Basic Information</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Timestamp:</span>
                      <span className="text-sm">{new Date(requestDetail.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Source IP:</span>
                      <span className="font-mono">{requestDetail.src_ip}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Provider:</span>
                      <Badge variant="outline">{requestDetail.provider}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Model:</span>
                      <Badge variant="secondary">{requestDetail.model}</Badge>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Risk Assessment</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Risk Score:</span>
                      <Badge variant={getRiskBadgeVariant(requestDetail.risk_score)}>
                        {requestDetail.risk_score}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Status:</span>
                      <Badge variant={requestDetail.is_flagged ? "destructive" : "default"}>
                        {requestDetail.is_flagged ? "Flagged" : "Clean"}
                      </Badge>
                    </div>
                    {requestDetail.flag_reason && (
                      <div className="flex items-center justify-between">
                        <span>Threat Type:</span>
                        <span className="text-sm">{getThreatType(requestDetail.flag_reason)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Prompt</h4>
                <div className="bg-muted p-3 rounded-md">
                  <pre className="whitespace-pre-wrap text-sm">
                    {isAdmin() ? requestDetail.prompt : requestDetail.prompt_preview}
                  </pre>
                </div>
              </div>
              
              {isAdmin() && requestDetail.response && (
                <div>
                  <h4 className="font-semibold mb-2">Response</h4>
                  <div className="bg-muted p-3 rounded-md">
                    <pre className="whitespace-pre-wrap text-sm">{requestDetail.response}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LiveFeed;