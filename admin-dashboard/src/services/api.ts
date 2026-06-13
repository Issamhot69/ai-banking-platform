import axios from 'axios';

const API_BASE = '';

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const authService = {
  login: (email: string, password: string) =>
    api.post('/api/v1/auth/login', { email, password }),
  me: () => api.get('/api/v1/auth/me'),
};

export const statsService = {
  getUsers: () => api.get('/api/v1/auth/users'),
  getAccounts: () => api.get('/api/v1/accounts'),
  getTransactions: (account_id?: string) =>
    api.get('/api/v1/transactions', { params: { account_id: account_id || 'cc0c10cd-4a3f-49c6-b71a-abf91a8f6347', per_page: 50 } }),
};

export default api;
