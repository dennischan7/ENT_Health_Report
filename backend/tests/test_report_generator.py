"""
Tests for Report Generator Service.
"""

import os
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

# Import directly to avoid circular import issues in services/__init__.py
from app.services.report_generator import (
    ReportGenerator,
    ReportGeneratorError,
    get_report_generator,
)
from app.schemas.report import (
    ReportData,
    ReportType,
    FinancialMetric,
    YearlyMetric,
    TrendData,
    ChartData,
    ExecutiveSummary,
    FinancialMetricsSection,
    PeerComparisonSection,
    PeerCompany,
    RiskAssessmentSection,
    RecommendationsSection,
)


class TestReportGeneratorInit:
    """Test ReportGenerator initialization."""

    def test_default_init(self, tmp_path):
        """Test default initialization with custom directory."""
        generator = ReportGenerator(reports_dir=str(tmp_path))
        assert generator.reports_dir == tmp_path
        assert generator.chart_width == 6.0
        assert generator.chart_height == 4.0

    def test_custom_chart_dimensions(self, tmp_path):
        """Test custom chart dimensions."""
        generator = ReportGenerator(
            reports_dir=str(tmp_path),
            chart_width=8.0,
            chart_height=5.0,
        )
        assert generator.chart_width == 8.0
        assert generator.chart_height == 5.0

    def test_reports_dir_created(self, tmp_path):
        """Test that reports directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_reports"
        assert not new_dir.exists()

        generator = ReportGenerator(reports_dir=str(new_dir))
        assert new_dir.exists()
        assert generator.reports_dir == new_dir

    def test_get_report_generator_function(self, tmp_path):
        """Test convenience function."""
        generator = get_report_generator(reports_dir=str(tmp_path))
        assert isinstance(generator, ReportGenerator)
        assert generator.reports_dir == tmp_path


class TestReportGeneratorGenerate:
    """Test report generation."""

    @pytest.fixture
    def sample_report_data(self):
        """Create sample report data for testing."""
        return ReportData(
            enterprise_id=1,
            company_code="600000",
            company_name="浦发银行",
            industry_name="银行业",
            report_type=ReportType.FULL_DIAGNOSIS,
            report_years="2021-2023",
            report_date=date(2026, 3, 20),
            executive_summary=ExecutiveSummary(
                overall_rating="良",
                overall_score=Decimal("75.5"),
                summary_text="该企业整体经营状况良好，财务结构健康，盈利能力稳定。",
                key_strengths=["盈利能力强", "偿债能力稳健", "现金流充沛"],
                key_risks=["市场竞争加剧", "利率波动风险"],
                recommendation="建议持续优化资产结构，加强风险管理。",
            ),
            financial_metrics=FinancialMetricsSection(
                profitability=[
                    FinancialMetric(
                        name="ROE（净资产收益率）",
                        value=Decimal("12.5"),
                        unit="%",
                        change_rate=Decimal("2.3"),
                        industry_avg=Decimal("11.2"),
                    ),
                    FinancialMetric(
                        name="ROA（总资产收益率）",
                        value=Decimal("1.2"),
                        unit="%",
                        change_rate=Decimal("0.5"),
                        industry_avg=Decimal("1.0"),
                    ),
                ],
                solvency=[
                    FinancialMetric(
                        name="资产负债率",
                        value=Decimal("93.5"),
                        unit="%",
                        change_rate=Decimal("-0.5"),
                        industry_avg=Decimal("92.8"),
                    ),
                    FinancialMetric(
                        name="流动比率",
                        value=Decimal("1.5"),
                        unit="倍",
                        change_rate=Decimal("5.2"),
                        industry_avg=Decimal("1.3"),
                    ),
                ],
                operation=[],
                growth=[
                    FinancialMetric(
                        name="营业收入增长率",
                        value=Decimal("8.5"),
                        unit="%",
                        change_rate=Decimal("3.2"),
                        industry_avg=Decimal("6.0"),
                    ),
                ],
            ),
            bar_charts=[
                ChartData(
                    chart_type="bar",
                    title="盈利能力对比",
                    x_labels=["ROE", "ROA", "净利率"],
                    datasets=[
                        {"label": "本企业", "data": [12.5, 1.2, 25.0]},
                        {"label": "行业平均", "data": [11.2, 1.0, 22.0]},
                    ],
                ),
            ],
            trends=[
                TrendData(
                    metric_name="营业收入",
                    unit="亿元",
                    data=[
                        YearlyMetric(year=2021, value=Decimal("1500")),
                        YearlyMetric(year=2022, value=Decimal("1650")),
                        YearlyMetric(year=2023, value=Decimal("1780")),
                    ],
                ),
                TrendData(
                    metric_name="净利润",
                    unit="亿元",
                    data=[
                        YearlyMetric(year=2021, value=Decimal("450")),
                        YearlyMetric(year=2022, value=Decimal("520")),
                        YearlyMetric(year=2023, value=Decimal("580")),
                    ],
                ),
            ],
            peer_comparison=PeerComparisonSection(
                peer_companies=[
                    PeerCompany(
                        company_code="601398",
                        company_name="工商银行",
                        industry_name="银行业",
                    ),
                    PeerCompany(
                        company_code="601288",
                        company_name="农业银行",
                        industry_name="银行业",
                    ),
                ],
                comparison_metrics=[
                    FinancialMetric(
                        name="ROE",
                        value=Decimal("12.5"),
                        unit="%",
                        change_rate=None,
                        industry_avg=Decimal("11.2"),
                    ),
                ],
                analysis_text="该企业在银行业中处于中上水平，ROE指标优于行业平均。",
                ranking_in_industry=15,
            ),
            risk_assessment=RiskAssessmentSection(
                overall_risk_level="中",
                financial_risk="财务风险可控，资产负债率在合理范围内。",
                operational_risk="经营稳健，收入来源多元化。",
                market_risk="市场风险中等，需关注利率波动影响。",
                risk_warnings=["关注房地产贷款集中度", "监控不良贷款率变化"],
            ),
            recommendations=RecommendationsSection(
                strategic_recommendations=["加强数字化转型", "拓展零售业务"],
                financial_recommendations=["优化资产负债结构", "提高资本充足率"],
                operational_recommendations=["提升运营效率", "加强成本控制"],
                action_items=["制定三年发展规划", "完善风险管理体系"],
            ),
        )

    def test_generate_report_success(self, tmp_path, sample_report_data):
        """Test successful report generation."""
        generator = ReportGenerator(reports_dir=str(tmp_path))

        doc_path = generator.generate(sample_report_data)

        # Check file exists
        assert os.path.exists(doc_path)
        assert doc_path.endswith(".docx")

        # Check file size (should be > 10KB for a report with charts)
        file_size = os.path.getsize(doc_path)
        assert file_size > 10000, f"Report file too small: {file_size} bytes"

    def test_generate_report_custom_filename(self, tmp_path, sample_report_data):
        """Test report generation with custom filename."""
        generator = ReportGenerator(reports_dir=str(tmp_path))

        custom_filename = "custom_report.docx"
        doc_path = generator.generate(sample_report_data, output_filename=custom_filename)

        assert doc_path.endswith(custom_filename)
        assert os.path.exists(doc_path)

    def test_generate_report_auto_filename(self, tmp_path, sample_report_data):
        """Test automatic filename generation."""
        generator = ReportGenerator(reports_dir=str(tmp_path))

        doc_path = generator.generate(sample_report_data)

        # Should contain company code and date
        assert "600000" in doc_path
        assert "full_diagnosis" in doc_path

    def test_generate_report_minimal_data(self, tmp_path):
        """Test report generation with minimal data."""
        generator = ReportGenerator(reports_dir=str(tmp_path))

        minimal_data = ReportData(
            enterprise_id=1,
            company_code="000001",
            company_name="测试公司",
            industry_name="制造业",
            report_years="2023",
            executive_summary=ExecutiveSummary(
                overall_rating="中",
                summary_text="这是一个测试报告。",
                recommendation="无建议。",
            ),
            financial_metrics=FinancialMetricsSection(
                profitability=[],
                solvency=[],
                operation=[],
                growth=[],
            ),
            risk_assessment=RiskAssessmentSection(
                overall_risk_level="中",
                financial_risk="一般",
                operational_risk="一般",
                market_risk="一般",
            ),
            recommendations=RecommendationsSection(
                strategic_recommendations=[],
                financial_recommendations=[],
                operational_recommendations=[],
                action_items=[],
            ),
        )

        doc_path = generator.generate(minimal_data)

        assert os.path.exists(doc_path)
        file_size = os.path.getsize(doc_path)
        assert file_size > 5000  # Smaller but still valid

    def test_generate_report_with_charts(self, tmp_path, sample_report_data):
        """Test that charts are embedded in the report."""
        generator = ReportGenerator(reports_dir=str(tmp_path))

        doc_path = generator.generate(sample_report_data)

        # File should be larger with charts
        file_size = os.path.getsize(doc_path)
        assert file_size > 50000  # Charts add significant size


class TestReportGeneratorHelperMethods:
    """Test helper methods."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a generator instance for testing."""
        return ReportGenerator(reports_dir=str(tmp_path))

    def test_format_decimal_none(self, generator):
        """Test formatting None decimal."""
        result = generator._format_decimal(None)
        assert result == "-"

    def test_format_decimal_value(self, generator):
        """Test formatting decimal value."""
        result = generator._format_decimal(Decimal("12345.67"))
        assert "12,345.67" in result

    def test_format_change_rate_none(self, generator):
        """Test formatting None change rate."""
        result = generator._format_change_rate(None)
        assert result == "-"

    def test_format_change_rate_positive(self, generator):
        """Test formatting positive change rate."""
        result = generator._format_change_rate(Decimal("5.5"))
        assert "+" in result
        assert "5.50" in result

    def test_format_change_rate_negative(self, generator):
        """Test formatting negative change rate."""
        result = generator._format_change_rate(Decimal("-3.2"))
        assert "-" in result
        assert "3.20" in result

    def test_get_report_path(self, generator):
        """Test getting report path."""
        path = generator.get_report_path("test.docx")
        assert str(path).endswith("test.docx")

    def test_cleanup_old_reports(self, generator):
        """Test cleanup of old reports."""
        import time

        # Create some test files
        old_file = generator.reports_dir / "old_report.docx"
        new_file = generator.reports_dir / "new_report.docx"

        old_file.write_bytes(b"test content")
        new_file.write_bytes(b"test content")

        # Set old file's mtime to 60 days ago
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        # Run cleanup
        deleted = generator.cleanup_old_reports(days_old=30)

        # Old file should be deleted, new file should remain
        assert deleted == 1
        assert not old_file.exists()
        assert new_file.exists()


