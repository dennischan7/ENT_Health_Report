"""
Report schemas for request/response validation and report data structure.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.report import ReportType, ReportStatus


# ==================== Financial Metric Schemas ====================


class FinancialMetric(BaseModel):
    """Single financial metric with value and change."""

    name: str = Field(..., description="指标名称")
    value: Optional[Decimal] = Field(None, description="当前值")
    unit: str = Field("元", description="单位")
    change_rate: Optional[Decimal] = Field(None, description="同比增长率(%)")
    industry_avg: Optional[Decimal] = Field(None, description="行业平均值")
    industry_rank: Optional[int] = Field(None, description="行业排名")


class YearlyMetric(BaseModel):
    """Metric value for a single year."""

    year: int = Field(..., description="年份")
    value: Optional[Decimal] = Field(None, description="值")


class TrendData(BaseModel):
    """Multi-year trend data for a metric."""

    metric_name: str = Field(..., description="指标名称")
    unit: str = Field("元", description="单位")
    data: List[YearlyMetric] = Field(default_factory=list, description="年度数据")


# ==================== Report Section Data Schemas ====================


class ExecutiveSummary(BaseModel):
    """Executive summary section."""

    overall_rating: str = Field(..., description="综合评级 (优/良/中/差)")
    overall_score: Optional[Decimal] = Field(None, description="综合得分(0-100)")
    summary_text: str = Field(..., description="摘要文字")
    key_strengths: List[str] = Field(default_factory=list, description="主要优势")
    key_risks: List[str] = Field(default_factory=list, description="主要风险")
    recommendation: str = Field(..., description="综合建议")


class FinancialMetricsSection(BaseModel):
    """Financial metrics table section."""

    profitability: List[FinancialMetric] = Field(default_factory=list, description="盈利能力指标")
    solvency: List[FinancialMetric] = Field(default_factory=list, description="偿债能力指标")
    operation: List[FinancialMetric] = Field(default_factory=list, description="运营能力指标")
    growth: List[FinancialMetric] = Field(default_factory=list, description="成长能力指标")


class ChartData(BaseModel):
    """Chart data for embedding in report."""

    chart_type: str = Field(..., description="图表类型 (bar/line/pie)")
    title: str = Field(..., description="图表标题")
    x_labels: List[str] = Field(default_factory=list, description="X轴标签")
    datasets: List[Dict[str, Any]] = Field(default_factory=list, description="数据集")


class PeerCompany(BaseModel):
    """Peer company for comparison."""

    company_code: str = Field(..., description="公司代码")
    company_name: str = Field(..., description="公司名称")
    industry_name: str = Field(..., description="所属行业")


class PeerComparisonSection(BaseModel):
    """Peer comparison analysis section."""

    peer_companies: List[PeerCompany] = Field(default_factory=list, description="对比公司列表")
    comparison_metrics: List[FinancialMetric] = Field(default_factory=list, description="对比指标")
    analysis_text: str = Field(..., description="分析文字")
    ranking_in_industry: Optional[int] = Field(None, description="行业排名")


class RiskAssessmentSection(BaseModel):
    """Risk assessment section."""

    overall_risk_level: str = Field(..., description="整体风险等级 (低/中/高)")
    financial_risk: str = Field(..., description="财务风险分析")
    operational_risk: str = Field(..., description="经营风险分析")
    market_risk: str = Field(..., description="市场风险分析")
    risk_warnings: List[str] = Field(default_factory=list, description="风险预警事项")


class RecommendationsSection(BaseModel):
    """Recommendations section."""

    strategic_recommendations: List[str] = Field(default_factory=list, description="战略建议")
    financial_recommendations: List[str] = Field(default_factory=list, description="财务建议")
    operational_recommendations: List[str] = Field(default_factory=list, description="经营建议")
    action_items: List[str] = Field(default_factory=list, description="行动事项")


# ==================== Full Report Data Schema ====================


class ReportData(BaseModel):
    """
    Complete report data structure for generation.

    This is the main data structure that the ReportGenerator uses
    to generate a Word document report.
    """

    # Enterprise information
    enterprise_id: int = Field(..., description="企业ID")
    company_code: str = Field(..., description="公司代码")
    company_name: str = Field(..., description="公司名称")
    industry_name: str = Field(..., description="所属行业")

    # Report metadata
    report_type: ReportType = Field(ReportType.FULL_DIAGNOSIS, description="报告类型")
    report_years: str = Field(..., description="报告年度范围 (e.g., '2021-2023')")
    report_date: date = Field(default_factory=date.today, description="报告日期")

    # Report sections
    executive_summary: ExecutiveSummary = Field(..., description="执行摘要")
    financial_metrics: FinancialMetricsSection = Field(..., description="财务指标")

    # Chart data
    bar_charts: List[ChartData] = Field(default_factory=list, description="柱状图数据")
    line_charts: List[ChartData] = Field(default_factory=list, description="折线图数据")

    # Trend data for line charts
    trends: List[TrendData] = Field(default_factory=list, description="趋势数据")

    # Analysis sections
    peer_comparison: Optional[PeerComparisonSection] = Field(None, description="同业对比")
    risk_assessment: RiskAssessmentSection = Field(..., description="风险评估")
    recommendations: RecommendationsSection = Field(..., description="建议")


# ==================== Report Request/Response Schemas ====================


class ReportGenerateRequest(BaseModel):
    """Request to generate a new report."""

    enterprise_id: int = Field(..., description="企业ID")
    report_type: ReportType = Field(ReportType.FULL_DIAGNOSIS, description="报告类型")
    report_years: Optional[str] = Field(None, description="报告年度范围 (e.g., '2021-2023')")
    include_peer_comparison: bool = Field(True, description="是否包含同业对比")
    peer_count: int = Field(5, ge=1, le=10, description="同业对比公司数量")


class GeneratedReportResponse(BaseModel):
    """Response for a generated report."""

    id: int
    enterprise_id: int
    enterprise_code: Optional[str] = Field(None, description="企业代码")
    enterprise_name: Optional[str] = Field(None, description="企业名称")
    task_id: Optional[str] = Field(None, description="任务ID")
    report_type: ReportType
    report_title: str
    report_years: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    status: ReportStatus
    progress: Optional[int] = Field(None, description="进度百分比")
    error_message: Optional[str]
    generated_by: Optional[int]
    generation_time_seconds: Optional[float]
    llm_model_used: Optional[str]
    tokens_used: Optional[int]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    model_config = {"from_attributes": True}


class GeneratedReportListResponse(BaseModel):
    """Paginated list of generated reports."""

    items: List[GeneratedReportResponse]
    total: int
    page: int
    page_size: int
    pages: int
