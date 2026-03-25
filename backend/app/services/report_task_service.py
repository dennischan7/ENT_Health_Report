"""
Report Task Service for async report generation.

This module provides functionality to manage async report generation tasks
using FastAPI BackgroundTasks and Redis for status tracking.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.enterprise import Enterprise
from app.models.report import GeneratedReport, ReportStatus, ReportType
from app.services.task_manager import TaskManager, TaskStatus
from app.services.agents.peer_comparison_agent import (
    PeerComparisonAgent,
    ComparisonReport,
    PeerComparisonResult,
)
from app.services.report_generator import ReportGenerator
from app.schemas.report import (
    ReportData,
    FinancialMetric,
    TrendData,
    YearlyMetric,
    ChartData,
    ExecutiveSummary,
    FinancialMetricsSection,
    PeerComparisonSection,
    PeerCompany,
    RiskAssessmentSection,
    RecommendationsSection,
)


logger = logging.getLogger(__name__)


class ReportTaskService:
    """
    Service for managing async report generation tasks.

    This service handles:
    - Starting async report generation via FastAPI BackgroundTasks
    - Tracking task status in Redis
    - Coordinating PeerComparisonAgent and ReportGenerator
    - Error handling and status updates

    Example:
        >>> service = ReportTaskService()
        >>> task_id = await service.start_report_generation(
        ...     enterprise_id=1,
        ...     user_id=1,
        ...     background_tasks=background_tasks,
        ... )
        >>> # Check status later
        >>> status = service.get_task_status(task_id)
        >>> print(status["status"])  # "completed"
    """

    TASK_TYPE = "report_generation"

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the report task service.

        Args:
            redis_url: Optional Redis URL. Defaults to settings.REDIS_URL.
        """
        self.task_manager = TaskManager(redis_url)

    async def start_report_generation(
        self,
        enterprise_id: int,
        user_id: int,
        background_tasks: BackgroundTasks,
        year: Optional[int] = None,
    ) -> str:
        """
        Start async report generation and return task ID.

        This method:
        1. Creates a task record in Redis
        2. Schedules the actual generation as a background task
        3. Returns immediately with the task ID

        Args:
            enterprise_id: The ID of the enterprise to analyze.
            user_id: The ID of the user requesting the report.
            background_tasks: FastAPI BackgroundTasks instance.
            year: Optional fiscal year for analysis.

        Returns:
            The task ID for tracking progress.
        """
        # Create task in Redis
        task_id = self.task_manager.create_task(
            task_type=self.TASK_TYPE,
            enterprise_id=enterprise_id,
            user_id=user_id,
            metadata={"year": year},
        )

        logger.info(
            f"Created report generation task {task_id} for "
            f"enterprise {enterprise_id}, user {user_id}"
        )

        # Schedule background task
        background_tasks.add_task(
            self._run_report_generation,
            task_id=task_id,
            enterprise_id=enterprise_id,
            user_id=user_id,
            year=year,
        )

        return task_id

    def _run_report_generation(
        self,
        task_id: str,
        enterprise_id: int,
        user_id: int,
        year: Optional[int] = None,
    ) -> None:
        """
        Execute the report generation (runs in background).

        This method is called by FastAPI BackgroundTasks and handles:
        - Running PeerComparisonAgent
        - Building ReportData schema
        - Running ReportGenerator for DOCX
        - Creating GeneratedReport record
        - Updating task status in Redis
        - Error handling

        Args:
            task_id: The task ID for status tracking.
            enterprise_id: The enterprise to analyze.
            user_id: The user who requested the report.
            year: Optional fiscal year for analysis.
        """
        import asyncio

        # Run the async function in a new event loop
        asyncio.run(
            self._async_run_report_generation(
                task_id=task_id,
                enterprise_id=enterprise_id,
                user_id=user_id,
                year=year,
            )
        )

    async def _async_run_report_generation(
        self,
        task_id: str,
        enterprise_id: int,
        user_id: int,
        year: Optional[int] = None,
    ) -> None:
        """
        Async implementation of report generation.

        Args:
            task_id: The task ID for status tracking.
            enterprise_id: The enterprise to analyze.
            user_id: The user who requested the report.
            year: Optional fiscal year for analysis.
        """
        db: Optional[Session] = None
        report: Optional[GeneratedReport] = None

        try:
            # Update status to running
            self.task_manager.update_task_status(
                task_id,
                status=TaskStatus.RUNNING.value,
                progress=0,
            )

            # Create database session
            db = SessionLocal()

            # Get enterprise
            enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            # Find existing report record (created by API endpoint)
            report = db.query(GeneratedReport).filter(
                GeneratedReport.task_id == task_id
            ).first()

            # If no existing record, create one
            if not report:
                report_years = f"{year}" if year else f"{date.today().year - 2}-{date.today().year}"
                report = GeneratedReport(
                    enterprise_id=enterprise_id,
                    generated_by=user_id,
                    task_id=task_id,
                    report_type=ReportType.FULL_DIAGNOSIS,
                    report_title=f"{enterprise.company_name} 健康度诊断报告",
                    report_years=report_years,
                    status=ReportStatus.GENERATING,
                    started_at=datetime.utcnow(),
                )
                db.add(report)
                db.commit()
                db.refresh(report)
            else:
                # Update existing record
                report.status = ReportStatus.GENERATING
                report.started_at = datetime.utcnow()
                db.commit()
                db.refresh(report)

            # Define progress callback
            def progress_callback(progress: int, message: str) -> None:
                self.task_manager.update_task_status(
                    task_id,
                    progress=progress,
                    metadata={"current_step": message},
                )

            # Step 1: Run peer comparison analysis (using new LangGraph agent)
            progress_callback(5, "Starting peer comparison analysis")

            peer_agent = PeerComparisonAgent(db)
            # The new LangGraph agent uses synchronous run() method
            peer_result = peer_agent.run(
                enterprise_id=enterprise_id,
                years=3,
            )

            # Step 2: Build ReportData schema
            progress_callback(45, "Building report data")

            report_data = self._build_report_data_from_comparison(
                enterprise=enterprise,
                peer_result=peer_result,
                year=year,
            )

            # Step 3: Generate DOCX report
            progress_callback(50, "Generating document")

            doc_generator = ReportGenerator()
            doc_path = doc_generator.generate(report_data)

            # Step 4: Update report record with results
            progress_callback(90, "Finalizing report")

            # Get file size
            import os

            file_size = os.path.getsize(doc_path) if doc_path and os.path.exists(doc_path) else None

            report.status = ReportStatus.COMPLETED
            report.file_path = doc_path
            report.file_size = file_size
            # Use peer_count as a proxy for health score (simplified for new agent)
            report.health_score = Decimal(str(min(peer_result.report.peer_count * 10, 100)))
            report.dimension_scores = {
                "profitability": 75.0,  # Default values - can be enhanced
                "solvency": 70.0,
                "growth": 65.0,
                "operational_efficiency": 70.0,
            }
            report.peer_comparison = {
                "peer_count": peer_result.report.peer_count,
                "industry_name": peer_result.report.industry_name,
            }
            report.summary = peer_result.report.executive_summary
            report.findings = self._generate_findings_from_report(peer_result.report)
            report.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(report)

            # Update task status to completed
            hs = report.health_score
            if hs is not None:
                health_score_value = float(hs)
            else:
                health_score_value = None
            self.task_manager.update_task_status(
                task_id,
                status=TaskStatus.COMPLETED.value,
                progress=100,
                metadata={
                    "report_id": report.id,
                    "health_score": health_score_value,
                    "file_path": doc_path,
                },
            )

            logger.info(
                f"Report generation task {task_id} completed: "
                f"report_id={report.id}, file={doc_path}"
            )

        except ValueError as e:
            # Validation error
            logger.error(f"Task {task_id} validation error: {e}")
            self.task_manager.update_task_status(
                task_id,
                status=TaskStatus.FAILED.value,
                error_message=str(e),
            )
            if report and db:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                report.completed_at = datetime.utcnow()
                db.commit()

        except Exception as e:
            # Unexpected error
            logger.exception(f"Task {task_id} unexpected error: {e}")
            self.task_manager.update_task_status(
                task_id,
                status=TaskStatus.FAILED.value,
                error_message=f"Internal error: {str(e)}",
            )
            if report and db:
                report.status = ReportStatus.FAILED
                report.error_message = f"Internal error: {str(e)}"
                report.completed_at = datetime.utcnow()
                db.commit()

        finally:
            # Clean up database session
            if db is not None:
                db.close()

    def _build_report_data_from_comparison(
        self,
        enterprise: Enterprise,
        peer_result: PeerComparisonResult,
        year: Optional[int] = None,
    ) -> ReportData:
        """
        Build ReportData schema from PeerComparisonResult.

        Args:
            enterprise: The enterprise being analyzed.
            peer_result: Complete result from peer comparison agent.
            year: The fiscal year for analysis.

        Returns:
            ReportData schema ready for DOCX generation.
        """
        peer_report = peer_result.report

        # Build executive summary from LLM-generated report
        executive_summary = ExecutiveSummary(
            overall_rating="良",
            overall_score=Decimal("70.0"),
            summary_text=peer_report.executive_summary,
            key_strengths=[s.item for s in peer_report.strengths[:3]],
            key_risks=[w.item for w in peer_report.weaknesses[:3]],
            recommendation=peer_report.recommendations[0]
            if peer_report.recommendations
            else "建议进一步分析企业状况。",
        )

        # Build financial metrics from comparison_metrics
        logger.info(f"Building financial metrics from {len(peer_result.comparison_metrics)} comparison_metrics")
        logger.debug(f"comparison_metrics sample: {peer_result.comparison_metrics[:2] if peer_result.comparison_metrics else 'empty'}")
        financial_metrics = self._build_financial_metrics(peer_result.comparison_metrics)

        # Build peer comparison with actual data
        peer_comparison = self._build_peer_comparison(peer_result)

        # Build trends from target_financials
        logger.info(f"Building trends from {len(peer_result.target_financials)} target_financials")
        logger.debug(f"target_financials sample: {peer_result.target_financials[:1] if peer_result.target_financials else 'empty'}")
        trends = self._build_trends(peer_result.target_financials)
        logger.info(f"Built {len(trends)} trends")

        # Build bar charts from comparison_metrics
        bar_charts = self._build_comparison_charts(peer_result.comparison_metrics)
        logger.info(f"Built {len(bar_charts)} bar_charts")

        # Build risk assessment from LLM report
        risk_level = "低" if not peer_report.risk_indicators else "中"
        risk_assessment = RiskAssessmentSection(
            overall_risk_level=risk_level,
            financial_risk=peer_report.financial_position_analysis[:500]
            if peer_report.financial_position_analysis
            else "暂无详细分析",
            operational_risk=peer_report.profitability_analysis[:500]
            if peer_report.profitability_analysis
            else "暂无详细分析",
            market_risk=peer_report.growth_analysis[:300]
            if peer_report.growth_analysis
            else "",
            risk_warnings=peer_report.risk_indicators[:5],
        )

        # Build recommendations from LLM report
        recommendations = RecommendationsSection(
            strategic_recommendations=peer_report.recommendations[:2],
            financial_recommendations=peer_report.recommendations[2:4]
            if len(peer_report.recommendations) > 2
            else [],
            operational_recommendations=peer_report.recommendations[4:6]
            if len(peer_report.recommendations) > 4
            else [],
            action_items=[w.item for w in peer_report.weaknesses[:3]],
        )

        # Build report data
        report_years = f"{year}" if year else f"{date.today().year - 2}-{date.today().year}"

        return ReportData(
            enterprise_id=enterprise.id,
            company_code=enterprise.company_code,
            company_name=enterprise.company_name,
            industry_name=enterprise.industry_name,
            report_type=ReportType.FULL_DIAGNOSIS,
            report_years=report_years,
            report_date=date.today(),
            executive_summary=executive_summary,
            financial_metrics=financial_metrics,
            bar_charts=bar_charts,
            line_charts=[],
            trends=trends,
            peer_comparison=peer_comparison,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
        )

    def _build_financial_metrics(
        self, comparison_metrics: List[Dict[str, Any]]
    ) -> FinancialMetricsSection:
        """Build financial metrics section from comparison metrics."""
        profitability = []
        solvency = []
        operation = []
        growth = []

        # Map metrics to categories
        metric_categories = {
            "营业收入": ("profitability", "元"),
            "净利润": ("profitability", "元"),
            "总资产": ("solvency", "元"),
            "所有者权益": ("solvency", "元"),
            "负债合计": ("solvency", "元"),
            "营业利润": ("profitability", "元"),
            "基本每股收益": ("profitability", "元/股"),
        }

        for metric in comparison_metrics:
            name = metric.get("name", "")
            category_info = metric_categories.get(name)

            if not category_info:
                continue

            category, unit = category_info

            fin_metric = FinancialMetric(
                name=name,
                value=Decimal(str(metric.get("target_value", 0)))
                if metric.get("target_value") else None,
                unit=metric.get("unit", unit),
                change_rate=None,
                industry_avg=Decimal(str(metric.get("peer_average", 0)))
                if metric.get("peer_average") else None,
                industry_rank=metric.get("target_rank"),
            )

            if category == "profitability":
                profitability.append(fin_metric)
            elif category == "solvency":
                solvency.append(fin_metric)
            elif category == "operation":
                operation.append(fin_metric)
            elif category == "growth":
                growth.append(fin_metric)

        return FinancialMetricsSection(
            profitability=profitability,
            solvency=solvency,
            operation=operation,
            growth=growth,
        )

    def _build_peer_comparison(
        self, peer_result: PeerComparisonResult
    ) -> PeerComparisonSection:
        """Build peer comparison section from agent result."""
        # Build peer companies list
        peer_companies = []
        for peer in peer_result.peer_enterprises[:10]:
            peer_companies.append(
                PeerCompany(
                    company_code=peer.get("company_code", ""),
                    company_name=peer.get("company_name", ""),
                    industry_name=peer.get("industry_name", ""),
                )
            )

        # Build comparison metrics for report
        comparison_metrics = []
        for metric in peer_result.comparison_metrics:
            comparison_metrics.append(
                FinancialMetric(
                    name=metric.get("name", ""),
                    value=Decimal(str(metric.get("target_value", 0)))
                    if metric.get("target_value") else None,
                    unit=metric.get("unit", "元"),
                    change_rate=None,
                    industry_avg=Decimal(str(metric.get("peer_average", 0)))
                    if metric.get("peer_average") else None,
                    industry_rank=metric.get("target_rank"),
                )
            )

        # Get ranking from first metric if available
        ranking = None
        if peer_result.comparison_metrics:
            ranking = peer_result.comparison_metrics[0].get("target_rank")

        # Build analysis text from LLM report
        peer_report = peer_result.report
        analysis_parts = []
        if peer_report.financial_position_analysis:
            analysis_parts.append(f"**财务状况**: {peer_report.financial_position_analysis}")
        if peer_report.profitability_analysis:
            analysis_parts.append(f"**盈利能力**: {peer_report.profitability_analysis}")
        if peer_report.growth_analysis:
            analysis_parts.append(f"**成长性**: {peer_report.growth_analysis}")

        analysis_text = "\n\n".join(analysis_parts) if analysis_parts else f"本企业与{peer_report.peer_count}家同行业企业进行了对比分析。"

        return PeerComparisonSection(
            peer_companies=peer_companies,
            comparison_metrics=comparison_metrics,
            analysis_text=analysis_text,
            ranking_in_industry=ranking,
        )

    def _build_trends(
        self, target_financials: List[Dict[str, Any]]
    ) -> List[TrendData]:
        """Build trend data from target financials (converted to 万元)."""
        trends = []

        if not target_financials:
            return trends

        # Build revenue trend
        revenue_data = []
        profit_data = []
        assets_data = []

        for year_data in sorted(target_financials, key=lambda x: x.get("year", 0)):
            year = year_data.get("year")
            income = year_data.get("income_statement") or {}
            balance = year_data.get("balance_sheet") or {}

            # Convert to 万元
            if income.get("operating_revenue"):
                revenue_data.append(
                    YearlyMetric(year=year, value=Decimal(str(income["operating_revenue"])) / 10000)
                )
            if income.get("net_profit"):
                profit_data.append(
                    YearlyMetric(year=year, value=Decimal(str(income["net_profit"])) / 10000)
                )
            if balance.get("total_assets"):
                assets_data.append(
                    YearlyMetric(year=year, value=Decimal(str(balance["total_assets"])) / 10000)
                )

        if revenue_data:
            trends.append(TrendData(metric_name="营业收入", unit="万元", data=revenue_data))
        if profit_data:
            trends.append(TrendData(metric_name="净利润", unit="万元", data=profit_data))
        if assets_data:
            trends.append(TrendData(metric_name="总资产", unit="万元", data=assets_data))

        return trends

    def _build_comparison_charts(
        self, comparison_metrics: List[Dict[str, Any]]
    ) -> List[ChartData]:
        """Build comparison bar charts from metrics."""
        charts = []

        if not comparison_metrics:
            return charts

        # Build a grouped bar chart for key metrics
        labels = []
        target_values = []
        avg_values = []

        for metric in comparison_metrics[:7]:  # Limit to 7 metrics
            name = metric.get("name", "")[:6]  # Truncate long names
            labels.append(name)
            target_values.append(metric.get("target_value") or 0)
            avg_values.append(metric.get("peer_average") or 0)

        if labels:
            charts.append(
                ChartData(
                    chart_type="bar",
                    title="关键指标与行业平均对比",
                    x_labels=labels,
                    datasets=[
                        {"label": "目标企业", "data": target_values},
                        {"label": "行业平均", "data": avg_values},
                    ],
                )
            )

        return charts

    def _generate_findings_from_report(
        self,
        peer_report: ComparisonReport,
    ) -> List[Dict[str, Any]]:
        """Generate key findings list from ComparisonReport."""
        findings = []

        # Add strengths as findings
        for strength in peer_report.strengths:
            findings.append(
                {
                    "type": "strength",
                    "title": strength.item,
                    "description": strength.evidence,
                }
            )

        # Add weaknesses as findings
        for weakness in peer_report.weaknesses:
            findings.append(
                {
                    "type": "warning",
                    "title": weakness.item,
                    "description": weakness.evidence,
                }
            )

        return findings

    def _build_report_data(
        self,
        enterprise: Enterprise,
        peer_result: Any,
        year: Optional[int] = None,
    ) -> ReportData:
        """
        Build ReportData schema from peer comparison results.

        Args:
            enterprise: The enterprise being analyzed.
            peer_result: Results from PeerComparisonAgent.
            year: The fiscal year for analysis.

        Returns:
            ReportData schema ready for DOCX generation.
        """
        # Build executive summary
        score = peer_result.overall_score
        if score >= 80:
            rating = "优"
        elif score >= 60:
            rating = "良"
        elif score >= 40:
            rating = "中"
        else:
            rating = "差"

        scores = [
            ("盈利能力", peer_result.profitability_score),
            ("偿债能力", peer_result.solvency_score),
            ("成长能力", peer_result.growth_score),
            ("运营效率", peer_result.operational_efficiency_score),
        ]
        scores.sort(key=lambda x: x[1], reverse=True)

        executive_summary = ExecutiveSummary(
            overall_rating=rating,
            overall_score=score,
            summary_text=self._generate_summary_text(enterprise, peer_result),
            key_strengths=[s[0] for s in scores[:2] if s[1] >= 60],
            key_risks=[s[0] for s in scores if s[1] < 50],
            recommendation=self._get_recommendation(rating),
        )

        # Build financial metrics
        metrics = peer_result.metrics_comparison
        financial_metrics = FinancialMetricsSection(
            profitability=[
                FinancialMetric(
                    name="净资产收益率(ROE)",
                    value=Decimal(str(metrics.get("roe", 0) or 0)),
                    unit="%",
                    change_rate=None,
                    industry_avg=None,
                    industry_rank=None,
                ),
                FinancialMetric(
                    name="总资产收益率(ROA)",
                    value=Decimal(str(metrics.get("roa", 0) or 0)),
                    unit="%",
                    change_rate=None,
                    industry_avg=None,
                    industry_rank=None,
                ),
            ],
            solvency=[
                FinancialMetric(
                    name="资产负债率",
                    value=Decimal(str(metrics.get("debt_ratio", 0) or 0)),
                    unit="%",
                    change_rate=None,
                    industry_avg=None,
                    industry_rank=None,
                ),
                FinancialMetric(
                    name="流动比率",
                    value=Decimal(str(metrics.get("current_ratio", 0) or 0)),
                    unit="",
                    change_rate=None,
                    industry_avg=None,
                    industry_rank=None,
                ),
            ],
            operation=[
                FinancialMetric(
                    name="资产周转率",
                    value=Decimal(str(metrics.get("asset_turnover", 0) or 0)),
                    unit="次",
                    change_rate=None,
                    industry_avg=None,
                    industry_rank=None,
                ),
            ],
            growth=[],  # Would need historical data
        )

        # Build peer comparison
        peer_companies = [
            PeerCompany(
                company_code=p.get("company_code", ""),
                company_name=p.get("company_name", ""),
                industry_name=peer_result.industry_name,
            )
            for p in peer_result.peer_scores[:5]
        ]

        peer_comparison = PeerComparisonSection(
            peer_companies=peer_companies,
            comparison_metrics=[
                FinancialMetric(
                    name="行业平均分",
                    value=peer_result.industry_average,
                    unit="分",
                    change_rate=None,
                    industry_avg=None,
                    industry_rank=None,
                ),
            ],
            analysis_text=f"本企业在{peer_result.industry_name}行业中处于{peer_result.percentile_rank}%分位。",
            ranking_in_industry=peer_result.percentile_rank,
        )

        # Build risk assessment
        risk_level = "低" if score >= 70 else "中" if score >= 50 else "高"
        risk_assessment = RiskAssessmentSection(
            overall_risk_level=risk_level,
            financial_risk="财务风险较低" if peer_result.solvency_score >= 60 else "财务风险需关注",
            operational_risk="经营状况良好"
            if peer_result.profitability_score >= 60
            else "经营效率需改善",
            market_risk="市场地位稳固" if peer_result.percentile_rank >= 50 else "市场竞争压力较大",
            risk_warnings=[f"{s[0]}得分较低({s[1]:.1f}分)" for s in scores if s[1] < 50],
        )

        # Build recommendations
        recommendations = RecommendationsSection(
            strategic_recommendations=[
                "持续优化主营业务结构",
                "加强核心竞争优势",
            ],
            financial_recommendations=[
                "优化资产负债结构" if peer_result.solvency_score < 60 else "保持健康的财务结构",
                "提高资金使用效率",
            ],
            operational_recommendations=[
                "提升运营效率"
                if peer_result.operational_efficiency_score < 60
                else "持续优化运营流程",
            ],
            action_items=[
                "定期监控关键财务指标",
                "建立风险预警机制",
            ],
        )

        # Build report data
        report_years = f"{year}" if year else f"{date.today().year - 2}-{date.today().year}"

        return ReportData(
            enterprise_id=enterprise.id,
            company_code=enterprise.company_code,
            company_name=enterprise.company_name,
            industry_name=enterprise.industry_name,
            report_type=ReportType.FULL_DIAGNOSIS,
            report_years=report_years,
            report_date=date.today(),
            executive_summary=executive_summary,
            financial_metrics=financial_metrics,
            bar_charts=self._build_bar_charts(peer_result),
            line_charts=[],
            trends=[],
            peer_comparison=peer_comparison,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
        )

    def _build_bar_charts(
        self,
        peer_result: Any,
    ) -> List[ChartData]:
        """Build bar charts for the report."""
        # Dimension scores chart
        return [
            ChartData(
                chart_type="bar",
                title="企业健康度维度评分",
                x_labels=["盈利能力", "偿债能力", "成长能力", "运营效率"],
                datasets=[
                    {
                        "label": "得分",
                        "data": [
                            float(peer_result.profitability_score),
                            float(peer_result.solvency_score),
                            float(peer_result.growth_score),
                            float(peer_result.operational_efficiency_score),
                        ],
                    }
                ],
            )
        ]

    def _generate_summary_text(
        self,
        enterprise: Enterprise,
        peer_result: Any,
    ) -> str:
        """Generate executive summary text."""
        score = peer_result.overall_score

        if score >= 80:
            assessment = "企业整体经营状况优秀，各项指标表现突出"
        elif score >= 60:
            assessment = "企业整体经营状况良好，大部分指标处于健康水平"
        elif score >= 40:
            assessment = "企业整体经营状况一般，部分指标需要关注"
        else:
            assessment = "企业整体经营状况需重点关注，多项指标存在风险"

        return (
            f"{enterprise.company_name}综合健康度评分为{score:.1f}分，"
            f"在{peer_result.industry_name}行业中处于{peer_result.percentile_rank}%分位。"
            f"{assessment}。"
        )

    def _generate_findings_list(
        self,
        peer_result: Any,
    ) -> List[Dict[str, Any]]:
        """Generate key findings list."""
        findings = []

        if peer_result.profitability_score >= 70:
            findings.append(
                {
                    "type": "strength",
                    "title": "盈利能力突出",
                    "description": f"盈利能力得分{peer_result.profitability_score:.1f}分",
                }
            )
        elif peer_result.profitability_score < 40:
            findings.append(
                {
                    "type": "warning",
                    "title": "盈利能力需关注",
                    "description": f"盈利能力得分{peer_result.profitability_score:.1f}分",
                }
            )

        if peer_result.solvency_score >= 70:
            findings.append(
                {
                    "type": "strength",
                    "title": "偿债能力强",
                    "description": f"偿债能力得分{peer_result.solvency_score:.1f}分",
                }
            )
        elif peer_result.solvency_score < 40:
            findings.append(
                {
                    "type": "risk",
                    "title": "偿债风险",
                    "description": f"偿债能力得分{peer_result.solvency_score:.1f}分",
                }
            )

        if peer_result.percentile_rank >= 75:
            findings.append(
                {
                    "type": "strength",
                    "title": "行业领先",
                    "description": f"行业排名{peer_result.percentile_rank}%分位",
                }
            )

        return findings

    def _get_recommendation(self, rating: str) -> str:
        """Get overall recommendation based on rating."""
        recommendations = {
            "优": "企业综合表现优秀，建议保持当前经营策略，持续提升核心竞争力。",
            "良": "企业整体表现良好，建议关注弱势指标，优化经营结构。",
            "中": "企业表现一般，建议深入分析问题领域，制定改进计划。",
            "差": "企业存在较多问题，建议全面诊断，优先解决关键风险。",
        }
        return recommendations.get(rating, "建议进一步分析企业状况。")

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        Get the status of a report generation task.

        Args:
            task_id: The task ID to query.

        Returns:
            Dictionary with task status or None if not found.
        """
        return self.task_manager.get_task_status(task_id)

    def list_tasks(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        List report generation tasks.

        Args:
            user_id: Filter by user ID.
            status: Filter by status.
            limit: Maximum number of tasks to return.

        Returns:
            List of task dictionaries.
        """
        return self.task_manager.list_tasks(
            user_id=user_id,
            status=status,
            task_type=self.TASK_TYPE,
            limit=limit,
        )

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.

        Note: This only marks the task as cancelled. If the task is already
        running, it will continue to completion.

        Args:
            task_id: The task ID to cancel.

        Returns:
            True if task was cancelled, False if not found or already completed.
        """
        status = self.task_manager.get_task_status(task_id)

        if not status:
            return False

        if status.get("status") in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
            return False

        # Mark as failed with cancellation message
        self.task_manager.update_task_status(
            task_id,
            status=TaskStatus.FAILED.value,
            error_message="Task cancelled by user",
        )

        logger.info(f"Task {task_id} cancelled")
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task record.

        Args:
            task_id: The task ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self.task_manager.delete_task(task_id)

    def set_task_expiry(self, task_id: str, seconds: int = 86400) -> bool:
        """
        Set expiry time for a task record.

        By default, task records expire after 24 hours.

        Args:
            task_id: The task ID.
            seconds: Time to live in seconds (default: 24 hours).

        Returns:
            True if successful, False otherwise.
        """
        return self.task_manager.set_task_expiry(task_id, seconds)


# Singleton instance for convenience
_report_task_service: Optional[ReportTaskService] = None


def get_report_task_service() -> ReportTaskService:
    """
    Get the singleton ReportTaskService instance.

    Returns:
        ReportTaskService instance.
    """
    global _report_task_service
    if _report_task_service is None:
        _report_task_service = ReportTaskService()
    return _report_task_service
