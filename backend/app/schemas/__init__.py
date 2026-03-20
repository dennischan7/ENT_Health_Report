"""
Pydantic schemas package.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.enterprise import (
    EnterpriseBase,
    EnterpriseCreate,
    EnterpriseUpdate,
    EnterpriseResponse,
    EnterpriseListResponse,
)
from app.schemas.financial import (
    BalanceSheetBase,
    BalanceSheetResponse,
    BalanceSheetListResponse,
    IncomeStatementBase,
    IncomeStatementResponse,
    IncomeStatementListResponse,
    CashFlowStatementBase,
    CashFlowStatementResponse,
    CashFlowStatementListResponse,
    EnterpriseFinancialSummary,
    EnterpriseFinancialSummaryList,
    EnterpriseFinancialDetail,
)
from app.schemas.ai_config import (
    AIProvider,
    AIConfigBase,
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    AIConfigListResponse,
)
from app.schemas.report import (
    ReportData,
    ReportGenerateRequest,
    GeneratedReportResponse,
    GeneratedReportListResponse,
    FinancialMetric,
    YearlyMetric,
    TrendData,
    ExecutiveSummary,
    FinancialMetricsSection,
    ChartData,
    PeerComparisonSection,
    RiskAssessmentSection,
    RecommendationsSection,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "TokenResponse",
    # Enterprise schemas
    "EnterpriseBase",
    "EnterpriseCreate",
    "EnterpriseUpdate",
    "EnterpriseResponse",
    "EnterpriseListResponse",
    # Financial schemas
    "BalanceSheetBase",
    "BalanceSheetResponse",
    "BalanceSheetListResponse",
    "IncomeStatementBase",
    "IncomeStatementResponse",
    "IncomeStatementListResponse",
    "CashFlowStatementBase",
    "CashFlowStatementResponse",
    "CashFlowStatementListResponse",
    "EnterpriseFinancialSummary",
    "EnterpriseFinancialSummaryList",
    "EnterpriseFinancialDetail",
    # AI Config schemas
    "AIProvider",
    "AIConfigBase",
    "AIConfigCreate",
    "AIConfigUpdate",
    "AIConfigResponse",
    "AIConfigListResponse",
    # Report schemas
    "ReportData",
    "ReportGenerateRequest",
    "GeneratedReportResponse",
    "GeneratedReportListResponse",
    "FinancialMetric",
    "YearlyMetric",
    "TrendData",
    "ExecutiveSummary",
    "FinancialMetricsSection",
    "ChartData",
    "PeerComparisonSection",
    "RiskAssessmentSection",
    "RecommendationsSection",
]
