"""
Financial data schemas for request/response validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Balance Sheet Schemas ====================


class BalanceSheetBase(BaseModel):
    """Base balance sheet schema."""

    report_date: date = Field(..., description="报告日期")
    report_year: int = Field(..., description="报告年度")

    # Assets
    cash: Optional[Decimal] = Field(None, description="货币资金")
    trading_financial_assets: Optional[Decimal] = Field(None, description="交易性金融资产")
    accounts_receivable: Optional[Decimal] = Field(None, description="应收账款")
    inventory: Optional[Decimal] = Field(None, description="存货")
    total_current_assets: Optional[Decimal] = Field(None, description="流动资产合计")
    fixed_assets: Optional[Decimal] = Field(None, description="固定资产")
    total_assets: Optional[Decimal] = Field(None, description="资产总计")

    # Liabilities
    short_term_borrowings: Optional[Decimal] = Field(None, description="短期借款")
    accounts_payable: Optional[Decimal] = Field(None, description="应付账款")
    total_current_liabilities: Optional[Decimal] = Field(None, description="流动负债合计")
    long_term_borrowings: Optional[Decimal] = Field(None, description="长期借款")
    total_liabilities: Optional[Decimal] = Field(None, description="负债合计")

    # Equity
    paid_in_capital: Optional[Decimal] = Field(None, description="实收资本")
    retained_earnings: Optional[Decimal] = Field(None, description="未分配利润")
    total_equity: Optional[Decimal] = Field(None, description="所有者权益合计")


class BalanceSheetResponse(BalanceSheetBase):
    """Schema for balance sheet response."""

    id: int
    enterprise_id: int
    data_source: str
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceSheetListResponse(BaseModel):
    """Schema for paginated balance sheet list."""

    items: List[BalanceSheetResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ==================== Income Statement Schemas ====================


class IncomeStatementBase(BaseModel):
    """Base income statement schema."""

    report_date: date = Field(..., description="报告日期")
    report_year: int = Field(..., description="报告年度")

    # Revenue
    operating_revenue: Optional[Decimal] = Field(None, description="营业收入")
    operating_cost: Optional[Decimal] = Field(None, description="营业成本")
    selling_expenses: Optional[Decimal] = Field(None, description="销售费用")
    admin_expenses: Optional[Decimal] = Field(None, description="管理费用")
    financial_expenses: Optional[Decimal] = Field(None, description="财务费用")

    # Profit
    operating_profit: Optional[Decimal] = Field(None, description="营业利润")
    total_profit: Optional[Decimal] = Field(None, description="利润总额")
    income_tax: Optional[Decimal] = Field(None, description="所得税费用")
    net_profit: Optional[Decimal] = Field(None, description="净利润")
    net_profit_parent: Optional[Decimal] = Field(None, description="归母净利润")

    # Per share
    basic_eps: Optional[Decimal] = Field(None, description="基本每股收益")
    diluted_eps: Optional[Decimal] = Field(None, description="稀释每股收益")


class IncomeStatementResponse(IncomeStatementBase):
    """Schema for income statement response."""

    id: int
    enterprise_id: int
    data_source: str
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncomeStatementListResponse(BaseModel):
    """Schema for paginated income statement list."""

    items: List[IncomeStatementResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ==================== Cash Flow Statement Schemas ====================


class CashFlowStatementBase(BaseModel):
    """Base cash flow statement schema."""

    report_date: date = Field(..., description="报告日期")
    report_year: int = Field(..., description="报告年度")

    # Operating activities
    cash_received_sales: Optional[Decimal] = Field(None, description="销售商品收到的现金")
    tax_refund_received: Optional[Decimal] = Field(None, description="收到的税费返还")
    cash_paid_goods: Optional[Decimal] = Field(None, description="购买商品支付的现金")
    cash_paid_employees: Optional[Decimal] = Field(None, description="支付给职工的现金")
    cash_paid_taxes: Optional[Decimal] = Field(None, description="支付的各项税费")
    net_cash_operating: Optional[Decimal] = Field(None, description="经营活动现金流净额")

    # Investing activities
    cash_received_investments: Optional[Decimal] = Field(None, description="收回投资收到的现金")
    cash_paid_assets: Optional[Decimal] = Field(None, description="购建固定资产支付的现金")
    cash_paid_investments: Optional[Decimal] = Field(None, description="投资支付的现金")
    net_cash_investing: Optional[Decimal] = Field(None, description="投资活动现金流净额")

    # Financing activities
    cash_received_borrowings: Optional[Decimal] = Field(None, description="取得借款收到的现金")
    cash_paid_debt: Optional[Decimal] = Field(None, description="偿还债务支付的现金")
    cash_paid_dividends: Optional[Decimal] = Field(None, description="分配股利支付的现金")
    net_cash_financing: Optional[Decimal] = Field(None, description="筹资活动现金流净额")

    # Summary
    net_cash_increase: Optional[Decimal] = Field(None, description="现金净增加额")
    cash_end_period: Optional[Decimal] = Field(None, description="期末现金余额")


class CashFlowStatementResponse(CashFlowStatementBase):
    """Schema for cash flow statement response."""

    id: int
    enterprise_id: int
    data_source: str
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CashFlowStatementListResponse(BaseModel):
    """Schema for paginated cash flow statement list."""

    items: List[CashFlowStatementResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ==================== Combined Financial Data Response ====================


class EnterpriseFinancialSummary(BaseModel):
    """Summary of enterprise with financial data availability."""

    enterprise_id: int
    company_code: str
    company_name: str
    balance_sheet_count: int = Field(0, description="资产负债表数量")
    income_statement_count: int = Field(0, description="利润表数量")
    cashflow_statement_count: int = Field(0, description="现金流量表数量")
    latest_report_date: Optional[date] = Field(None, description="最新报告日期")


class EnterpriseFinancialSummaryList(BaseModel):
    """Paginated list of enterprise financial summary."""

    items: List[EnterpriseFinancialSummary]
    total: int
    page: int
    page_size: int
    pages: int


class EnterpriseFinancialDetail(BaseModel):
    """Complete financial data for an enterprise."""

    enterprise_id: int
    company_code: str
    company_name: str
    balance_sheets: List[BalanceSheetResponse]
    income_statements: List[IncomeStatementResponse]
    cash_flow_statements: List[CashFlowStatementResponse]
