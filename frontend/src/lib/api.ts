import { useState, useEffect, useCallback } from 'react'
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { message } from 'antd'

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8005'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
      message.error('没有权限执行此操作')
    } else if (error.response?.status === 500) {
      message.error('服务器错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

// Generic API hook
export function useApi<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(
    async (config?: AxiosRequestConfig) => {
      setLoading(true)
      setError(null)
      try {
        const response = await apiClient.request<T>({
          url: endpoint,
          ...config,
        })
        setData(response.data)
        return response.data
      } catch (err) {
        const errorMessage = (err as AxiosError<{ detail?: string }>).response?.data?.detail ||
          (err as Error).message ||
          '请求失败'
        setError(errorMessage)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [endpoint]
  )

  return { data, loading, error, execute }
}

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/api/auth/login', { email, password })
    return response.data
  },
  logout: async () => {
    const response = await apiClient.post('/api/auth/logout')
    return response.data
  },
  me: async () => {
    const response = await apiClient.get('/api/auth/me')
    return response.data
  },
  refresh: async (refreshToken: string) => {
    const response = await apiClient.post('/api/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },
}

// Health check
export const healthCheck = async () => {
  const response = await apiClient.get('/health')
  return response.data
}

export default apiClient