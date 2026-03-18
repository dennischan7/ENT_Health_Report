// User types
export interface User {
  id: number
  email: string
  full_name: string | null
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  email: string
  password: string
  full_name?: string
  role?: 'admin' | 'user'
}

export interface UserUpdate {
  email?: string
  full_name?: string
  role?: 'admin' | 'user'
  is_active?: boolean
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RefreshRequest {
  refresh_token: string
}

export interface RefreshResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// Enterprise types (Phase 2+)
export interface Enterprise {
  id: number
  name: string
  unified_social_credit_code: string | null
  industry: string | null
  scale: string | null
  contact_person: string | null
  contact_phone: string | null
  created_by: number
  created_at: string
  updated_at: string
}

export interface EnterpriseCreate {
  name: string
  unified_social_credit_code?: string
  industry?: string
  scale?: string
  contact_person?: string
  contact_phone?: string
}

export interface EnterpriseUpdate {
  name?: string
  unified_social_credit_code?: string
  industry?: string
  scale?: string
  contact_person?: string
  contact_phone?: string
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ErrorResponse {
  detail: string
  status_code: number
}