import axios from 'axios';

// Create API client
export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds for complex queries
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API service functions
export const authService = {
  login: (username, password) =>
    apiClient.post('/auth/login', null, { params: { username, password } }),
  
  getCurrentUser: () => apiClient.get('/auth/me'),
};

export const requestsService = {
  getRequests: (params = {}) => apiClient.get('/requests', { params }),
  
  getRequestById: (id) => apiClient.get(`/requests/${id}`),
  
  getStats: (days = 30) => apiClient.get('/stats/totals', { params: { days } }),
};

export const rulesService = {
  getRules: (params = {}) => apiClient.get('/rules', { params }),
  
  createRule: (ruleData) => apiClient.post('/rules', ruleData),
  
  updateRule: (id, ruleData) => apiClient.put(`/rules/${id}`, ruleData),
  
  deleteRule: (id) => apiClient.delete(`/rules/${id}`),
  
  bulkOperation: (operation) => apiClient.post('/rules/bulk', operation),
  
  getTemplates: () => apiClient.get('/rules/templates'),
};

export const sessionsService = {
  getSessions: (params = {}) => apiClient.get('/sessions', { params }),
  
  getSessionById: (id) => apiClient.get(`/sessions/${id}`),
};

export const alertsService = {
  getAlerts: (params = {}) => apiClient.get('/alerts', { params }),
  
  createAlert: (alertData) => apiClient.post('/alerts', alertData),
  
  updateAlert: (id, alertData) => apiClient.put(`/alerts/${id}`, alertData),
  
  bulkOperation: (operation) => apiClient.post('/alerts/bulk', operation),
  
  getStats: () => apiClient.get('/alerts/stats'),
};

export const healthService = {
  getHealth: () => apiClient.get('/health'),
};

export const settingsService = {
  getSettings: (category = null) => 
    apiClient.get('/settings', { params: category ? { category } : {} }),
    
  updateSetting: (key, value) => 
    apiClient.put(`/settings/${key}`, { value }),
    
  getDatabaseStats: () => apiClient.get('/settings/database/stats'),
  
  manualCleanup: () => apiClient.post('/settings/database/cleanup'),
  
  purgeAllData: () => apiClient.post('/settings/database/purge'),
  
  exportData: (exportRequest) => apiClient.post('/export', exportRequest, {
    responseType: 'blob',
    headers: {
      'Accept': exportRequest.format === 'csv' ? 'text/csv' : 'application/json'
    }
  })
};

export const usersService = {
  getUsers: (params = {}) => apiClient.get('/users', { params }),
  
  createUser: (userData) => apiClient.post('/users', userData),
  
  updateUser: (userId, userData) => apiClient.put(`/users/${userId}`, userData),
  
  deleteUser: (userId) => apiClient.delete(`/users/${userId}`),
  
  changePassword: (passwordData) => apiClient.post('/users/change-password', passwordData),
  
  updateUsername: (newUsername) => apiClient.put('/users/profile/username', { username: newUsername }),
  
  updateProfile: (nameData) => apiClient.put('/users/profile/name', nameData),
  
  adminResetPassword: (userId, newPassword) => apiClient.put(`/users/${userId}/reset-password`, { new_password: newPassword })
};

export const kafkaService = {
  testConnection: (kafkaConfig) => apiClient.post('/kafka/test-connection', kafkaConfig),
  
  saveConfiguration: (kafkaConfig) => apiClient.post('/kafka/save-configuration', kafkaConfig),
  
  toggleDemoData: (enabled, clearData = false) => apiClient.post('/kafka/demo-data/toggle', {
    enabled: enabled,
    clear_existing_data: clearData
  }),
  
  getStatus: () => apiClient.get('/kafka/status')
};

export const demoService = {
  getStatus: () => apiClient.get('/demo/status'),
  
  toggle: (enabled) => apiClient.post('/demo/toggle', { enabled: enabled })
};

export const analyticsService = {
  getVolumeTrends: (filters = {}) => apiClient.get('/analytics/volume-trends', { params: filters }),
  
  getThreatTrends: (filters = {}) => apiClient.get('/analytics/threat-trends', { params: filters }),
  
  getModelUsage: (filters = {}) => apiClient.get('/analytics/model-usage', { params: filters }),
  
  getProviderBreakdown: (filters = {}) => apiClient.get('/analytics/provider-breakdown', { params: filters }),
  
  getKeyMetrics: (filters = {}) => apiClient.get('/analytics/key-metrics', { params: filters }),
  
  getAnomalies: (filters = {}) => apiClient.get('/analytics/anomalies', { params: filters }),
  
  getFilterOptions: () => apiClient.get('/analytics/filter-options'),
  
  exportAnalytics: async (format, filters = {}) => {
    const response = await apiClient.get(`/analytics/export/${format}`, { 
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  },
  
  refreshAggregates: () => apiClient.post('/analytics/refresh-aggregates'),
  
  getForecast: (filters = {}) => apiClient.get('/analytics/forecast', { params: filters })
};