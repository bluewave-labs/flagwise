import React, { useState, useEffect } from 'react';
import { analyticsService } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MetricCard, MetricCardContent } from '../components/ui/metric-card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Switch } from '../components/ui/switch';
import { Input } from '../components/ui/input';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Shield, 
  Cpu, 
  Calendar,
  RefreshCw,
  AlertTriangle,
  BarChart3,
  Filter,
  Zap
} from 'lucide-react';

const Analytics = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Time range and filters
  const [timeRange, setTimeRange] = useState('daily'); // hourly, daily, weekly, monthly
  const [dateRange, setDateRange] = useState('7d'); // 24h, 7d, 30d, 90d
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [selectedModel, setSelectedModel] = useState('all');
  
  // Analytics data
  const [volumeTrends, setVolumeTrends] = useState([]);
  const [threatTrends, setThreatTrends] = useState([]);
  const [modelUsage, setModelUsage] = useState([]);
  const [providerBreakdown, setProviderBreakdown] = useState([]);
  const [keyMetrics, setKeyMetrics] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  
  // Forecasting data and controls
  const [forecastData, setForecastData] = useState(null);
  const [showForecast, setShowForecast] = useState(false);
  const [forecastDays, setForecastDays] = useState(7);
  const [loadingForecast, setLoadingForecast] = useState(false);
  
  // Available providers and models for filtering
  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);
  
  const COLORS = ['#3b82f6', '#22c55e', '#8b5cf6', '#f97316', '#f43f5e', '#06b6d4', '#84cc16', '#f59e0b'];

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange, dateRange, selectedProvider, selectedModel]);

  const loadForecastData = async () => {
    try {
      setLoadingForecast(true);
      
      const filters = {
        timeRange,
        dateRange,
        forecastDays,
        provider: selectedProvider !== 'all' ? selectedProvider : null,
        model: selectedModel !== 'all' ? selectedModel : null
      };
      
      const response = await analyticsService.getForecast(filters);
      const data = response.data || response;
      
      setForecastData(data);
      
      console.log('Forecast data loaded:', data);
      
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err.response?.data?.detail || "Failed to load forecast data",
      });
      console.error('Forecast error:', err);
    } finally {
      setLoadingForecast(false);
    }
  };

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filters = {
        timeRange,
        dateRange,
        provider: selectedProvider !== 'all' ? selectedProvider : null,
        model: selectedModel !== 'all' ? selectedModel : null
      };
      
      const [
        volumeResponse,
        threatResponse, 
        modelResponse,
        providerResponse,
        metricsResponse,
        anomalyResponse,
        filtersResponse
      ] = await Promise.all([
        analyticsService.getVolumeTrends(filters),
        analyticsService.getThreatTrends(filters),
        analyticsService.getModelUsage(filters),
        analyticsService.getProviderBreakdown(filters),
        analyticsService.getKeyMetrics(filters),
        analyticsService.getAnomalies(filters),
        analyticsService.getFilterOptions()
      ]);
      
      // Extract data from API responses and ensure arrays
      // Check if data is wrapped in .data or returned directly
      const volumeData = volumeResponse.data || volumeResponse;
      const threatData = threatResponse.data || threatResponse;
      const modelData = modelResponse.data || modelResponse;
      const providerData = providerResponse.data || providerResponse;
      const metricsData = metricsResponse.data || metricsResponse;
      const anomalyData = anomalyResponse.data || anomalyResponse;
      const filtersData = filtersResponse.data || filtersResponse;
      
      setVolumeTrends(Array.isArray(volumeData) ? volumeData : []);
      setThreatTrends(Array.isArray(threatData) ? threatData : []);
      setModelUsage(Array.isArray(modelData) ? modelData : []);
      setProviderBreakdown(Array.isArray(providerData) ? providerData : []);
      setKeyMetrics(typeof metricsData === 'object' ? metricsData : {});
      setAnomalies(Array.isArray(anomalyData) ? anomalyData : []);
      setProviders(filtersData?.providers || []);
      setModels(filtersData?.models || []);
      
      console.log('Analytics data loaded:', {
        volumeData,
        providerData,
        metricsData
      });
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics data');
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toLocaleString() || 0;
  };

  const formatPercent = (value) => `${value?.toFixed(1) || 0}%`;
  
  const formatCurrency = (value) => `$${value?.toFixed(2) || 0}`;

  // Combine historical and forecast data for charts
  const getCombinedVolumeData = () => {
    if (!showForecast || !forecastData?.volume_forecast) {
      return volumeTrends;
    }
    
    return [
      ...volumeTrends,
      ...forecastData.volume_forecast.map(point => ({
        ...point,
        isForecast: true
      }))
    ];
  };

  const getCombinedThreatData = () => {
    if (!showForecast || !forecastData?.threat_forecast) {
      return threatTrends;
    }
    
    return [
      ...threatTrends,
      ...forecastData.threat_forecast.map(point => ({
        ...point,
        isForecast: true
      }))
    ];
  };

  const getTimeRangeLabel = () => {
    switch(dateRange) {
      case '24h': return 'Last 24 Hours';
      case '7d': return 'Last 7 Days'; 
      case '30d': return 'Last 30 Days';
      case '90d': return 'Last 90 Days';
      default: return 'Custom Range';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-5 w-5 animate-spin" />
          <span>Loading analytics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-13 text-gray-600">
            Advanced analytics and trend analysis for LLM monitoring
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadAnalyticsData()}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card className="bg-muted/30 border-muted">
        <CardHeader>
          <CardTitle className="text-lg">
            Filters & Time Range
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-13 font-medium mb-2 block">Time Range</label>
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24h">Last 24 Hours</SelectItem>
                  <SelectItem value="7d">Last 7 Days</SelectItem>
                  <SelectItem value="30d">Last 30 Days</SelectItem>
                  <SelectItem value="90d">Last 90 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium mb-2 block">Granularity</label>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">Hourly</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium mb-2 block">Provider</label>
              <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Providers</SelectItem>
                  {providers.map(provider => (
                    <SelectItem key={provider} value={provider}>{provider}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium mb-2 block">Model</label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Models</SelectItem>
                  {models.map(model => (
                    <SelectItem key={model} value={model}>{model}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Forecasting Controls */}
          <div className="mt-6 pt-4 border-t">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Switch
                  checked={showForecast}
                  onCheckedChange={setShowForecast}
                />
                <div>
                  <label className="text-13 font-medium">Enable Predictive Forecasting</label>
                  <p className="text-xs text-muted-foreground">
                    Show AI-powered trend predictions
                  </p>
                </div>
              </div>
              
              {showForecast && (
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <label className="text-13 font-medium">Forecast Days:</label>
                    <Input
                      type="number"
                      min="1"
                      max="30"
                      value={forecastDays}
                      onChange={(e) => setForecastDays(parseInt(e.target.value) || 7)}
                      className="w-20"
                    />
                  </div>
                  <Button
                    size="sm"
                    onClick={loadForecastData}
                    disabled={loadingForecast}
                  >
                    {loadingForecast ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <TrendingUp className="h-4 w-4 mr-1" />
                    )}
                    Generate
                  </Button>
                </div>
              )}
            </div>
            
            {showForecast && forecastData?.confidence_metrics && (
              <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                <span>Confidence: Volume <Badge variant="outline" className="text-xs">
                  {forecastData.confidence_metrics.volume_accuracy}
                </Badge></span>
                <span>Threat <Badge variant="outline" className="text-xs">
                  {forecastData.confidence_metrics.threat_accuracy}
                </Badge></span>
                <span>Data Points: {forecastData.confidence_metrics.data_points}</span>
                <span>Method: {forecastData.confidence_metrics.forecast_method}</span>
              </div>
            )}
          </div>

          <div className="mt-4 text-sm text-muted-foreground">
            Showing data for: <strong>{getTimeRangeLabel()}</strong>
            {selectedProvider !== 'all' && (
              <> • Provider: <strong>{selectedProvider}</strong></>
            )}
            {selectedModel !== 'all' && (
              <> • Model: <strong>{selectedModel}</strong></>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard variant="blue">
          <MetricCardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-5 w-5 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Total Requests</p>
                <div className="flex items-center">
                  <p className="text-xl font-medium text-gray-700">{formatNumber(keyMetrics.totalRequests)}</p>
                  {keyMetrics.requestsGrowth > 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-500 ml-2" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500 ml-2" />
                  )}
                </div>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
        
        <MetricCard variant="red">
          <MetricCardContent className="p-6">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Threat Detection Rate</p>
                <div className="flex items-center">
                  <p className="text-xl font-medium text-gray-700">{formatPercent(keyMetrics.threatRate)}</p>
                  <Badge variant={keyMetrics.threatRate > 5 ? "destructive" : "secondary"} className="ml-2">
                    {keyMetrics.flaggedRequests || 0} flagged
                  </Badge>
                </div>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
        
        <MetricCard variant="purple">
          <MetricCardContent className="p-6">
            <div className="flex items-center">
              <Cpu className="h-5 w-5 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Total Tokens</p>
                <div className="flex items-center">
                  <p className="text-xl font-medium text-gray-700">{formatNumber(keyMetrics.totalTokens)}</p>
                  <span className="text-sm text-muted-foreground ml-2">
                    {formatCurrency(keyMetrics.totalCost)}
                  </span>
                </div>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
        
        <MetricCard variant="orange">
          <MetricCardContent className="p-6">
            <div className="flex items-center">
              <Zap className="h-5 w-5 text-orange-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Avg Response Time</p>
                <div className="flex items-center">
                  <p className="text-xl font-medium text-gray-700">{keyMetrics.avgDuration?.toFixed(0) || 0}ms</p>
                  <span className="text-sm text-muted-foreground ml-2">
                    {keyMetrics.uniqueIPs || 0} IPs
                  </span>
                </div>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Volume Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Request Volume Trends</CardTitle>
            <CardDescription>
              LLM request volume over time ({timeRange} view)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={getCombinedVolumeData()}>
                <defs>
                  <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip 
                  labelFormatter={(label, payload) => {
                    const point = payload?.[0]?.payload;
                    return point?.isForecast ? `${label} (Forecast)` : label;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#volumeGradient)"
                  connectNulls={false}
                />
                {/* Overlay for forecast data with different styling */}
                {showForecast && forecastData?.volume_forecast && (
                  <Area
                    type="monotone"
                    dataKey={(entry) => entry.isForecast ? entry.requests : null}
                    stroke="#8b5cf6"
                    strokeDasharray="5 5"
                    fillOpacity={0.1}
                    fill="url(#forecastGradient)"
                    connectNulls={false}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Threat Detection Rate */}
        <Card>
          <CardHeader>
            <CardTitle>Threat Detection Rate</CardTitle>
            <CardDescription>
              Security threat detection percentage over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getCombinedThreatData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${value}%`, 
                    props.payload?.isForecast ? 'Threat Rate (Forecast)' : 'Threat Rate'
                  ]}
                  labelFormatter={(label, payload) => {
                    const point = payload?.[0]?.payload;
                    return point?.isForecast ? `${label} (Forecast)` : label;
                  }}
                />
                {/* Historical data */}
                <Line 
                  type="monotone" 
                  dataKey="threatRate" 
                  stroke="#f43f5e" 
                  strokeWidth={3}
                  dot={{ fill: '#f43f5e', r: 4 }}
                  connectNulls={false}
                />
                {/* Forecast data with different styling */}
                {showForecast && forecastData?.threat_forecast && (
                  <Line 
                    type="monotone" 
                    dataKey={(entry) => entry.isForecast ? entry.threatRate : null}
                    stroke="#8b5cf6" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ fill: '#8b5cf6', r: 3 }}
                    connectNulls={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Model Usage and Provider Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Usage Patterns */}
        <Card>
          <CardHeader>
            <CardTitle>Model Usage Patterns</CardTitle>
            <CardDescription>
              Usage distribution by AI model
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={modelUsage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="model" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="requests" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Provider Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Provider Distribution</CardTitle>
            <CardDescription>
              Request distribution by AI provider
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={providerBreakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="requests"
                >
                  {Array.isArray(providerBreakdown) && providerBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Anomalies Detection */}
      {Array.isArray(anomalies) && anomalies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              Detected Anomalies
            </CardTitle>
            <CardDescription>
              Unusual patterns detected in your LLM traffic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {anomalies.map((anomaly, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <AlertTriangle className="h-4 w-4 text-orange-500" />
                    <div>
                      <p className="font-medium">{anomaly.type}</p>
                      <p className="text-sm text-muted-foreground">{anomaly.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={anomaly.severity === 'high' ? 'destructive' : 'secondary'}>
                      {anomaly.severity}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {new Date(anomaly.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Analytics;