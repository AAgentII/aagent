import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

export const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const api = {
  // Workflows
  workflows: {
    list: () => apiClient.get('/workflows'),
    get: (id: string) => apiClient.get(`/workflows/${id}`),
    create: (data: any) => apiClient.post('/workflows', data),
    update: (id: string, data: any) => apiClient.put(`/workflows/${id}`, data),
    delete: (id: string) => apiClient.delete(`/workflows/${id}`),
    validate: (id: string) => apiClient.post(`/workflows/${id}/validate`),
  },

  // Agents
  agents: {
    list: (params?: any) => apiClient.get('/agents', { params }),
    get: (id: string) => apiClient.get(`/agents/${id}`),
    create: (data: any) => apiClient.post('/agents', data),
    update: (id: string, data: any) => apiClient.put(`/agents/${id}`, data),
    delete: (id: string) => apiClient.delete(`/agents/${id}`),
    getRoles: () => apiClient.get('/agents/roles/available'),
    getModels: () => apiClient.get('/agents/models/available'),
    getTools: () => apiClient.get('/agents/tools/available'),
  },

  // Executions
  executions: {
    list: (params?: any) => apiClient.get('/executions', { params }),
    get: (id: string) => apiClient.get(`/executions/${id}`),
    create: (data: any) => apiClient.post('/executions', data),
    cancel: (id: string) => apiClient.post(`/executions/${id}/cancel`),
    getNodes: (id: string) => apiClient.get(`/executions/${id}/nodes`),
  },

  // Health
  health: {
    check: () => apiClient.get('/health'),
    ready: () => apiClient.get('/health/ready'),
  },
};