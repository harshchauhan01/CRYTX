import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8001/api';

const api = axios.create({ baseURL: API_BASE });

// Auto-attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('crytx_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('crytx_refresh_token');
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh/`, { refresh });
          localStorage.setItem('crytx_access_token', res.data.access);
          original.headers.Authorization = `Bearer ${res.data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem('crytx_access_token');
          localStorage.removeItem('crytx_refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE };
