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

// Enterprise types
export interface Enterprise {
  id: number
  category_name: string
  industry_code: string
  industry_name: string
  company_code: string
  company_name: string
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface EnterpriseCreate {
  category_name: string
  industry_code: string
  industry_name: string
  company_code: string
  company_name: string
}

export interface EnterpriseUpdate {
  category_name?: string
  industry_code?: string
  industry_name?: string
  company_code?: string
  company_name?: string
}

// ==================== Financial Data Types ====================

// Balance Sheet
export interface BalanceSheet {
  id: number
  enterprise_id: number
  report_date: string
  report_year: number
  // Assets (values can be string from API Decimal serialization)
  cash: number | string | null
  trading_financial_assets: number | string | null
  accounts_receivable: number | string | null
  inventory: number | string | null
  total_current_assets: number | string | null
  fixed_assets: number | string | null
  total_assets: number | string | null
  // Liabilities
  short_term_borrowings: number | string | null
  accounts_payable: number | string | null
  total_current_liabilities: number | string | null
  long_term_borrowings: number | string | null
  total_liabilities: number | string | null
  // Equity
  paid_in_capital: number | string | null
  retained_earnings: number | string | null
  total_equity: number | string | null
  // Metadata
  data_source: string
  fetched_at: string
  created_at: string
  updated_at: string
}

// Income Statement
export interface IncomeStatement {
  id: number
  enterprise_id: number
  report_date: string
  report_year: number
  // Revenue (values can be string from API Decimal serialization)
  operating_revenue: number | string | null
  operating_cost: number | string | null
  selling_expenses: number | string | null
  admin_expenses: number | string | null
  financial_expenses: number | string | null
  // Profit
  operating_profit: number | string | null
  total_profit: number | string | null
  income_tax: number | string | null
  net_profit: number | string | null
  net_profit_parent: number | string | null
  // Per share
  basic_eps: number | string | null
  diluted_eps: number | string | null
  // Metadata
  data_source: string
  fetched_at: string
  created_at: string
  updated_at: string
}

// Cash Flow Statement
export interface CashFlowStatement {
  id: number
  enterprise_id: number
  report_date: string
  report_year: number
  // Operating activities (values can be string from API Decimal serialization)
  cash_received_sales: number | string | null
  tax_refund_received: number | string | null
  cash_paid_goods: number | string | null
  cash_paid_employees: number | string | null
  cash_paid_taxes: number | string | null
  net_cash_operating: number | string | null
  // Investing activities
  cash_received_investments: number | string | null
  cash_paid_assets: number | string | null
  cash_paid_investments: number | string | null
  net_cash_investing: number | string | null
  // Financing activities
  cash_received_borrowings: number | string | null
  cash_paid_debt: number | string | null
  cash_paid_dividends: number | string | null
  net_cash_financing: number | string | null
  // Summary
  net_cash_increase: number | string | null
  cash_end_period: number | string | null
  // Metadata
  data_source: string
  fetched_at: string
  created_at: string
  updated_at: string
}

// Enterprise Financial Summary
export interface EnterpriseFinancialSummary {
  enterprise_id: number
  company_code: string
  company_name: string
  balance_sheet_count: number
  income_statement_count: number
  cashflow_statement_count: number
  latest_report_date: string | null
}

// Enterprise Financial Detail (complete data for one enterprise)
export interface EnterpriseFinancialDetail {
  enterprise_id: number
  company_code: string
  company_name: string
  balance_sheets: BalanceSheet[]
  income_statements: IncomeStatement[]
  cash_flow_statements: CashFlowStatement[]
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

// Global Financial Statistics
export interface GlobalFinancialStats {
  total_enterprises: number
  enterprises_with_data: number
  data_coverage_rate: number
  balance_sheet_records: number
  income_statement_records: number
  cashflow_statement_records: number
  total_records: number
}

// Enterprise Data Status
export interface EnterpriseDataStatus {
  enterprise_id: number
  company_code: string
  company_name: string
  has_data: boolean
  latest_year: number | null
  earliest_year: number | null
  total_years: number
  expected_years: number
  missing_years: number[]
  need_update: boolean
  status: 'no_data' | 'partial' | 'complete'
}

// Enterprise Detail (with full information)
export interface EnterpriseDetail extends Enterprise {
  english_name?: string
  legal_representative?: string
  registered_capital?: number
  establish_date?: string
  listing_date?: string
  website?: string
  email?: string
  phone?: string
  fax?: string
  registered_address?: string
  office_address?: string
  main_business?: string
  business_scope?: string
  company_profile?: string
}

// ==================== AI Analysis Types ====================

// AI Configuration
export interface AIConfig {
  id: number
  name: string
  provider: string
  model: string
  api_base_url: string
  api_key: string // Masked in responses
  temperature: number
  max_tokens: number
  is_default: boolean
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

export interface AIConfigCreate {
  name: string
  provider: string
  model: string
  api_base_url: string
  api_key: string
  temperature?: number
  max_tokens?: number
  is_default?: boolean
  is_active?: boolean
}

export interface AIConfigUpdate {
  name?: string
  provider?: string
  model?: string
  api_base_url?: string
  api_key?: string
  temperature?: number
  max_tokens?: number
  is_default?: boolean
  is_active?: boolean
}

export interface AIConfigListResponse {
  items: AIConfig[]
  total: number
}

// Report Task
export enum ReportStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface ReportTask {
  id: number
  enterprise_id: number
  enterprise_name?: string
  report_type: string
  status: ReportStatus
  progress: number
  error_message?: string
  result_url?: string
  created_by: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface ReportTaskCreate {
  enterprise_id: number
  report_type: string
  config_id?: number
}

export interface ReportTaskListResponse {
  items: ReportTask[]
  total: number
}