"""
Report generation API routes.
Provides endpoints for generating, tracking, and downloading enterprise health reports.
"""

from typing import Optional, List
from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.models.enterprise import Enterprise
from app.models.report import GeneratedReport, ReportType, ReportStatus
from app.schemas.report import (
    ReportGenerateRequest,
    GeneratedReportResponse,
    GeneratedReportListResponse,
)
from app.api.deps import get_current_user
from app.services.report_task_service import get_report_task_service, ReportTaskService


router = APIRouter()


# ==================== Request/Response Schemas ====================


class TaskStatusResponse(BaseModel):
    """Response for task status."""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: Optional[int] = Field(default=None, description="进度百分比")
    message: Optional[str] = Field(default=None, description="状态消息")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")
    report_id: Optional[int] = Field(default=None, description="生成的报告ID")


class GenerateResponse(BaseModel):
    """Response for report generation start."""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")


# ==================== Report Generation Endpoint ====================


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate enterprise health report",
)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateResponse:
    """
    Start generating a health report for an enterprise.
    启动企业健康度报告生成任务。

    - **enterprise_id**: 企业ID（必填）
    - **report_type**: 报告类型（默认：完整诊断报告）
    - **report_years**: 报告年度范围（如：'2021-2023'）
    - **include_peer_comparison**: 是否包含同业对比（默认：是）
    - **peer_count**: 同业对比公司数量（默认：5）
    """
    # Verify enterprise exists
    enterprise = db.query(Enterprise).filter(Enterprise.id == request.enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {request.enterprise_id} not found",
        )

    # Create report record
    report = GeneratedReport(
        enterprise_id=request.enterprise_id,
        report_type=request.report_type,
        report_title=f"{enterprise.company_name}健康度诊断报告",
        report_years=request.report_years,
        status=ReportStatus.PENDING,
        generated_by=current_user.id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Start report generation task using the service
    service = get_report_task_service()

    # The service handles task creation and background execution
    task_id = await service.start_report_generation(
        enterprise_id=request.enterprise_id,
        user_id=current_user.id,
        background_tasks=background_tasks,
        year=int(request.report_years.split("-")[0]) if request.report_years else None,
    )

    # Update report with task_id
    report.task_id = task_id
    report.status = ReportStatus.GENERATING
    report.started_at = datetime.now()
    db.commit()

    return GenerateResponse(
        task_id=task_id,
        status="pending",
        message=f"报告生成任务已启动，任务ID: {task_id}",
    )


# ==================== Task Status Endpoint ====================


@router.get(
    "/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="Get report generation task status",
)
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusResponse:
    """
    Get the status of a report generation task.
    获取报告生成任务的状态。
    """
    service = get_report_task_service()
    task_status = service.get_task_status(task_id)

    if not task_status:
        # Check if task exists in database
        report = db.query(GeneratedReport).filter(GeneratedReport.task_id == task_id).first()
        if report:
            return TaskStatusResponse(
                task_id=task_id,
                status=report.status.value,
                message=f"报告状态: {report.status.value}",
                report_id=report.id,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    # Get report_id if available
    report = db.query(GeneratedReport).filter(GeneratedReport.task_id == task_id).first()

    return TaskStatusResponse(
        task_id=task_id,
        status=task_status.get("status", "unknown"),
        progress=task_status.get("progress"),
        message=task_status.get("message"),
        error_message=task_status.get("error_message"),
        created_at=task_status.get("created_at"),
        updated_at=task_status.get("updated_at"),
        report_id=report.id if report else None,
    )


# ==================== List Reports Endpoint ====================


@router.get(
    "",
    response_model=GeneratedReportListResponse,
    summary="List generated reports",
)
def list_reports(
    enterprise_id: Optional[int] = Query(None, description="企业ID筛选"),
    report_type: Optional[ReportType] = Query(None, description="报告类型筛选"),
    status_filter: Optional[ReportStatus] = Query(None, alias="status", description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedReportListResponse:
    """
    List generated reports with pagination and filters.
    查询已生成的报告列表。

    支持按企业ID、报告类型、状态筛选。
    """
    query = db.query(GeneratedReport)

    # Apply filters
    if enterprise_id:
        query = query.filter(GeneratedReport.enterprise_id == enterprise_id)

    if report_type:
        query = query.filter(GeneratedReport.report_type == report_type)

    if status_filter:
        query = query.filter(GeneratedReport.status == status_filter)

    # Order by created_at descending
    query = query.order_by(GeneratedReport.created_at.desc())

    # Count total
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return GeneratedReportListResponse(
        items=[GeneratedReportResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


# ==================== Get Report Detail Endpoint ====================


@router.get(
    "/{report_id}",
    response_model=GeneratedReportResponse,
    summary="Get report by ID",
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedReportResponse:
    """
    Get a specific report by ID.
    根据ID获取报告详情。
    """
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id {report_id} not found",
        )

    return GeneratedReportResponse.model_validate(report)


# ==================== Cancel/Delete Task Endpoint ====================


@router.delete(
    "/{task_id}",
    summary="Cancel or delete a report task",
)
def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a pending/running task or delete a completed task.
    取消正在运行的任务或删除已完成的任务记录。
    """
    service = get_report_task_service()

    # Check if task exists in database
    report = db.query(GeneratedReport).filter(GeneratedReport.task_id == task_id).first()

    if not report and not service.get_task_status(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    # Cancel task in task manager
    cancelled = service.cancel_task(task_id)

    if report:
        if report.status in [ReportStatus.PENDING, ReportStatus.GENERATING]:
            # Cancel running task
            report.status = ReportStatus.FAILED
            report.error_message = "Task cancelled by user"
            report.completed_at = datetime.now()
            db.commit()
            return {
                "status": "cancelled",
                "message": "任务已取消",
                "task_id": task_id,
            }
        else:
            # Delete completed/failed task
            db.delete(report)
            db.commit()
            service.delete_task(task_id)
            return {
                "status": "deleted",
                "message": "任务记录已删除",
                "task_id": task_id,
            }

    return {
        "status": "cancelled" if cancelled else "not_found",
        "message": "任务已取消" if cancelled else "任务未找到",
        "task_id": task_id,
    }


# ==================== Download Report Endpoint ====================


@router.get(
    "/{task_id}/download",
    summary="Download generated report",
)
def download_report(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download a generated report file.
    下载已生成的报告文件。
    """
    # Find report by task_id
    report = db.query(GeneratedReport).filter(GeneratedReport.task_id == task_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with task_id {task_id} not found",
        )

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready for download. Current status: {report.status.value}",
        )

    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found. It may have been deleted or moved.",
        )

    # Generate filename
    filename = f"{report.report_title}.docx"
    filename = filename.replace(" ", "_").replace("/", "_")

    return FileResponse(
        path=report.file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ==================== Enterprise Reports Summary ====================


class EnterpriseReportSummary(BaseModel):
    """Summary of reports for an enterprise."""

    enterprise_id: int
    company_code: str
    company_name: str
    total_reports: int
    latest_report_date: Optional[datetime]
    latest_health_score: Optional[float]


@router.get(
    "/enterprises/{enterprise_id}/summary",
    response_model=EnterpriseReportSummary,
    summary="Get report summary for an enterprise",
)
def get_enterprise_report_summary(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseReportSummary:
    """
    Get a summary of reports for a specific enterprise.
    获取指定企业的报告摘要。
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )

    # Get report stats
    total_reports = (
        db.query(GeneratedReport)
        .filter(
            GeneratedReport.enterprise_id == enterprise_id,
            GeneratedReport.status == ReportStatus.COMPLETED,
        )
        .count()
    )

    latest_report = (
        db.query(GeneratedReport)
        .filter(
            GeneratedReport.enterprise_id == enterprise_id,
            GeneratedReport.status == ReportStatus.COMPLETED,
        )
        .order_by(GeneratedReport.created_at.desc())
        .first()
    )

    # Get the actual datetime value from the model
    latest_report_date = None
    if latest_report:
        # Access the actual value, not the column descriptor
        latest_report_date = getattr(latest_report, "created_at", None)

    latest_health_score = None
    if latest_report and latest_report.health_score is not None:
        latest_health_score = float(latest_report.health_score)

    return EnterpriseReportSummary(
        enterprise_id=enterprise_id,
        company_code=enterprise.company_code,
        company_name=enterprise.company_name,
        total_reports=total_reports,
        latest_report_date=latest_report_date,
        latest_health_score=latest_health_score,
    )
