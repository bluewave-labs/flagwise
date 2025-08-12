import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { settingsService, kafkaService } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { PageHeader, PageHeaderTabs } from '../components/ui/page-header';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import { 
  Loader2, 
  Settings as SettingsIcon, 
  Database,
  Download,
  Trash2,
  AlertCircle,
  CheckCircle,
  Calendar,
  BarChart3,
  FileText,
  Save,
  RotateCcw,
  HardDrive,
  Activity,
  Clock,
  Zap,
  Server,
  Play,
  Square,
  TestTube,
  Cable,
  Shield,
  Key,
  FileKey,
  Timer,
  RefreshCw,
  Circle,
  Edit
} from 'lucide-react';

const Settings = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Settings state
  const [settings, setSettings] = useState([]);
  const [databaseStats, setDatabaseStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);
  
  // Export state
  const [exportLoading, setExportLoading] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showCleanupDialog, setShowCleanupDialog] = useState(false);
  const [showPurgeDialog, setShowPurgeDialog] = useState(false);
  const [exportForm, setExportForm] = useState({
    data_type: 'requests',
    format: 'json',
    start_date: '',
    end_date: ''
  });
  
  // Data Sources state
  const [kafkaSettings, setKafkaSettings] = useState({
    kafka_enabled: false,
    kafka_brokers: 'localhost:9092',
    kafka_topic: 'llm-traffic-logs',
    kafka_group_id: 'flagwise-consumer',
    kafka_auth_type: 'none',
    kafka_username: '',
    kafka_password: '',
    kafka_ssl_cert: '',
    kafka_ssl_key: '',
    kafka_ssl_ca: '',
    kafka_timeout_ms: '30000',
    kafka_retry_backoff_ms: '1000',
    kafka_message_schema: '',
    demo_data_enabled: true
  });
  const [kafkaStatus, setKafkaStatus] = useState('disconnected'); // connected, disconnected, testing
  const [showSchemaDialog, setShowSchemaDialog] = useState(false);
  const [showDemoDataDialog, setShowDemoDataDialog] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [schemaError, setSchemaError] = useState(null);

  // Load settings and database stats
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsResponse, statsResponse] = await Promise.all([
        settingsService.getSettings(),
        settingsService.getDatabaseStats()
      ]);
      
      setSettings(settingsResponse.data);
      setDatabaseStats(statsResponse.data);
      
      // Parse Kafka settings from loaded settings
      const kafkaConfig = {};
      settingsResponse.data.forEach(setting => {
        if (setting.category === 'data_sources') {
          if (setting.key === 'kafka_enabled') {
            kafkaConfig[setting.key] = setting.value === 'true';
          } else if (setting.key === 'demo_data_enabled') {
            kafkaConfig[setting.key] = setting.value === 'true';
          } else {
            kafkaConfig[setting.key] = setting.value;
          }
        }
      });
      
      setKafkaSettings(prev => ({ ...prev, ...kafkaConfig }));
      
      // Set initial Kafka status based on enabled state
      setKafkaStatus(kafkaConfig.kafka_enabled ? 'connected' : 'disconnected');
      
    } catch (err) {
      setError('Failed to load settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadDatabaseStats = async () => {
    try {
      setStatsLoading(true);
      const response = await settingsService.getDatabaseStats();
      setDatabaseStats(response.data);
    } catch (err) {
      setError('Failed to refresh database statistics');
      console.error(err);
    } finally {
      setStatsLoading(false);
    }
  };

  const updateSetting = async (key, value) => {
    try {
      await settingsService.updateSetting(key, value);
      setSuccess(`Setting "${key}" updated successfully`);
      
      // Update local state
      setSettings(prev => 
        prev.map(setting => 
          setting.key === key ? { ...setting, value, updated_at: new Date().toISOString() } : setting
        )
      );
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to update setting: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleManualCleanup = async () => {
    try {
      setLoading(true);
      const response = await settingsService.manualCleanup();
      const stats = response.data.cleanup_stats;
      
      const totalDeleted = stats.total_deleted;
      const description = totalDeleted > 0 
        ? `Deleted ${stats.deleted_requests.toLocaleString()} requests, ${stats.deleted_alerts} alerts, ${stats.deleted_sessions} sessions (${totalDeleted.toLocaleString()} total records)`
        : `No records older than ${stats.retention_days} days found to delete`;
      
      toast({
        variant: "success",
        title: "Cleanup Completed",
        description: description
      });
      
      // Refresh stats after cleanup
      await loadDatabaseStats();
      
      setShowCleanupDialog(false);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Cleanup Failed",
        description: err.response?.data?.detail || err.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePurgeAllData = async () => {
    try {
      setLoading(true);
      const response = await settingsService.purgeAllData();
      const stats = response.data.purge_stats;
      
      const totalDeleted = stats.total_deleted;
      const analyticsDeleted = (stats.deleted_analytics_hourly || 0) + (stats.deleted_analytics_daily || 0) + 
                              (stats.deleted_analytics_weekly || 0) + (stats.deleted_analytics_monthly || 0);
      
      const description = `Purged ${stats.deleted_requests.toLocaleString()} requests, ${stats.deleted_alerts} alerts, ${stats.deleted_sessions} sessions, ${stats.deleted_rules} rules, ${analyticsDeleted.toLocaleString()} analytics records (${totalDeleted.toLocaleString()} total records)`;
      
      toast({
        variant: "success",
        title: "All Data Purged",
        description: description
      });
      
      // Refresh stats after purge
      await loadDatabaseStats();
      
      setShowPurgeDialog(false);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Purge Failed",
        description: err.response?.data?.detail || err.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      if (!exportForm.start_date || !exportForm.end_date) {
        setError('Please select both start and end dates for export');
        return;
      }

      setExportLoading(true);
      const response = await settingsService.exportData({
        ...exportForm,
        start_date: new Date(exportForm.start_date).toISOString(),
        end_date: new Date(exportForm.end_date).toISOString()
      });

      // Create download link
      const blob = new Blob([response.data], { 
        type: exportForm.format === 'csv' ? 'text/csv' : 'application/json' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${exportForm.data_type}_export.${exportForm.format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess(`${exportForm.data_type} data exported successfully`);
      setShowExportDialog(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to export data: ${err.response?.data?.detail || err.message}`);
    } finally {
      setExportLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  const getSettingByKey = (key) => {
    return settings.find(s => s.key === key);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">System Settings</h1>
          <p className="text-13 text-gray-600">
            Configure system settings and manage data storage
          </p>
        </div>
        <Button variant="outline" onClick={() => loadData()}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert variant="default" className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="data-sources" className="space-y-6">
        <TabsList className="grid grid-cols-2 w-full max-w-2xl">
          <TabsTrigger value="data-sources" className="flex items-center space-x-2">
            <Zap className="h-4 w-4" />
            <span>Data Sources</span>
          </TabsTrigger>
          <TabsTrigger value="data-storage" className="flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <span>Data & Storage</span>
          </TabsTrigger>
        </TabsList>

        {/* Data Sources Tab */}
        <TabsContent value="data-sources" className="space-y-6">

          {/* Demo Data Control */}
          <Card>
            <CardHeader>
              <CardTitle>
                Demo Data Control
              </CardTitle>
              <CardDescription>
                Manage demo data generation for testing and development
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Demo Data Generation</p>
                  <p className="text-sm text-muted-foreground">
                    {kafkaSettings.demo_data_enabled ? 'Currently generating sample LLM traffic' : 'Demo data generation stopped'}
                  </p>
                </div>
                
                <Dialog open={showDemoDataDialog} onOpenChange={setShowDemoDataDialog}>
                  <DialogTrigger asChild>
                    <Button variant={kafkaSettings.demo_data_enabled ? "destructive" : "default"}>
                      {kafkaSettings.demo_data_enabled ? (
                        <>
                          <Square className="h-4 w-4 mr-2" />
                          Remove Demo Data
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Add Demo Data
                        </>
                      )}
                    </Button>
                  </DialogTrigger>
                  
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {kafkaSettings.demo_data_enabled ? 'Remove Demo Data' : 'Add Demo Data'}
                      </DialogTitle>
                      <DialogDescription>
                        {kafkaSettings.demo_data_enabled 
                          ? 'This will stop demo data generation and permanently delete all existing demo data. This action cannot be undone.'
                          : 'This will start generating demo LLM traffic data for testing and development purposes.'
                        }
                      </DialogDescription>
                    </DialogHeader>
                    
                    <div className="flex justify-end space-x-2">
                      <Button 
                        variant="outline" 
                        onClick={() => setShowDemoDataDialog(false)}
                      >
                        Cancel
                      </Button>
                      <Button 
                        variant={kafkaSettings.demo_data_enabled ? "destructive" : "default"}
                        onClick={async () => {
                          try {
                            const newEnabled = !kafkaSettings.demo_data_enabled;
                            const clearData = !newEnabled; // Clear data when disabling
                            
                            await kafkaService.toggleDemoData(newEnabled, clearData);
                            setKafkaSettings({...kafkaSettings, demo_data_enabled: newEnabled});
                            setSuccess(newEnabled ? 'Demo data generation started' : 'Demo data removed successfully');
                            setShowDemoDataDialog(false);
                            
                            setTimeout(() => setSuccess(null), 3000);
                          } catch (err) {
                            setError(err.response?.data?.detail || 'Failed to toggle demo data');
                          }
                        }}
                      >
                        {kafkaSettings.demo_data_enabled ? 'Remove Demo Data' : 'Add Demo Data'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>

          {/* Kafka Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>
                    Kafka Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure connection to your Kafka broker for real-time LLM traffic ingestion
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Circle 
                    className={`h-3 w-3 ${
                      kafkaStatus === 'connected' ? 'text-green-500 fill-green-500' : 
                      kafkaStatus === 'testing' ? 'text-yellow-500 fill-yellow-500' : 
                      'text-red-500 fill-red-500'
                    }`} 
                  />
                  <span className="text-sm font-medium capitalize">{kafkaStatus}</span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Enable/Disable Kafka */}
              <div className="flex items-center space-x-2 p-3 bg-muted/10 rounded-lg">
                <input
                  type="checkbox"
                  id="kafka-enabled"
                  checked={kafkaSettings.kafka_enabled}
                  onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_enabled: e.target.checked})}
                  className="w-4 h-4 text-primary bg-background border-2 border-border rounded focus:ring-primary"
                />
                <label htmlFor="kafka-enabled" className="text-sm font-medium">
                  Enable Kafka data ingestion
                </label>
                <Badge variant={kafkaSettings.kafka_enabled ? "default" : "secondary"}>
                  {kafkaSettings.kafka_enabled ? "Enabled" : "Disabled"}
                </Badge>
              </div>

              {/* Basic Connection Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Kafka Brokers</label>
                  <Input
                    value={kafkaSettings.kafka_brokers}
                    onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_brokers: e.target.value})}
                    placeholder="broker1:9092,broker2:9092"
                    className="mt-1"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Comma-separated list of Kafka broker URLs
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Topic Name</label>
                  <Input
                    value={kafkaSettings.kafka_topic}
                    onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_topic: e.target.value})}
                    placeholder="llm-traffic-logs"
                    className="mt-1"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Kafka topic containing LLM packet data
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Consumer Group ID</label>
                  <Input
                    value={kafkaSettings.kafka_group_id}
                    onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_group_id: e.target.value})}
                    placeholder="flagwise-consumer"
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Authentication</label>
                  <Select 
                    value={kafkaSettings.kafka_auth_type}
                    onValueChange={(value) => setKafkaSettings({...kafkaSettings, kafka_auth_type: value})}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      <SelectItem value="sasl_plain">SASL/PLAIN</SelectItem>
                      <SelectItem value="sasl_ssl">SASL/SSL</SelectItem>
                      <SelectItem value="ssl">SSL Only</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Authentication Fields */}
              {kafkaSettings.kafka_auth_type !== 'none' && (
                <div className="space-y-4 p-4 bg-muted/20 rounded-lg">
                  <h4 className="font-medium flex items-center space-x-2">
                    <Shield className="h-4 w-4" />
                    <span>Authentication Credentials</span>
                  </h4>
                  
                  {(kafkaSettings.kafka_auth_type === 'sasl_plain' || kafkaSettings.kafka_auth_type === 'sasl_ssl') && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium">Username</label>
                        <Input
                          value={kafkaSettings.kafka_username}
                          onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_username: e.target.value})}
                          placeholder="kafka-username"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Password</label>
                        <Input
                          type="password"
                          value={kafkaSettings.kafka_password}
                          onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_password: e.target.value})}
                          placeholder="kafka-password"
                          className="mt-1"
                        />
                      </div>
                    </div>
                  )}
                  
                  {(kafkaSettings.kafka_auth_type === 'ssl' || kafkaSettings.kafka_auth_type === 'sasl_ssl') && (
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">SSL Certificate</label>
                        <textarea
                          value={kafkaSettings.kafka_ssl_cert}
                          onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_ssl_cert: e.target.value})}
                          placeholder="-----BEGIN CERTIFICATE-----"
                          className="mt-1 w-full h-20 px-3 py-2 text-sm bg-background border border-input rounded-md resize-y"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">SSL Private Key</label>
                        <textarea
                          value={kafkaSettings.kafka_ssl_key}
                          onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_ssl_key: e.target.value})}
                          placeholder="-----BEGIN PRIVATE KEY-----"
                          className="mt-1 w-full h-20 px-3 py-2 text-sm bg-background border border-input rounded-md resize-y"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">SSL CA Certificate</label>
                        <textarea
                          value={kafkaSettings.kafka_ssl_ca}
                          onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_ssl_ca: e.target.value})}
                          placeholder="-----BEGIN CERTIFICATE-----"
                          className="mt-1 w-full h-20 px-3 py-2 text-sm bg-background border border-input rounded-md resize-y"
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Advanced Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Connection Timeout (ms)</label>
                  <Input
                    type="number"
                    value={kafkaSettings.kafka_timeout_ms}
                    onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_timeout_ms: e.target.value})}
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Retry Backoff (ms)</label>
                  <Input
                    type="number"
                    value={kafkaSettings.kafka_retry_backoff_ms}
                    onChange={(e) => setKafkaSettings({...kafkaSettings, kafka_retry_backoff_ms: e.target.value})}
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Message Schema */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium mb-2 block">Message Schema</label>
                  <textarea
                    value={kafkaSettings.kafka_message_schema || JSON.stringify({
                      "timestamp": "string",
                      "request_id": "string", 
                      "src_ip": "string",
                      "provider": "string",
                      "model": "string",
                      "prompt": "string",
                      "metadata": "object"
                    }, null, 2)}
                    onChange={(e) => {
                      setKafkaSettings({...kafkaSettings, kafka_message_schema: e.target.value});
                    }}
                    className="w-full px-3 py-2 text-sm font-mono bg-slate-900 text-slate-100 border border-slate-700 rounded-lg resize-y"
                    placeholder={JSON.stringify({
                      "timestamp": "string",
                      "request_id": "string", 
                      "src_ip": "string",
                      "provider": "string",
                      "model": "string",
                      "prompt": "string",
                      "metadata": "object"
                    }, null, 2)}
                    style={{ minHeight: '200px' }}
                  />
                  {schemaError && (
                    <p className="text-sm text-red-500 mt-1">{schemaError}</p>
                  )}
                </div>
                
                <div className="p-4 bg-muted/20 rounded-lg">
                  <h4 className="font-medium mb-3">Required Fields</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-start space-x-2">
                      <code className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">timestamp</code>
                      <span className="text-muted-foreground">Request timestamp (ISO format)</span>
                    </div>
                    <div className="flex items-start space-x-2">
                      <code className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">request_id</code>
                      <span className="text-muted-foreground">Unique request identifier</span>
                    </div>
                    <div className="flex items-start space-x-2">
                      <code className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">src_ip</code>
                      <span className="text-muted-foreground">Source IP address</span>
                    </div>
                    <div className="flex items-start space-x-2">
                      <code className="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded">provider</code>
                      <span className="text-muted-foreground">LLM provider (openai, anthropic)</span>
                    </div>
                    <div className="flex items-start space-x-2">
                      <code className="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded">model</code>
                      <span className="text-muted-foreground">Model name (gpt-4, claude-3)</span>
                    </div>
                    <div className="flex items-start space-x-2">
                      <code className="text-xs bg-purple-100 text-purple-800 px-1.5 py-0.5 rounded">prompt</code>
                      <span className="text-muted-foreground">User prompt content</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t">
                <Button 
                  variant="outline"
                  onClick={async () => {
                    try {
                      setTestingConnection(true);
                      
                      const result = await kafkaService.testConnection(kafkaSettings);
                      
                      if (result.data.status === 'success') {
                        toast({
                          variant: "success",
                          title: "Connection Successful",
                          description: `Found ${result.data.broker_count} brokers. Topic "${kafkaSettings.kafka_topic}" ${result.data.topic_exists ? 'exists' : 'not found'}.`
                        });
                        setKafkaStatus('connected');
                      } else {
                        toast({
                          variant: "destructive",
                          title: "Connection Failed",
                          description: result.data.message
                        });
                        setKafkaStatus('disconnected');
                      }
                    } catch (err) {
                      toast({
                        variant: "destructive",
                        title: "Connection Test Failed",
                        description: err.response?.data?.detail || 'Unable to test connection'
                      });
                      setKafkaStatus('disconnected');
                    } finally {
                      setTestingConnection(false);
                    }
                  }}
                  disabled={testingConnection}
                >
                  {testingConnection ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <TestTube className="h-4 w-4 mr-2" />
                      Test Connection
                    </>
                  )}
                </Button>
                
                <div className="space-x-2">
                  <Button variant="outline" onClick={loadData}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reset
                  </Button>
                  <Button onClick={async () => {
                    try {
                      setLoading(true);
                      
                      const result = await kafkaService.saveConfiguration(kafkaSettings);
                      toast({
                        variant: "success",
                        title: "Configuration Saved",
                        description: result.data.restart_status
                      });
                      
                      // Update status based on saved enabled state
                      setKafkaStatus(kafkaSettings.kafka_enabled ? 'connected' : 'disconnected');
                    } catch (err) {
                      toast({
                        variant: "destructive",
                        title: "Save Failed",
                        description: err.response?.data?.detail || 'Failed to save configuration'
                      });
                    } finally {
                      setLoading(false);
                    }
                  }}>
                    <Save className="h-4 w-4 mr-2" />
                    Save Configuration
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data-storage" className="space-y-6">
          {/* Retention Policy Section */}
          <Card>
            <CardHeader>
              <CardTitle>
                Data Retention Policy
              </CardTitle>
              <CardDescription>
                Configure how long data is stored before automatic deletion
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Retention Period (Days)</label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input
                        type="number"
                        min="1"
                        max="3650"
                        value={getSettingByKey('data_retention_days')?.value || '180'}
                        onChange={(e) => updateSetting('data_retention_days', e.target.value)}
                        className="flex-1"
                      />
                      <Badge variant="outline">
                        {Math.round((getSettingByKey('data_retention_days')?.value || 180) / 30)} months
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Data older than this will be automatically deleted (default: 180 days)
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Automatic Cleanup</label>
                    <Select 
                      value={getSettingByKey('cleanup_enabled')?.value || 'true'}
                      onValueChange={(value) => updateSetting('cleanup_enabled', value)}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="true">Enabled</SelectItem>
                        <SelectItem value="false">Disabled</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground mt-1">
                      Enable or disable automatic data cleanup
                    </p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Manual Cleanup</label>
                    <Dialog open={showCleanupDialog} onOpenChange={setShowCleanupDialog}>
                      <DialogTrigger asChild>
                        <Button
                          variant="destructive"
                          className="w-full mt-1"
                          disabled={loading}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Run Cleanup Now
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Confirm Database Cleanup</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to manually trigger database cleanup? This will permanently delete old data based on your retention settings.
                          </DialogDescription>
                        </DialogHeader>
                        
                        <div className="flex justify-end space-x-2">
                          <Button 
                            variant="outline" 
                            onClick={() => setShowCleanupDialog(false)}
                          >
                            Cancel
                          </Button>
                          <Button 
                            variant="destructive"
                            onClick={handleManualCleanup}
                            disabled={loading}
                          >
                            {loading ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4 mr-2" />
                            )}
                            Delete Old Data
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                    <p className="text-xs text-muted-foreground mt-1">
                      Immediately delete data older than the retention period
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Purge All Data</label>
                    <Dialog open={showPurgeDialog} onOpenChange={setShowPurgeDialog}>
                      <DialogTrigger asChild>
                        <Button
                          variant="destructive"
                          className="w-full mt-1"
                          disabled={loading}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Purge All Data
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>⚠️ Confirm Data Purge</DialogTitle>
                          <DialogDescription>
                            <span className="text-red-600 font-semibold">WARNING: This action cannot be undone!</span>
                            <br /><br />
                            This will permanently delete ALL collected data from the database including:
                            <ul className="mt-2 ml-4 list-disc space-y-1">
                              <li>All LLM requests and responses</li>
                              <li>All alerts and notifications</li>
                              <li>All user sessions</li>
                              <li>All detection rules</li>
                              <li>All analytics data (hourly, daily, weekly, monthly)</li>
                            </ul>
                            <br />
                            Only user accounts and system settings will be preserved.
                          </DialogDescription>
                        </DialogHeader>
                        
                        <div className="flex justify-end space-x-2">
                          <Button 
                            variant="outline" 
                            onClick={() => setShowPurgeDialog(false)}
                          >
                            Cancel
                          </Button>
                          <Button 
                            variant="destructive"
                            onClick={handlePurgeAllData}
                            disabled={loading}
                          >
                            {loading ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4 mr-2" />
                            )}
                            Purge All Data
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                    <p className="text-xs text-muted-foreground mt-1">
                      Permanently delete ALL collected data from the database
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Database Statistics Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Database Statistics</CardTitle>
                  <CardDescription>
                    Current database usage and table information
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadDatabaseStats}
                  disabled={statsLoading}
                >
                  {statsLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Activity className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {databaseStats && (
                <div className="space-y-6">
                  {/* Overview Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-medium text-blue-600">
                        {formatNumber(databaseStats.total_requests)}
                      </div>
                      <div className="text-sm text-muted-foreground">LLM Requests</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-medium text-orange-600">
                        {formatNumber(databaseStats.total_alerts)}
                      </div>
                      <div className="text-sm text-muted-foreground">Alerts</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-medium text-green-600">
                        {formatNumber(databaseStats.total_sessions)}
                      </div>
                      <div className="text-sm text-muted-foreground">Sessions</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-medium text-purple-600">
                        {databaseStats.database_size_mb.toFixed(1)} MB
                      </div>
                      <div className="text-sm text-muted-foreground">Database Size</div>
                    </div>
                  </div>

                  {/* Table Details */}
                  <div>
                    <h4 className="font-semibold mb-3">Table Breakdown</h4>
                    <div className="space-y-2">
                      {Object.entries(databaseStats.table_sizes).map(([tableName, stats]) => (
                        <div key={tableName} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center space-x-3">
                            <HardDrive className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="font-medium">{tableName}</div>
                              <div className="text-sm text-muted-foreground">
                                {formatNumber(stats.live_rows)} rows
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium">{stats.size_pretty}</div>
                            <div className="text-sm text-muted-foreground">
                              {stats.size_mb.toFixed(2)} MB
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data Export Section */}
          <Card>
            <CardHeader>
              <CardTitle>Data Export</CardTitle>
              <CardDescription>
                Export data with custom date ranges in CSV or JSON format
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Export Limit</label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input
                        type="number"
                        min="1000"
                        max="1000000"
                        value={getSettingByKey('max_export_records')?.value || '100000'}
                        onChange={(e) => updateSetting('max_export_records', e.target.value)}
                        className="flex-1"
                      />
                      <span className="text-sm text-muted-foreground">records</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Maximum number of records per export
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center justify-center">
                  <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
                    <DialogTrigger asChild>
                      <Button className="w-full">
                        <FileText className="h-4 w-4 mr-2" />
                        Export Data
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Export Data</DialogTitle>
                        <DialogDescription>
                          Choose what data to export and the date range
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium">Data Type</label>
                            <Select 
                              value={exportForm.data_type}
                              onValueChange={(value) => setExportForm({...exportForm, data_type: value})}
                            >
                              <SelectTrigger className="mt-1">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="requests">LLM Requests</SelectItem>
                                <SelectItem value="alerts">Alerts</SelectItem>
                                <SelectItem value="sessions">Sessions</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          
                          <div>
                            <label className="text-sm font-medium">Format</label>
                            <Select 
                              value={exportForm.format}
                              onValueChange={(value) => setExportForm({...exportForm, format: value})}
                            >
                              <SelectTrigger className="mt-1">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="json">JSON</SelectItem>
                                <SelectItem value="csv">CSV</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium">Start Date</label>
                            <Input
                              type="datetime-local"
                              value={exportForm.start_date}
                              onChange={(e) => setExportForm({...exportForm, start_date: e.target.value})}
                              className="mt-1"
                            />
                          </div>
                          
                          <div>
                            <label className="text-sm font-medium">End Date</label>
                            <Input
                              type="datetime-local"
                              value={exportForm.end_date}
                              onChange={(e) => setExportForm({...exportForm, end_date: e.target.value})}
                              className="mt-1"
                            />
                          </div>
                        </div>
                        
                        <div className="flex justify-end space-x-2">
                          <Button 
                            variant="outline" 
                            onClick={() => setShowExportDialog(false)}
                          >
                            Cancel
                          </Button>
                          <Button 
                            onClick={handleExport}
                            disabled={exportLoading}
                          >
                            {exportLoading ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4 mr-2" />
                            )}
                            Export
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;