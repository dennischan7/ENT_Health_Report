"""
E2E Tests for Report Generation Flow.

Tests the complete report generation workflow including:
- POST /api/reports/generate - Start report generation
- GET /api/reports/{task_id}/status - Get task status
- GET /api/reports - List reports
- GET /api/reports/{report_id} - Get report details
- DELETE /api/reports/{task_id} - Cancel/delete task
- GET /api/reports/{task_id}/download - Download report

Uses FastAPI dependency override for database mocking.
"""

import os
import tempfile
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.report import ReportStatus, ReportType
from app.db.session import get_db
from app.api.deps import get_current_user
from app.services.report_task_service import ReportTaskService


# ==================== Fixtures ====================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.role = "user"
    user.is_active = True
    return user


@pytest.fixture
def mock_enterprise():
    """Create a mock enterprise."""
    enterprise = MagicMock()
    enterprise.id = 1
    enterprise.company_code = "600000"
    enterprise.company_name = "浦发银行"
    enterprise.industry_name = "银行业"
    enterprise.category_name = "金融业"
    enterprise.industry_code = "J66"
    return enterprise


@pytest.fixture
def mock_report():
    """Create a mock generated report."""
    report = MagicMock()
    report.id = 1
    report.enterprise_id = 1
    report.report_type = ReportType.FULL_DIAGNOSIS
    report.report_title = "浦发银行健康度诊断报告"
    report.report_years = "2021-2023"
    report.status = ReportStatus.COMPLETED
    report.generated_by = 1
    report.file_path = "/tmp/test_report.docx"
    report.file_size = 102400
    report.health_score = Decimal("75.5")
    report.task_id = "test-task-id-12345"
    report.created_at = datetime(2024, 1, 1, 0, 0, 0)
    report.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    report.generation_time_seconds = 30.5
    report.llm_model_used = "deepseek-chat"
    report.tokens_used = 1500
    report.prompt_tokens = 500
    report.completion_tokens = 1000
    report.error_message = None
    report.started_at = datetime(2024, 1, 1, 0, 0, 0)
    report.completed_at = datetime(2024, 1, 1, 0, 0, 30)
    return report


@pytest.fixture
def mock_comparison_report():
    """Create a mock ComparisonReport for testing."""
    from app.services.agents.peer_comparison_agent import ComparisonReport, StrengthWeakness

    return ComparisonReport(
        target_company="浦发银行",
        target_code="600000",
        industry_name="银行业",
        peer_count=5,
        executive_summary="该企业整体经营状况良好，财务结构健康。",
        strengths=[
            StrengthWeakness(item="盈利能力强", evidence="ROE高于行业平均"),
            StrengthWeakness(item="偿债能力稳健", evidence="资产负债率处于合理范围"),
        ],
        weaknesses=[
            StrengthWeakness(item="成长性不足", evidence="营收增长率低于行业平均"),
        ],
        financial_position_analysis="财务状况总体稳健",
        profitability_analysis="盈利能力处于行业中上水平",
        growth_analysis="近3年保持稳定增长态势",
        recommendations=[
            "建议优化资产结构",
            "建议加强成本控制",
        ],
        risk_indicators=[
            "市场竞争加剧",
        ],
    )


@pytest.fixture
def client_with_mock(mock_db, mock_user):
    """Create a test client with mocked dependencies."""

    def override_get_db():
        yield mock_db

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client, mock_db

    app.dependency_overrides.clear()


# ==================== Test Report Generation Endpoint ====================


