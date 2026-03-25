"""
Peer Comparison Agent using LangGraph.

This agent performs comprehensive peer comparison analysis for enterprises:
1. Fetches target enterprise information
2. Finds top 10 peers by industry_code (sorted by operating_revenue)
3. Fetches 3-year financial data for all peers
4. Calculates comparison metrics
5. Generates LLM-powered analysis with structured output
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.enterprise import Enterprise
from app.models.financial import BalanceSheet, CashFlowStatement, IncomeStatement
from app.services.llm_service import LLMClient, LLMConfigNotFoundError, LLMError

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Schemas for Structured Output
# =============================================================================


class FinancialMetric(BaseModel):
    """Single financial metric with comparison data."""

    name: str = Field(description="Metric name (e.g., '营业收入', '净利润')")
    target_value: Optional[float] = Field(default=None, description="Target enterprise value")
    peer_average: Optional[float] = Field(default=None, description="Peer average value")
    peer_median: Optional[float] = Field(default=None, description="Peer median value")
    peer_max: Optional[float] = Field(default=None, description="Peer maximum value")
    peer_min: Optional[float] = Field(default=None, description="Peer minimum value")
    target_rank: Optional[int] = Field(default=None, description="Target's rank among peers")
    total_peers: int = Field(default=0, description="Total number of peers compared")
    unit: str = Field(default="元", description="Unit of measurement")


class YearlyFinancials(BaseModel):
    """Financial data for a single year."""

    year: int = Field(description="Fiscal year")
    operating_revenue: Optional[float] = Field(default=None, description="营业收入")
    net_profit: Optional[float] = Field(default=None, description="净利润")
    total_assets: Optional[float] = Field(default=None, description="总资产")
    total_equity: Optional[float] = Field(default=None, description="所有者权益")
    total_liabilities: Optional[float] = Field(default=None, description="负债合计")
    operating_profit: Optional[float] = Field(default=None, description="营业利润")
    basic_eps: Optional[float] = Field(default=None, description="基本每股收益")


class PeerAnalysis(BaseModel):
    """Analysis for a single peer enterprise."""

    company_code: str = Field(description="Stock code")
    company_name: str = Field(description="Company name")
    industry_name: str = Field(description="Industry name")
    operating_revenue: Optional[float] = Field(default=None, description="Latest operating revenue")
    net_profit: Optional[float] = Field(default=None, description="Latest net profit")
    total_assets: Optional[float] = Field(default=None, description="Latest total assets")
    financials_3yr: List[YearlyFinancials] = Field(
        default_factory=list, description="3-year financial data"
    )


class StrengthWeakness(BaseModel):
    """Strength or weakness item."""

    item: str = Field(description="The strength or weakness description")
    evidence: str = Field(description="Supporting evidence from financial data")


class ComparisonReport(BaseModel):
    """Final structured comparison report from LLM analysis."""

    target_company: str = Field(description="Target company name")
    target_code: str = Field(description="Target company stock code")
    industry_name: str = Field(description="Industry name")
    peer_count: int = Field(description="Number of peers compared")

    # Executive Summary
    executive_summary: str = Field(description="2-3 sentence executive summary of the comparison")

    # Strengths and Weaknesses
    strengths: List[StrengthWeakness] = Field(
        default_factory=list, description="Key strengths compared to peers"
    )
    weaknesses: List[StrengthWeakness] = Field(
        default_factory=list, description="Key weaknesses compared to peers"
    )

    # Financial Position Analysis
    financial_position_analysis: Optional[str] = Field(
        default=None, description="Analysis of financial position (资产, 负债, 所有者权益)"
    )

    # Profitability Analysis
    profitability_analysis: Optional[str] = Field(
        default=None, description="Analysis of profitability (营业收入, 净利润, 每股收益)"
    )

    # Growth Analysis
    growth_analysis: Optional[str] = Field(
        default=None, description="Analysis of 3-year growth trends"
    )

    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list, description="Strategic recommendations based on comparison"
    )

    # Risk Indicators
    risk_indicators: List[str] = Field(
        default_factory=list, description="Potential risk indicators identified"
    )


class PeerComparisonResult(BaseModel):
    """Complete result from peer comparison agent including all computed data."""

    # LLM-generated report
    report: ComparisonReport = Field(description="LLM-generated analysis report")

    # Computed data for report generation
    peer_enterprises: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of peer enterprises"
    )
    comparison_metrics: List[Dict[str, Any]] = Field(
        default_factory=list, description="Comparison metrics data"
    )
    target_financials: List[Dict[str, Any]] = Field(
        default_factory=list, description="Target enterprise 3-year financials"
    )
    target_enterprise: Optional[Dict[str, Any]] = Field(
        default=None, description="Target enterprise info"
    )


# =============================================================================
# LangGraph State
# =============================================================================


class PeerComparisonState(TypedDict):
    """State for peer comparison workflow."""

    # Input
    enterprise_id: int
    years: int  # Number of years to analyze (default: 3)

    # Intermediate data
    target_enterprise: Optional[Dict[str, Any]]
    peer_enterprises: List[Dict[str, Any]]
    target_financials: List[Dict[str, Any]]
    peer_financials: Dict[int, List[Dict[str, Any]]]  # enterprise_id -> financials
    comparison_metrics: List[Dict[str, Any]]

    # Final output
    report: Optional[ComparisonReport]

    # Error handling
    error: Optional[str]


# =============================================================================
# Peer Comparison Agent
# =============================================================================


class PeerComparisonAgent:
    """
    LangGraph-based agent for peer comparison analysis.

    This agent uses LangGraph to orchestrate a multi-step workflow:
    1. fetch_target_enterprise - Get target enterprise details
    2. find_top_10_peers - Find peers by industry_code
    3. fetch_peer_financials - Get 3-year financial data
    4. calculate_comparison_metrics - Calculate comparison metrics
    5. generate_llm_analysis - Generate structured analysis report

    Example:
        >>> from sqlalchemy.orm import Session
        >>> from app.services.agents import PeerComparisonAgent
        >>>
        >>> agent = PeerComparisonAgent(db)
        >>> report = agent.run(enterprise_id=1)
        >>> print(report.executive_summary)
    """

    def __init__(self, db: Session, llm_client: Optional[LLMClient] = None):
        """
        Initialize the peer comparison agent.

        Args:
            db: SQLAlchemy database session
            llm_client: Optional LLM client instance. If not provided,
                       will create one when needed.
        """
        self.db = db
        self.llm_client = llm_client or LLMClient()
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the LangGraph workflow."""
        workflow = StateGraph(PeerComparisonState)

        # Add nodes
        workflow.add_node("fetch_target_enterprise", self._fetch_target_enterprise)
        workflow.add_node("find_top_10_peers", self._find_top_10_peers)
        workflow.add_node("fetch_peer_financials", self._fetch_peer_financials)
        workflow.add_node("calculate_comparison_metrics", self._calculate_comparison_metrics)
        workflow.add_node("generate_llm_analysis", self._generate_llm_analysis)

        # Define edges
        workflow.set_entry_point("fetch_target_enterprise")
        workflow.add_edge("fetch_target_enterprise", "find_top_10_peers")
        workflow.add_edge("find_top_10_peers", "fetch_peer_financials")
        workflow.add_edge("fetch_peer_financials", "calculate_comparison_metrics")
        workflow.add_edge("calculate_comparison_metrics", "generate_llm_analysis")
        workflow.add_edge("generate_llm_analysis", END)

        return workflow.compile()

    def run(self, enterprise_id: int, years: int = 3) -> PeerComparisonResult:
        """
        Execute the peer comparison analysis workflow.

        Args:
            enterprise_id: The ID of the target enterprise
            years: Number of years to analyze (default: 3)

        Returns:
            PeerComparisonResult: Complete result with report and computed data

        Raises:
            ValueError: If enterprise not found
            LLMError: If LLM generation fails
        """
        initial_state: PeerComparisonState = {
            "enterprise_id": enterprise_id,
            "years": years,
            "target_enterprise": None,
            "peer_enterprises": [],
            "target_financials": [],
            "peer_financials": {},
            "comparison_metrics": [],
            "report": None,
            "error": None,
        }

        final_state = self.graph.invoke(initial_state)

        if final_state.get("error"):
            raise LLMError(final_state["error"])

        if not final_state.get("report"):
            raise LLMError("Failed to generate comparison report")

        # Return complete result with all computed data
        return PeerComparisonResult(
            report=final_state["report"],
            peer_enterprises=final_state.get("peer_enterprises", []),
            comparison_metrics=final_state.get("comparison_metrics", []),
            target_financials=final_state.get("target_financials", []),
            target_enterprise=final_state.get("target_enterprise"),
        )

    # =========================================================================
    # Workflow Nodes
    # =========================================================================

    def _fetch_target_enterprise(self, state: PeerComparisonState) -> PeerComparisonState:
        """Fetch target enterprise information."""
        enterprise_id = state["enterprise_id"]

        enterprise = self.db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()

        if not enterprise:
            state["error"] = f"Enterprise with ID {enterprise_id} not found"
            return state

        state["target_enterprise"] = {
            "id": enterprise.id,
            "company_code": enterprise.company_code,
            "company_name": enterprise.company_name,
            "industry_code": enterprise.industry_code,
            "industry_name": enterprise.industry_name,
            "category_name": enterprise.category_name,
        }

        logger.info(
            f"Fetched target enterprise: {enterprise.company_name} ({enterprise.company_code})"
        )

        return state

    def _find_top_10_peers(self, state: PeerComparisonState) -> PeerComparisonState:
        """Find top 10 peers by industry_code, sorted by operating revenue."""
        target = state.get("target_enterprise")
        if not target:
            state["error"] = "No target enterprise found"
            return state

        industry_code = target["industry_code"]
        target_id = target["id"]

        # Find enterprises in the same industry, excluding the target
        # Sort by latest operating revenue (descending)
        peers_query = (
            self.db.query(Enterprise)
            .outerjoin(IncomeStatement, Enterprise.id == IncomeStatement.enterprise_id)
            .filter(
                Enterprise.industry_code == industry_code,
                Enterprise.id != target_id,
            )
            .distinct()
        )

        # Get all peers first
        all_peers = peers_query.all()

        # Sort by latest operating revenue
        peers_with_revenue = []
        for peer in all_peers:
            latest_income = (
                self.db.query(IncomeStatement)
                .filter(IncomeStatement.enterprise_id == peer.id)
                .order_by(desc(IncomeStatement.report_date))
                .first()
            )
            revenue = (
                float(latest_income.operating_revenue)
                if latest_income and latest_income.operating_revenue
                else 0
            )
            peers_with_revenue.append((peer, revenue))

        # Sort by revenue descending and take top 10
        peers_with_revenue.sort(key=lambda x: x[1], reverse=True)
        top_10_peers = peers_with_revenue[:10]

        state["peer_enterprises"] = [
            {
                "id": peer.id,
                "company_code": peer.company_code,
                "company_name": peer.company_name,
                "industry_code": peer.industry_code,
                "industry_name": peer.industry_name,
                "operating_revenue": revenue,
            }
            for peer, revenue in top_10_peers
        ]

        logger.info(f"Found {len(state['peer_enterprises'])} peers for industry {industry_code}")

        return state

    def _get_latest_financial_year(self) -> int:
        """
        Query the latest financial data year from database.

        Returns:
            int: The latest year with financial data, or current year - 1 as fallback.
        """
        latest_income = (
            self.db.query(IncomeStatement.report_year)
            .order_by(desc(IncomeStatement.report_year))
            .first()
        )
        if latest_income:
            logger.info(f"Latest financial data year in database: {latest_income[0]}")
            return latest_income[0]
        # Fallback to current year - 1 if no data exists
        fallback_year = date.today().year - 1
        logger.warning(f"No financial data found, using fallback year: {fallback_year}")
        return fallback_year

    def _fetch_peer_financials(self, state: PeerComparisonState) -> PeerComparisonState:
        """Fetch 3-year financial data for target and peers."""
        years = state["years"]
        target = state.get("target_enterprise")
        peers = state.get("peer_enterprises", [])

        if not target:
            state["error"] = "No target enterprise found"
            return state

        # Calculate year range based on actual data availability
        latest_year = self._get_latest_financial_year()
        year_range = list(range(latest_year - years + 1, latest_year + 1))

        # Fetch target financials
        target_financials = self._fetch_enterprise_financials(target["id"], year_range)
        state["target_financials"] = target_financials

        # Fetch peer financials
        peer_financials = {}
        for peer in peers:
            peer_financials[peer["id"]] = self._fetch_enterprise_financials(peer["id"], year_range)

        state["peer_financials"] = peer_financials

        logger.info(f"Fetched financials for target and {len(peers)} peers ({years} years)")
        logger.info(f"Year range: {year_range}")
        logger.info(f"Target financials count: {len(target_financials)}")
        for fin in target_financials:
            has_income = fin.get("income_statement") is not None
            has_balance = fin.get("balance_sheet") is not None
            logger.info(f"  Year {fin.get('year')}: income_statement={has_income}, balance_sheet={has_balance}")

        return state

    def _fetch_enterprise_financials(
        self, enterprise_id: int, year_range: List[int]
    ) -> List[Dict[str, Any]]:
        """Fetch financial data for a single enterprise."""
        financials = []

        for year in year_range:
            # Fetch balance sheet
            balance_sheet = (
                self.db.query(BalanceSheet)
                .filter(
                    BalanceSheet.enterprise_id == enterprise_id,
                    BalanceSheet.report_year == year,
                )
                .first()
            )

            # Fetch income statement
            income_statement = (
                self.db.query(IncomeStatement)
                .filter(
                    IncomeStatement.enterprise_id == enterprise_id,
                    IncomeStatement.report_year == year,
                )
                .first()
            )

            # Fetch cash flow statement
            cash_flow = (
                self.db.query(CashFlowStatement)
                .filter(
                    CashFlowStatement.enterprise_id == enterprise_id,
                    CashFlowStatement.report_year == year,
                )
                .first()
            )

            year_data = {
                "year": year,
                "balance_sheet": self._model_to_dict(balance_sheet) if balance_sheet else None,
                "income_statement": self._model_to_dict(income_statement)
                if income_statement
                else None,
                "cash_flow": self._model_to_dict(cash_flow) if cash_flow else None,
            }

            financials.append(year_data)

        return financials

    def _model_to_dict(self, model: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary, handling Decimals."""
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, Decimal):
                result[column.name] = float(value)
            else:
                result[column.name] = value
        return result

    def _calculate_comparison_metrics(self, state: PeerComparisonState) -> PeerComparisonState:
        """Calculate comparison metrics for key financial indicators."""
        target_financials = state.get("target_financials", [])
        peer_financials = state.get("peer_financials", {})
        peers = state.get("peer_enterprises", [])

        if not target_financials:
            state["error"] = "No target financial data available"
            return state

        # Get latest year data
        latest_year_data = None
        for fin in sorted(target_financials, key=lambda x: x["year"], reverse=True):
            if fin.get("income_statement") or fin.get("balance_sheet"):
                latest_year_data = fin
                break

        if not latest_year_data:
            state["error"] = "No valid financial data for target enterprise"
            return state

        # Define metrics to compare
        metrics_definitions = [
            ("operating_revenue", "营业收入", "income_statement"),
            ("net_profit", "净利润", "income_statement"),
            ("total_assets", "总资产", "balance_sheet"),
            ("total_equity", "所有者权益", "balance_sheet"),
            ("total_liabilities", "负债合计", "balance_sheet"),
            ("operating_profit", "营业利润", "income_statement"),
            ("basic_eps", "基本每股收益", "income_statement"),
        ]

        comparison_metrics = []

        for field_name, display_name, statement_type in metrics_definitions:
            metric = self._calculate_single_metric(
                field_name=field_name,
                display_name=display_name,
                statement_type=statement_type,
                target_financials=target_financials,
                peer_financials=peer_financials,
                peers=peers,
            )
            comparison_metrics.append(metric)
            logger.debug(f"Metric {display_name}: target={metric.get('target_value')}, avg={metric.get('peer_average')}")

        state["comparison_metrics"] = comparison_metrics

        logger.info(f"Calculated {len(comparison_metrics)} comparison metrics")

        return state

    def _calculate_single_metric(
        self,
        field_name: str,
        display_name: str,
        statement_type: str,
        target_financials: List[Dict[str, Any]],
        peer_financials: Dict[int, List[Dict[str, Any]]],
        peers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate a single comparison metric."""
        # Get target value (latest year)
        target_value = None
        for fin in sorted(target_financials, key=lambda x: x["year"], reverse=True):
            statement = fin.get(statement_type)
            if statement and statement.get(field_name) is not None:
                target_value = statement[field_name]
                break

        # Get peer values
        peer_values = []
        for peer in peers:
            peer_id = peer["id"]
            peer_fin_list = peer_financials.get(peer_id, [])
            for fin in sorted(peer_fin_list, key=lambda x: x["year"], reverse=True):
                statement = fin.get(statement_type)
                if statement and statement.get(field_name) is not None:
                    peer_values.append(statement[field_name])
                    break

        # Calculate statistics
        peer_average = sum(peer_values) / len(peer_values) if peer_values else None
        peer_sorted = sorted(peer_values)
        peer_median = peer_sorted[len(peer_sorted) // 2] if peer_sorted else None
        peer_max = max(peer_values) if peer_values else None
        peer_min = min(peer_values) if peer_values else None

        # Calculate rank
        target_rank = None
        if target_value is not None and peer_values:
            all_values = peer_values + [target_value]
            all_values_sorted = sorted(all_values, reverse=True)
            target_rank = all_values_sorted.index(target_value) + 1

        return {
            "name": display_name,
            "field_name": field_name,
            "target_value": target_value / 10000 if target_value else None,  # Convert to 万元
            "peer_average": peer_average / 10000 if peer_average else None,  # Convert to 万元
            "peer_median": peer_median / 10000 if peer_median else None,  # Convert to 万元
            "peer_max": peer_max / 10000 if peer_max else None,  # Convert to 万元
            "peer_min": peer_min / 10000 if peer_min else None,  # Convert to 万元
            "target_rank": target_rank,
            "total_peers": len(peers),
            "unit": "万元" if field_name != "basic_eps" else "元/股",
        }

    def _generate_llm_analysis(self, state: PeerComparisonState) -> PeerComparisonState:
        """Generate structured LLM analysis report."""
        target = state.get("target_enterprise")
        peers = state.get("peer_enterprises", [])
        target_financials = state.get("target_financials", [])
        peer_financials = state.get("peer_financials", {})
        comparison_metrics = state.get("comparison_metrics", [])

        if not target:
            state["error"] = "No target enterprise found for analysis"
            return state

        try:
            # Prepare context for LLM
            context = self._prepare_llm_context(
                target=target,
                peers=peers,
                target_financials=target_financials,
                peer_financials=peer_financials,
                comparison_metrics=comparison_metrics,
            )

            # Build prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(context)

            # Generate structured output
            report = self.llm_client.generate_structured_from_config(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                schema=ComparisonReport,
                db=self.db,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            state["report"] = report

            logger.info(f"Generated LLM analysis report for {target['company_name']}")

        except LLMConfigNotFoundError as e:
            state["error"] = f"LLM configuration not found: {str(e)}"
            logger.error(state["error"])
        except LLMError as e:
            state["error"] = f"LLM generation failed: {str(e)}"
            logger.error(state["error"])
        except Exception as e:
            state["error"] = f"Unexpected error during LLM analysis: {str(e)}"
            logger.exception("Unexpected error in LLM analysis")

        return state

    def _prepare_llm_context(
        self,
        target: Dict[str, Any],
        peers: List[Dict[str, Any]],
        target_financials: List[Dict[str, Any]],
        peer_financials: Dict[int, List[Dict[str, Any]]],
        comparison_metrics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare context data for LLM analysis."""
        # Helper function to convert to 万元
        def to_wan(value):
            return value / 10000 if value else None

        # Build 3-year financial summary for target
        target_3yr = []
        for fin in sorted(target_financials, key=lambda x: x["year"]):
            income = fin.get("income_statement") or {}
            balance = fin.get("balance_sheet") or {}

            target_3yr.append(
                {
                    "year": fin["year"],
                    "operating_revenue": to_wan(income.get("operating_revenue")),
                    "net_profit": to_wan(income.get("net_profit")),
                    "total_assets": to_wan(balance.get("total_assets")),
                    "total_equity": to_wan(balance.get("total_equity")),
                    "total_liabilities": to_wan(balance.get("total_liabilities")),
                    "operating_profit": to_wan(income.get("operating_profit")),
                    "basic_eps": income.get("basic_eps"),  # Keep as is (元/股)
                }
            )

        # Build peer summaries
        peer_summaries = []
        for peer in peers:
            peer_fin_list = peer_financials.get(peer["id"], [])

            # Get 3-year data for peer
            peer_3yr = []
            for fin in sorted(peer_fin_list, key=lambda x: x["year"]):
                income = fin.get("income_statement") or {}
                balance = fin.get("balance_sheet") or {}

                peer_3yr.append(
                    {
                        "year": fin["year"],
                        "operating_revenue": to_wan(income.get("operating_revenue")),
                        "net_profit": to_wan(income.get("net_profit")),
                        "total_assets": to_wan(balance.get("total_assets")),
                        "total_equity": to_wan(balance.get("total_equity")),
                    }
                )

            peer_summaries.append(
                {
                    "company_code": peer["company_code"],
                    "company_name": peer["company_name"],
                    "operating_revenue": to_wan(peer.get("operating_revenue")),
                    "financials_3yr": peer_3yr,
                }
            )

        return {
            "target": {
                "company_code": target["company_code"],
                "company_name": target["company_name"],
                "industry_name": target["industry_name"],
                "financials_3yr": target_3yr,
            },
            "peers": peer_summaries,
            "comparison_metrics": comparison_metrics,
            "peer_count": len(peers),
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for LLM analysis."""
        return """你是一位资深的企业财务分析师，专长于上市公司同业对比分析和投资价值评估。

你的任务是分析目标企业与同行业企业的财务数据对比，生成专业、深入的分析报告。

## 分析框架要求

### 1. 财务状况分析（至少3个维度）
- 资产结构：总资产、净资产、负债规模及变化趋势
- 资产质量：资产负债率、流动比率、速动比率
- 权益结构：所有者权益占比、留存收益情况

### 2. 盈利能力分析（至少3个维度）
- 收入规模：营业收入及增长率
- 利润水平：净利润、毛利率、净利率
- 股东回报：ROE、ROA、每股收益

### 3. 成长性分析（基于3年数据）
- 收入增长趋势及驱动因素
- 利润增长趋势及可持续性
- 资产扩张节奏

### 4. 竞争优劣势分析（SWOT框架）
- 优势（Strengths）：相对同业的领先指标
- 劣势（Weaknesses）：落后于同业的指标
- 机会（Opportunities）：行业趋势带来的机遇
- 威胁（Threats）：潜在的竞争风险

## 输出质量要求

1. **数据支撑**：每个分析点必须引用具体数据
   - 正确示例："营业收入123.45亿元，同比增长12.3%，高于行业平均8.5%的增速"
   - 错误示例："营业收入表现良好"

2. **逻辑链条**：结论必须有推理过程
   - 正确示例："资产负债率65%，高于行业平均55%，主要由于近两年大规模扩产投资，需关注偿债压力"
   - 错误示例："资产负债率较高"

3. **对比视角**：始终与同业进行对比
   - 排名位置（如"营业收入排名第3/11"）
   - 与平均水平的偏离程度
   - 与行业龙头差距

4. **风险识别**：指出具体的财务风险点
   - 流动性风险指标
   - 盈利能力下降信号
   - 资产质量预警

## 输出格式要求

- 使用专业但易懂的语言
- 每个分析维度单独成段
- 关键数据和结论用数据标注
- 建议具有可操作性"""

    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        """Build the user prompt with context data."""
        target = context["target"]
        peers = context["peers"]
        metrics = context["comparison_metrics"]

        # Format metrics with ranking context
        metrics_text = "## 关键指标对比分析\n\n"
        metrics_text += "| 指标 | 目标企业 | 行业平均 | 行业中位 | 排名 | 评价 |\n"
        metrics_text += "|------|----------|----------|----------|------|------|\n"

        for m in metrics:
            target_val = f"{m['target_value']:,.2f}" if m['target_value'] is not None else "N/A"
            avg_val = f"{m['peer_average']:,.2f}" if m['peer_average'] is not None else "N/A"
            med_val = f"{m['peer_median']:,.2f}" if m['peer_median'] is not None else "N/A"

            # Calculate position
            total = m['total_peers'] + 1
            rank_str = f"{m['target_rank']}/{total}" if m['target_rank'] else "N/A"

            # Performance indicator
            if m['target_value'] and m['peer_average']:
                diff_pct = (m['target_value'] / m['peer_average'] - 1) * 100
                if diff_pct > 20:
                    indicator = "显著领先"
                elif diff_pct > 0:
                    indicator = "略高于平均"
                elif diff_pct > -20:
                    indicator = "略低于平均"
                else:
                    indicator = "明显落后"
            else:
                indicator = "-"

            metrics_text += f"| {m['name']} | {target_val} {m['unit']} | {avg_val} {m['unit']} | {med_val} {m['unit']} | {rank_str} | {indicator} |\n"

        # Format target 3-year data with growth rates
        target_3yr_text = "## 目标企业近3年财务数据及变化趋势（单位：万元）\n\n"

        financials = target["financials_3yr"]
        if len(financials) >= 2:
            target_3yr_text += "| 年份 | 营业收入 | 同比增长 | 净利润 | 同比增长 | 总资产 | 所有者权益 |\n"
            target_3yr_text += "|------|----------|----------|--------|----------|--------|------------|\n"

            prev_rev = None
            prev_profit = None

            for fin in financials:
                rev = fin.get("operating_revenue")
                profit = fin.get("net_profit")
                assets = fin.get("total_assets")
                equity = fin.get("total_equity")

                rev_str = f"{rev:,.2f}" if rev else "N/A"
                profit_str = f"{profit:,.2f}" if profit else "N/A"
                assets_str = f"{assets:,.2f}" if assets else "N/A"
                equity_str = f"{equity:,.2f}" if equity else "N/A"

                # Calculate growth rates
                rev_growth = f"{(rev/prev_rev-1)*100:+.1f}%" if rev and prev_rev else "-"
                profit_growth = f"{(profit/prev_profit-1)*100:+.1f}%" if profit and prev_profit else "-"

                target_3yr_text += f"| {fin['year']} | {rev_str} | {rev_growth} | {profit_str} | {profit_growth} | {assets_str} | {equity_str} |\n"

                prev_rev = rev
                prev_profit = profit
        else:
            for fin in financials:
                target_3yr_text += f"### {fin['year']}年\n"
                rev = fin.get("operating_revenue")
                profit = fin.get("net_profit")
                assets = fin.get("total_assets")
                equity = fin.get("total_equity")

                rev_str = f"{rev:,.2f}" if rev is not None else "N/A"
                profit_str = f"{profit:,.2f}" if profit is not None else "N/A"
                assets_str = f"{assets:,.2f}" if assets is not None else "N/A"
                equity_str = f"{equity:,.2f}" if equity is not None else "N/A"

                target_3yr_text += f"- 营业收入: {rev_str} 万元\n"
                target_3yr_text += f"- 净利润: {profit_str} 万元\n"
                target_3yr_text += f"- 总资产: {assets_str} 万元\n"
                target_3yr_text += f"- 所有者权益: {equity_str} 万元\n\n"

        # Format peer summaries with ranking
        peers_text = f"## 同业对比企业详情 ({len(peers)}家，单位：万元)\n\n"
        peers_text += "| 排名 | 公司名称 | 股票代码 | 最新营业收入 | 净利润 |\n"
        peers_text += "|------|----------|----------|--------------|--------|\n"

        for i, peer in enumerate(peers, 1):
            peer_rev = peer.get("operating_revenue")
            peer_rev_str = f"{peer_rev:,.2f}" if peer_rev is not None else "N/A"

            # Get latest profit from financials
            latest_fin = peer.get("financials_3yr", [])[-1] if peer.get("financials_3yr") else {}
            peer_profit = latest_fin.get("net_profit")
            peer_profit_str = f"{peer_profit:,.2f}" if peer_profit is not None else "N/A"

            peers_text += f"| {i} | {peer['company_name']} | {peer['company_code']} | {peer_rev_str} | {peer_profit_str} |\n"

        prompt = f"""请对以下企业进行深入的同业对比分析：

# 目标企业
- 名称: {target["company_name"]}
- 股票代码: {target["company_code"]}
- 所属行业: {target["industry_name"]}

{target_3yr_text}

{peers_text}

{metrics_text}

请按照分析框架要求，生成专业深入的同业对比分析报告。每个分析点必须引用具体数据，结论必须有逻辑支撑。"""

        return prompt