class TestReportGeneratorExceptions:
    """Test exception handling."""

    def test_exception_is_exception(self):
        """Test ReportGeneratorError is an Exception."""
        assert issubclass(ReportGeneratorError, Exception)

    def test_exception_message(self):
        """Test exception message."""
        with pytest.raises(ReportGeneratorError) as exc_info:
            raise ReportGeneratorError("Test error")
        assert "Test error" in str(exc_info.value)


class TestChartData:
    """Test chart data creation."""

    def test_chart_data_creation(self):
        """Test creating ChartData."""
        chart = ChartData(
            chart_type="bar",
            title="Test Chart",
            x_labels=["A", "B", "C"],
            datasets=[
                {"label": "Series 1", "data": [1, 2, 3]},
                {"label": "Series 2", "data": [4, 5, 6]},
            ],
        )

        assert chart.chart_type == "bar"
        assert chart.title == "Test Chart"
        assert len(chart.datasets) == 2

    def test_trend_data_creation(self):
        """Test creating TrendData."""
        trend = TrendData(
            metric_name="Revenue",
            unit="万元",
            data=[
                YearlyMetric(year=2021, value=Decimal("1000")),
                YearlyMetric(year=2022, value=Decimal("1200")),
            ],
        )

        assert trend.metric_name == "Revenue"
        assert len(trend.data) == 2
