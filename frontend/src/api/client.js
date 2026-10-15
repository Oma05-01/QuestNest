// src/api/client.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const activeWorkspaceId = localStorage.getItem('active_org_id');

  const headers = {
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...(activeWorkspaceId && { 'X-Workspace-ID': activeWorkspaceId }),
    ...options.headers,
  };

  // Only default to JSON when body is NOT FormData and Content-Type is unset
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }

  return response;
}