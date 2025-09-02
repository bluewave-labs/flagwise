import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { rulesService } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { useDebounce } from '../hooks/useDebounce';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Pagination } from '../components/ui/pagination';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Checkbox } from '../components/ui/checkbox';
import { 
  Loader2, 
  Plus, 
  Edit, 
  Trash2, 
  AlertTriangle, 
  Shield,
  Eye,
  Copy,
  Download,
  Upload,
  Settings,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
  Lock,
  Unlock,
  Code,
  Zap,
  Target,
  Database,
  FileText,
  Globe,
  Cpu
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { SkeletonDetectionRules } from '../components/ui/skeleton';

const DetectionRules = () => {
  const { isAdmin } = useAuth();
  const { toast } = useToast();
  const [rules, setRules] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRules, setSelectedRules] = useState(new Set());
  
  // Filters and search
  const [filters, setFilters] = useState({
    category: 'all',
    rule_type: 'all',
    severity: 'all',
    is_active: 'all',
    search: ''
  });

  // Debounce search term to avoid excessive API calls
  const debouncedSearch = useDebounce(filters.search, 300);
  
  // Reset page when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch]);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Create/Edit Sheet
  const [showRuleSheet, setShowRuleSheet] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [showTemplatesDialog, setShowTemplatesDialog] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'security',
    rule_type: 'keyword',
    pattern: '',
    severity: 'medium',
    points: 50,
    priority: 0,
    stop_on_match: false,
    combination_logic: 'AND',
    is_active: true
  });

  const fetchRules = async (page = currentPage) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page,
        page_size: pageSize,
        ...Object.fromEntries(
          Object.entries({
            search: debouncedSearch || undefined,
            rule_type: filters.rule_type !== 'all' ? filters.rule_type : undefined,
            is_active: filters.is_active !== 'all' ? (filters.is_active === 'active') : undefined
          }).filter(([_, value]) => value !== undefined)
        )
      };
      
      const response = await rulesService.getRules(params);
      const data = response.data || response;
      
      setRules(data.items || []);
      setTotalCount(data.total_count || 0);
      setTotalPages(data.total_pages || 1);
      setCurrentPage(data.page || page);
      
    } catch (err) {
      const errorMessage = 'Failed to load detection rules';
      setError(errorMessage);
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage,
      });
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await rulesService.getTemplates();
      setTemplates(response.data || []);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  useEffect(() => {
    if (isAdmin()) {
      fetchRules();
      fetchTemplates();
    }
  }, []);
  
  useEffect(() => {
    if (isAdmin()) {
      fetchRules();
    }
  }, [currentPage, pageSize, filters]);

  const handleCreateRule = async (e) => {
    e.preventDefault();
    try {
      if (editingRule) {
        await rulesService.updateRule(editingRule.id, formData);
        toast({
          variant: "success",
          title: "Success",
          description: "Rule updated successfully",
        });
      } else {
        await rulesService.createRule(formData);
        toast({
          variant: "success",
          title: "Success",
          description: "Rule created successfully",
        });
      }
      
      setShowRuleSheet(false);
      setEditingRule(null);
      resetForm();
      fetchRules();
    } catch (err) {
      const errorMessage = editingRule ? 'Failed to update rule' : 'Failed to create rule';
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage,
      });
      console.error(err);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (window.confirm('Are you sure you want to delete this rule?')) {
      try {
        await rulesService.deleteRule(ruleId);
        toast({
          variant: "success",
          title: "Success",
          description: "Rule deleted successfully",
        });
        fetchRules();
      } catch (err) {
        toast({
          variant: "destructive",
          title: "Error",
          description: `Failed to delete rule: ${err.response?.data?.detail || err.message}`,
        });
        console.error('Delete rule error:', err);
      }
    }
  };

  const handleBulkOperation = async (operation) => {
    if (selectedRules.size === 0) return;
    
    const confirmMessage = `Are you sure you want to ${operation} ${selectedRules.size} rule(s)?`;
    if (window.confirm(confirmMessage)) {
      try {
        await rulesService.bulkOperation({
          rule_ids: Array.from(selectedRules),
          operation
        });
        toast({
          variant: "success",
          title: "Success",
          description: `${selectedRules.size} rule(s) ${operation}d successfully`,
        });
        setSelectedRules(new Set());
        fetchRules();
      } catch (err) {
        toast({
          variant: "destructive",
          title: "Error",
          description: `Failed to ${operation} rules: ${err.response?.data?.detail || err.message}`,
        });
        console.error(`Bulk ${operation} error:`, err);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'security',
      rule_type: 'keyword',
      pattern: '',
      severity: 'medium',
      points: 50,
      priority: 0,
      stop_on_match: false,
      combination_logic: 'AND',
      is_active: true
    });
  };

  const handleEditRule = (rule) => {
    setEditingRule(rule);
    setFormData({ ...rule });
    setShowRuleSheet(true);
  };

  const applyTemplate = (template) => {
    setFormData({
      ...formData,
      name: template.name,
      description: template.description,
      category: template.category,
      rule_type: template.rule_type,
      pattern: template.pattern,
      severity: template.severity,
      points: template.points
    });
    setEditingRule(null); // Ensure we're creating, not editing
    setShowTemplatesDialog(false);
    setShowRuleSheet(true); // Open the rule creation drawer
    toast({
      variant: "success",
      title: "Template Applied",
      description: `Template "${template.name}" has been applied to the form`,
    });
  };

  const toggleRuleSelection = (ruleId) => {
    const newSelection = new Set(selectedRules);
    if (newSelection.has(ruleId)) {
      newSelection.delete(ruleId);
    } else {
      newSelection.add(ruleId);
    }
    setSelectedRules(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedRules.size === filteredRules.length) {
      setSelectedRules(new Set());
    } else {
      setSelectedRules(new Set(filteredRules.map(rule => rule.id)));
    }
  };

  const getRuleTypeIcon = (ruleType) => {
    switch (ruleType) {
      case 'keyword': return <FileText className="h-4 w-4" />;
      case 'regex': return <Code className="h-4 w-4" />;
      case 'model_restriction': return <Shield className="h-4 w-4" />;
      case 'custom_scoring': return <Zap className="h-4 w-4" />;
      default: return <Target className="h-4 w-4" />;
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'data_privacy': return <Lock className="h-4 w-4" />;
      case 'security': return <Shield className="h-4 w-4" />;
      case 'compliance': return <Database className="h-4 w-4" />;
      default: return <Globe className="h-4 w-4" />;
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

  const formatRuleType = (ruleType) => {
    return ruleType.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatCategory = (category) => {
    return category.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  // Filter rules
  const filteredRules = rules.filter(rule => {
    if (filters.category !== 'all' && rule.category !== filters.category) return false;
    if (filters.rule_type !== 'all' && rule.rule_type !== filters.rule_type) return false;
    if (filters.severity !== 'all' && rule.severity !== filters.severity) return false;
    if (filters.is_active !== 'all' && rule.is_active.toString() !== filters.is_active) return false;
    if (debouncedSearch && !(rule.name.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
        rule.description?.toLowerCase().includes(debouncedSearch.toLowerCase()))) return false;
    return true;
  });

  if (!isAdmin()) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Detection Rules</h1>
          <p className="text-13 text-gray-600">
            Manage rule-based detection patterns and scoring
          </p>
        </div>
        <Alert>
          <Lock className="h-4 w-4" />
          <AlertDescription>Admin access required to manage detection rules.</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading) {
    return <SkeletonDetectionRules />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Detection Rules</h1>
          <p className="text-13 text-gray-600">
            Manage rule-based detection patterns and risk scoring
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button 
            variant="outline"
            onClick={() => setShowTemplatesDialog(true)}
          >
            <Download className="h-4 w-4 mr-2" />
            Templates
          </Button>
          
          <Button 
            onClick={() => {
              resetForm();
              setEditingRule(null);
              setShowRuleSheet(true);
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Rule
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
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Rule Filters</CardTitle>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">
                {filteredRules.length} of {rules.length} rules
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
                  placeholder="Search rules..."
                  value={filters.search}
                  onChange={(e) => {
                    setFilters({...filters, search: e.target.value});
                    // Page reset will happen when debouncedSearch changes
                  }}
                  className="pl-8"
                />
              </div>
            </div>
            
            <div>
              <label className="text-13 font-medium">Category</label>
              <Select value={filters.category} onValueChange={(value) => {
                setFilters({...filters, category: value});
                setCurrentPage(1);
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="data_privacy">Data Privacy</SelectItem>
                  <SelectItem value="security">Security</SelectItem>
                  <SelectItem value="compliance">Compliance</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Rule Type</label>
              <Select value={filters.rule_type} onValueChange={(value) => {
                setFilters({...filters, rule_type: value});
                setCurrentPage(1);
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="keyword">Keyword</SelectItem>
                  <SelectItem value="regex">Regex</SelectItem>
                  <SelectItem value="model_restriction">Model Restriction</SelectItem>
                  <SelectItem value="custom_scoring">Custom Scoring</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Severity</label>
              <Select value={filters.severity} onValueChange={(value) => {
                setFilters({...filters, severity: value});
                setCurrentPage(1);
              }}>
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
              <Select value={filters.is_active} onValueChange={(value) => {
                setFilters({...filters, is_active: value});
                setCurrentPage(1);
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="true">Active</SelectItem>
                  <SelectItem value="false">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-13 font-medium">Actions</label>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => {
                  setFilters({ category: 'all', rule_type: 'all', severity: 'all', is_active: 'all', search: '' });
                  setCurrentPage(1);
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedRules.size > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {selectedRules.size} rule(s) selected
              </span>
              <div className="flex items-center space-x-2">
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkOperation('enable')}
                >
                  <Unlock className="h-4 w-4 mr-1" />
                  Enable
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkOperation('disable')}
                >
                  <Lock className="h-4 w-4 mr-1" />
                  Disable
                </Button>
                <Button 
                  size="sm" 
                  variant="destructive"
                  onClick={() => handleBulkOperation('delete')}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Rules Table */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Detection Rules ({filteredRules.length})</h2>
        </div>
        
        <div>
          {filteredRules.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectedRules.size === filteredRules.length && filteredRules.length > 0}
                        onCheckedChange={toggleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Rule</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Points</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRules.map((rule) => (
                    <TableRow key={rule.id} className={selectedRules.has(rule.id) ? "bg-muted/50" : ""}>
                      <TableCell>
                        <Checkbox 
                          checked={selectedRules.has(rule.id)}
                          onCheckedChange={() => toggleRuleSelection(rule.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-medium flex items-center space-x-2">
                            {getRuleTypeIcon(rule.rule_type)}
                            <span>{rule.name}</span>
                          </div>
                          {rule.description && (
                            <div className="text-sm text-muted-foreground">
                              {rule.description}
                            </div>
                          )}
                          <div className="text-xs font-mono bg-muted px-2 py-1 rounded max-w-xs truncate">
                            {rule.pattern}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {getCategoryIcon(rule.category)}
                          <span className="text-13">{formatCategory(rule.category)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {formatRuleType(rule.rule_type)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getSeverityBadgeVariant(rule.severity)}>
                          {rule.severity.charAt(0).toUpperCase() + rule.severity.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-center">
                          <span className="font-medium">{rule.points}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-center">
                          <span className="font-medium">{rule.priority}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {rule.is_active ? (
                            <><Unlock className="h-3 w-3 text-green-500" /><span className="text-13 text-green-600">Active</span></>
                          ) : (
                            <><Lock className="h-3 w-3 text-red-500" /><span className="text-13 text-red-600">Inactive</span></>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => handleEditRule(rule)}>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => {
                              setFormData({ ...rule, name: `${rule.name} (Copy)` });
                              setEditingRule(null); // Ensure we're creating, not editing
                              setShowRuleSheet(true);
                            }}>
                              <Copy className="h-4 w-4 mr-2" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDeleteRule(rule.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No rules found</h3>
              <p className="text-muted-foreground mb-4">
                {rules.length === 0 
                  ? 'Get started by creating your first detection rule or using a template.'
                  : 'Try adjusting your filters to see more rules.'}
              </p>
              {rules.length === 0 && (
                <div className="flex justify-center space-x-2">
                  <Button onClick={() => setShowTemplatesDialog(true)}>
                    Browse Templates
                  </Button>
                  <Button variant="outline" onClick={() => setShowRuleSheet(true)}>
                    Create Rule
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Pagination */}
      {rules.length > 0 && totalCount > 0 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          itemName="rules"
          onPageChange={(page) => {
            setCurrentPage(page);
            fetchRules(page);
          }}
          onPageSizeChange={(newPageSize) => {
            setPageSize(newPageSize);
            setCurrentPage(1);
          }}
        />
      )}

      {/* Create/Edit Rule Sheet */}
      <Sheet open={showRuleSheet} onOpenChange={setShowRuleSheet}>
        <SheetContent className="w-[75%] sm:w-[900px] max-w-none overflow-y-auto">
          <SheetHeader>
            <SheetTitle>
              {editingRule ? 'Edit Detection Rule' : 'Create Detection Rule'}
            </SheetTitle>
            <SheetDescription>
              Configure rule patterns, scoring, and execution behavior
            </SheetDescription>
          </SheetHeader>
          
          <div className="border-b border-gray-200 mb-6"></div>
          
          <form onSubmit={handleCreateRule} className="space-y-6 mt-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Rule Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Unique rule name"
                  required
                />
              </div>
              
              <div>
                <label className="text-sm font-medium">Category</label>
                <Select value={formData.category} onValueChange={(value) => setFormData({...formData, category: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="data_privacy">Data Privacy</SelectItem>
                    <SelectItem value="security">Security</SelectItem>
                    <SelectItem value="compliance">Compliance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Description</label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Describe what this rule detects..."
                rows={2}
              />
            </div>

            {/* Rule Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Rule Type</label>
                <Select value={formData.rule_type} onValueChange={(value) => setFormData({...formData, rule_type: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="keyword">Keyword Matching</SelectItem>
                    <SelectItem value="regex">Regex Pattern</SelectItem>
                    <SelectItem value="model_restriction">Model Restriction</SelectItem>
                    <SelectItem value="custom_scoring">Custom Scoring</SelectItem>
                    </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium">Severity</label>
                <Select value={formData.severity} onValueChange={(value) => setFormData({...formData, severity: value})}>
                  <SelectTrigger>
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

            {/* Pattern Configuration */}
            <div>
              <label className="text-sm font-medium">Pattern</label>
              {formData.rule_type === 'keyword' && (
                <div className="space-y-2">
                  <Textarea
                    value={formData.pattern}
                    onChange={(e) => setFormData({...formData, pattern: e.target.value})}
                    placeholder="Enter keywords separated by commas (e.g., password,secret,api_key)"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Keywords are matched case-insensitively. Use commas to separate multiple keywords.
                  </p>
                </div>
              )}
              
              {formData.rule_type === 'regex' && (
                <div className="space-y-2">
                  <Textarea
                    value={formData.pattern}
                    onChange={(e) => setFormData({...formData, pattern: e.target.value})}
                    placeholder="Enter regex pattern (e.g., \\b[0-9]{3}-[0-9]{2}-[0-9]{4}\\b for SSN)"
                    required
                    className="font-mono"
                  />
                  <p className="text-xs text-muted-foreground">
                    Use standard regex syntax. Patterns are case-insensitive by default.
                  </p>
                </div>
              )}
              
              {formData.rule_type === 'model_restriction' && (
                <div className="space-y-2">
                  <Textarea
                    value={formData.pattern}
                    onChange={(e) => setFormData({...formData, pattern: e.target.value})}
                    placeholder="Enter restricted models separated by commas (e.g., gpt-4,claude-opus)"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    List model names that should be flagged when accessed.
                  </p>
                </div>
              )}
              
              {formData.rule_type === 'custom_scoring' && (
                <div className="space-y-2">
                  <Textarea
                    value={formData.pattern}
                    onChange={(e) => setFormData({...formData, pattern: e.target.value})}
                    placeholder="Enter condition (e.g., duration_ms > 30000)"
                    required
                    className="font-mono"
                  />
                  <p className="text-xs text-muted-foreground">
                    Use comparison operators: &gt;, &lt;, &gt;=, &lt;=, ==. Available fields: duration_ms
                  </p>
                </div>
              )}
              
            </div>

            {/* Scoring and Behavior */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium">Risk Points (0-100)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.points}
                  onChange={(e) => setFormData({...formData, points: parseInt(e.target.value) || 0})}
                  required
                />
              </div>
              
              <div>
                <label className="text-sm font-medium">Priority (0-1000)</label>
                <Input
                  type="number"
                  min="0"
                  max="1000"
                  value={formData.priority}
                  onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value) || 0})}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Higher priority rules execute first
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium">Logic</label>
                <Select value={formData.combination_logic} onValueChange={(value) => setFormData({...formData, combination_logic: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="AND">AND (All conditions)</SelectItem>
                    <SelectItem value="OR">OR (Any condition)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Rule Options */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch 
                  checked={formData.stop_on_match}
                  onCheckedChange={(checked) => setFormData({...formData, stop_on_match: checked})}
                />
                <div>
                  <label className="text-sm font-medium">Stop on Match</label>
                  <p className="text-xs text-muted-foreground">
                    Stop processing additional rules after this one matches
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch 
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({...formData, is_active: checked})}
                />
                <div>
                  <label className="text-sm font-medium">Active</label>
                  <p className="text-xs text-muted-foreground">
                    Enable this rule for active detection
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setShowRuleSheet(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                {editingRule ? 'Update Rule' : 'Create Rule'}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>

      {/* Templates Sheet */}
      <Sheet open={showTemplatesDialog} onOpenChange={setShowTemplatesDialog}>
        <SheetContent className="w-[75%] sm:w-[900px] max-w-none overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Rule Templates</SheetTitle>
            <SheetDescription>
              Pre-configured detection rules for common security scenarios
            </SheetDescription>
          </SheetHeader>
          
          <div className="border-b border-gray-200 mb-6"></div>
          
          <div className="grid gap-4 mt-6">
            {templates.map((template, index) => (
              <Card key={index} className="hover:bg-accent/50 cursor-pointer" onClick={() => applyTemplate(template)}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                          {getCategoryIcon(template.category)}
                          <Badge variant="outline">{formatCategory(template.category)}</Badge>
                        </div>
                        <Badge variant={getSeverityBadgeVariant(template.severity)}>
                          {template.severity}
                        </Badge>
                        <div className="flex items-center space-x-1">
                          <Target className="h-3 w-3" />
                          <span className="text-sm font-medium">{template.points} pts</span>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium">{template.name}</h4>
                        <p className="text-sm text-muted-foreground">{template.description}</p>
                      </div>
                      
                      <div className="bg-muted p-2 rounded text-xs font-mono">
                        {template.pattern}
                      </div>
                      
                      {template.examples.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Examples:</p>
                          <div className="flex flex-wrap gap-1">
                            {template.examples.slice(0, 3).map((example, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {example}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <Button size="sm" variant="outline">
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default DetectionRules;