class TestReportGenerationEndpoint:
    """Tests for POST /api/reports/generate endpoint."""

    def test_generate_report_success(
        self,
        client_with_mock,
        mock_user,
        mock_enterprise,
    ):
        """Test successful report generation request."""
        client, mock_db = client_with_mock

        # Setup enterprise query mock
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_enterprise,  # enterprise lookup
        ]

        # Mock report creation
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.task_id = "test-task-id"
        mock_report.status = ReportStatus.PENDING
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock the service
        with patch("app.api.reports.get_report_task_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.start_report_generation = AsyncMock(return_value="test-task-id-12345")
            mock_get_service.return_value = mock_service

            # Make request
            response = client.post(
                "/api/reports/generate",
                json={
                    "enterprise_id": 1,
                    "report_type": "full_diagnosis",
                    "report_years": "2021-2023",
                    "include_peer_comparison": True,
                    "peer_count": 5,
                },
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] == "pending"

    def test_generate_report_enterprise_not_found(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test report generation with non-existent enterprise."""
        client, mock_db = client_with_mock

        # Setup enterprise query mock
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.post(
            "/api/reports/generate",
            json={
                "enterprise_id": 999,
                "report_type": "full_diagnosis",
            },
        )

        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_report_invalid_report_type(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test report generation with invalid report type."""
        client, mock_db = client_with_mock

        # Make request with invalid report type
        response = client.post(
            "/api/reports/generate",
            json={
                "enterprise_id": 1,
                "report_type": "invalid_type",
            },
        )

        # Assertions - should fail validation
        assert response.status_code == 422


# ==================== Test Task Status Endpoint ====================


class TestTaskStatusEndpoint:
    """Tests for GET /api/reports/{task_id}/status endpoint."""

    def test_get_task_status_success(
        self,
        client_with_mock,
        mock_user,
        mock_report,
    ):
        """Test getting task status successfully."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        with patch("app.api.reports.get_report_task_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_task_status.return_value = {
                "task_id": "test-task-id-12345",
                "status": "completed",
                "progress": 100,
                "message": "报告生成完成",
            }
            mock_get_service.return_value = mock_service

            # Make request
            response = client.get("/api/reports/test-task-id-12345/status")

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id-12345"
            assert data["status"] == "completed"

    def test_get_task_status_not_found(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test getting status for non-existent task."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.api.reports.get_report_task_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_task_status.return_value = None
            mock_get_service.return_value = mock_service

            # Make request
            response = client.get("/api/reports/nonexistent-task-id/status")

            # Assertions
            assert response.status_code == 404


# ==================== Test List Reports Endpoint ====================


class TestListReportsEndpoint:
    """Tests for GET /api/reports endpoint."""

    def test_list_reports_success(
        self,
        client_with_mock,
        mock_user,
        mock_report,
    ):
        """Test listing reports successfully."""
        client, mock_db = client_with_mock

        # Setup query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_report]
        mock_query.count.return_value = 1
        mock_db.query.return_value = mock_query

        # Make request
        response = client.get("/api/reports")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_reports_pagination(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test listing reports with pagination."""
        client, mock_db = client_with_mock

        # Setup query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        # Make request with pagination
        response = client.get("/api/reports?page=2&page_size=10")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


# ==================== Test Get Report Detail Endpoint ====================


class TestGetReportDetailEndpoint:
    """Tests for GET /api/reports/{report_id} endpoint."""

    def test_get_report_detail_success(
        self,
        client_with_mock,
        mock_user,
        mock_report,
    ):
        """Test getting report detail successfully."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        # Make request
        response = client.get("/api/reports/1")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_get_report_detail_not_found(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test getting non-existent report detail."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.get("/api/reports/999")

        # Assertions
        assert response.status_code == 404


# ==================== Test Cancel/Delete Task Endpoint ====================


class TestCancelDeleteTaskEndpoint:
    """Tests for DELETE /api/reports/{task_id} endpoint."""

    def test_cancel_running_task(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test cancelling a running task."""
        client, mock_db = client_with_mock

        # Create a running report
        running_report = MagicMock()
        running_report.id = 1
        running_report.enterprise_id = 1
        running_report.report_title = "Test Report"
        running_report.status = ReportStatus.GENERATING
        running_report.task_id = "test-task-id-12345"

        mock_db.query.return_value.filter.return_value.first.return_value = running_report

        with patch("app.api.reports.get_report_task_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_task_status.return_value = {
                "task_id": "test-task-id-12345",
                "status": "running",
            }
            mock_service.cancel_task.return_value = True
            mock_get_service.return_value = mock_service

            # Make request
            response = client.delete("/api/reports/test-task-id-12345")

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"

    def test_delete_completed_task(
        self,
        client_with_mock,
        mock_user,
        mock_report,
    ):
        """Test deleting a completed task."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        with patch("app.api.reports.get_report_task_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_task_status.return_value = {
                "task_id": "test-task-id-12345",
                "status": "completed",
            }
            mock_service.cancel_task.return_value = False
            mock_service.delete_task.return_value = True
            mock_get_service.return_value = mock_service

            # Make request
            response = client.delete("/api/reports/test-task-id-12345")

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"

    def test_cancel_nonexistent_task(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test cancelling a non-existent task."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.api.reports.get_report_task_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_task_status.return_value = None
            mock_get_service.return_value = mock_service

            # Make request
            response = client.delete("/api/reports/nonexistent-task-id")

            # Assertions
            assert response.status_code == 404


# ==================== Test Download Report Endpoint ====================


class TestDownloadReportEndpoint:
    """Tests for GET /api/reports/{task_id}/download endpoint."""

    def test_download_report_success(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test downloading a completed report."""
        client, mock_db = client_with_mock

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(b"test content for docx file")
            tmp_path = tmp.name

        try:
            # Create a completed report with file
            completed_report = MagicMock()
            completed_report.id = 1
            completed_report.enterprise_id = 1
            completed_report.report_title = "Test Report"
            completed_report.status = ReportStatus.COMPLETED
            completed_report.task_id = "test-task-id-12345"
            completed_report.file_path = tmp_path

            mock_db.query.return_value.filter.return_value.first.return_value = completed_report

            # Make request
            response = client.get("/api/reports/test-task-id-12345/download")

            # Assertions
            assert response.status_code == 200
            assert "application/vnd.openxmlformats" in response.headers["content-type"]
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_download_report_not_ready(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test downloading a report that is not ready."""
        client, mock_db = client_with_mock

        # Create a generating report
        generating_report = MagicMock()
        generating_report.id = 1
        generating_report.enterprise_id = 1
        generating_report.report_title = "Test Report"
        generating_report.status = ReportStatus.GENERATING
        generating_report.task_id = "test-task-id-12345"

        mock_db.query.return_value.filter.return_value.first.return_value = generating_report

        # Make request
        response = client.get("/api/reports/test-task-id-12345/download")

        # Assertions
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()

    def test_download_report_file_not_found(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test downloading a report where file is missing."""
        client, mock_db = client_with_mock

        # Create a completed report with missing file
        completed_report = MagicMock()
        completed_report.id = 1
        completed_report.enterprise_id = 1
        completed_report.report_title = "Test Report"
        completed_report.status = ReportStatus.COMPLETED
        completed_report.task_id = "test-task-id-12345"
        completed_report.file_path = "/nonexistent/path/report.docx"

        mock_db.query.return_value.filter.return_value.first.return_value = completed_report

        # Make request
        response = client.get("/api/reports/test-task-id-12345/download")

        # Assertions
        assert response.status_code == 404


# ==================== Test Enterprise Report Summary Endpoint ====================


class TestEnterpriseReportSummaryEndpoint:
    """Tests for GET /api/reports/enterprises/{enterprise_id}/summary endpoint."""

    def test_get_enterprise_report_summary_success(
        self,
        client_with_mock,
        mock_user,
        mock_enterprise,
        mock_report,
    ):
        """Test getting enterprise report summary."""
        client, mock_db = client_with_mock

        # Setup mocks for the multiple queries
        def query_side_effect(model):
            mock_query = MagicMock()

            # For enterprise query
            if hasattr(model, "__tablename__") and model.__tablename__ == "enterprises":
                mock_query.filter.return_value.first.return_value = mock_enterprise
            else:
                # For generated_reports query
                mock_query.filter.return_value.filter.return_value.count.return_value = 1
                mock_query.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_report
            return mock_query

        mock_db.query.side_effect = query_side_effect

        # Make request
        response = client.get("/api/reports/enterprises/1/summary")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["enterprise_id"] == 1
        assert data["company_code"] == "600000"

    def test_get_enterprise_report_summary_enterprise_not_found(
        self,
        client_with_mock,
        mock_user,
    ):
        """Test getting summary for non-existent enterprise."""
        client, mock_db = client_with_mock

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.get("/api/reports/enterprises/999/summary")

        # Assertions
        assert response.status_code == 404


# ==================== Test ReportTaskService Integration ====================


class TestReportTaskService:
    """Tests for ReportTaskService class methods."""

    def test_service_initialization(self):
        """Test ReportTaskService initialization."""
        with patch("app.services.report_task_service.TaskManager") as mock_task_manager_class:
            mock_task_manager = MagicMock()
            mock_task_manager_class.return_value = mock_task_manager

            service = ReportTaskService()
            assert service.task_manager is not None

    def test_get_task_status(self):
        """Test getting task status from service."""
        with patch("app.services.report_task_service.TaskManager") as mock_task_manager_class:
            mock_task_manager = MagicMock()
            mock_task_manager.get_task_status.return_value = {
                "task_id": "test-id",
                "status": "completed",
            }
            mock_task_manager_class.return_value = mock_task_manager

            service = ReportTaskService()
            status = service.get_task_status("test-id")

            assert status is not None
            assert status["status"] == "completed"

    def test_cancel_task(self):
        """Test cancelling a task."""
        with patch("app.services.report_task_service.TaskManager") as mock_task_manager_class:
            mock_task_manager = MagicMock()
            mock_task_manager.get_task_status.return_value = {
                "task_id": "test-id",
                "status": "running",
            }
            mock_task_manager.update_task_status.return_value = True
            mock_task_manager_class.return_value = mock_task_manager

            service = ReportTaskService()
            result = service.cancel_task("test-id")

            assert result is True
            mock_task_manager.update_task_status.assert_called_once()

    def test_list_tasks(self):
        """Test listing tasks."""
        with patch("app.services.report_task_service.TaskManager") as mock_task_manager_class:
            mock_task_manager = MagicMock()
            mock_task_manager.list_tasks.return_value = [
                {"task_id": "task-1", "status": "completed"},
                {"task_id": "task-2", "status": "running"},
            ]
            mock_task_manager_class.return_value = mock_task_manager

            service = ReportTaskService()
            tasks = service.list_tasks(status="running")

            assert len(tasks) == 2


# ==================== Test Error Scenarios ====================


class TestErrorScenarios:
    """Tests for error scenarios and edge cases."""

    def test_missing_authorization_header(self):
        """Test request without authorization header."""
        with TestClient(app) as client:
            response = client.get("/api/reports")
            assert response.status_code == 403


# ==================== Test Health Check ====================


class TestHealthCheck:
    """Tests for health check endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        with TestClient(app) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint."""
        with TestClient(app) as client:
            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "docs" in data
