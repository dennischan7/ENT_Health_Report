"""
Generated Report model for tracking report generation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base, TimestampMixin


class ReportStatus(str, enum.Enum):
    """Report generation status."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(str, enum.Enum):
    """Report type."""

    FULL_DIAGNOSIS = "full_diagnosis"  # 完整诊断报告
    FINANCIAL_ANALYSIS = "financial_analysis"  # 财务分析报告
    PEER_COMPARISON = "peer_comparison"  # 同业对比报告
    RISK_ASSESSMENT = "risk_assessment"  # 风险评估报告


class GeneratedReport(Base, TimestampMixin):
    """
    Generated Report model for tracking report generation history.

    Stores metadata about generated reports including the enterprise,
    report type, file path, and generation status.
    """

    __tablename__ = "generated_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Enterprise being analyzed
    enterprise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enterprises.id"), nullable=False, index=True
    )

    # Report metadata
    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType), nullable=False, default=ReportType.FULL_DIAGNOSIS
    )
    report_title: Mapped[str] = mapped_column(String(200), nullable=False)

    # Report year range (e.g., "2021-2023")
    report_years: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Task ID from TaskManager (Redis)
    task_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Overall health score (0-100)
    health_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Individual dimension scores stored as JSON
    dimension_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Peer comparison data stored as JSON
    peer_comparison: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Main report content (Markdown or HTML)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Executive summary
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Key findings and recommendations as JSON array
    findings: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # File information
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes

    # Status tracking
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus), nullable=False, default=ReportStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generation metadata
    generated_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    generation_time_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # LLM usage tracking
    llm_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    generator = relationship("User", foreign_keys=[generated_by])

    def __repr__(self) -> str:
        return f"<GeneratedReport {self.id} - {self.report_title} ({self.status.value})>"
