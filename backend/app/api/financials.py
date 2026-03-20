"""
Financial data API routes.
Provides endpoints for querying balance sheets, income statements, and cash flow statements.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.models.enterprise import Enterprise
from app.models.financial import BalanceSheet, IncomeStatement, CashFlowStatement
from app.schemas.financial import (
    BalanceSheetResponse,
    BalanceSheetListResponse,
    IncomeStatementResponse,
    IncomeStatementListResponse,
    CashFlowStatementResponse,
    CashFlowStatementListResponse,
    EnterpriseFinancialSummary,
    EnterpriseFinancialSummaryList,
    EnterpriseFinancialDetail,
)
from app.api.deps import get_current_user


router = APIRouter()


# ==================== Balance Sheet Endpoints ====================


@router.get(
    "/balance-sheets",
    response_model=BalanceSheetListResponse,
    summary="List balance sheets",
)
def list_balance_sheets(
    enterprise_id: Optional[int] = Query(None, description="企业ID筛选"),
    company_code: Optional[str] = Query(None, description="公司代码筛选"),
    report_year: Optional[int] = Query(None, description="报告年度筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceSheetListResponse:
    """
    List balance sheets with pagination and filters.
    支持按企业ID、公司代码、报告年度筛选。
    """
    query = db.query(BalanceSheet)

    # Apply filters
    if enterprise_id:
        query = query.filter(BalanceSheet.enterprise_id == enterprise_id)
    elif company_code:
        enterprise = db.query(Enterprise).filter(Enterprise.company_code == company_code).first()
        if enterprise:
            query = query.filter(BalanceSheet.enterprise_id == enterprise.id)
        else:
            return BalanceSheetListResponse(
                items=[], total=0, page=page, page_size=page_size, pages=0
            )

    if report_year:
        query = query.filter(BalanceSheet.report_year == report_year)

    # Count total
    total = query.count()

    # Paginate and order
    offset = (page - 1) * page_size
    items = (
        query.order_by(BalanceSheet.enterprise_id, desc(BalanceSheet.report_date))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return BalanceSheetListResponse(
        items=[BalanceSheetResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/balance-sheets/{balance_sheet_id}",
    response_model=BalanceSheetResponse,
    summary="Get balance sheet by ID",
)
def get_balance_sheet(
    balance_sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceSheetResponse:
    """Get a specific balance sheet by ID."""
    item = db.query(BalanceSheet).filter(BalanceSheet.id == balance_sheet_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Balance sheet with id {balance_sheet_id} not found",
        )
    return BalanceSheetResponse.model_validate(item)


# ==================== Income Statement Endpoints ====================


@router.get(
    "/income-statements",
    response_model=IncomeStatementListResponse,
    summary="List income statements",
)
def list_income_statements(
    enterprise_id: Optional[int] = Query(None, description="企业ID筛选"),
    company_code: Optional[str] = Query(None, description="公司代码筛选"),
    report_year: Optional[int] = Query(None, description="报告年度筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeStatementListResponse:
    """
    List income statements with pagination and filters.
    支持按企业ID、公司代码、报告年度筛选。
    """
    query = db.query(IncomeStatement)

    # Apply filters
    if enterprise_id:
        query = query.filter(IncomeStatement.enterprise_id == enterprise_id)
    elif company_code:
        enterprise = db.query(Enterprise).filter(Enterprise.company_code == company_code).first()
        if enterprise:
            query = query.filter(IncomeStatement.enterprise_id == enterprise.id)
        else:
            return IncomeStatementListResponse(
                items=[], total=0, page=page, page_size=page_size, pages=0
            )

    if report_year:
        query = query.filter(IncomeStatement.report_year == report_year)

    # Count total
    total = query.count()

    # Paginate and order
    offset = (page - 1) * page_size
    items = (
        query.order_by(IncomeStatement.enterprise_id, desc(IncomeStatement.report_date))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return IncomeStatementListResponse(
        items=[IncomeStatementResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/income-statements/{income_statement_id}",
    response_model=IncomeStatementResponse,
    summary="Get income statement by ID",
)
def get_income_statement(
    income_statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeStatementResponse:
    """Get a specific income statement by ID."""
    item = db.query(IncomeStatement).filter(IncomeStatement.id == income_statement_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income statement with id {income_statement_id} not found",
        )
    return IncomeStatementResponse.model_validate(item)


# ==================== Cash Flow Statement Endpoints ====================


@router.get(
    "/cash-flow-statements",
    response_model=CashFlowStatementListResponse,
    summary="List cash flow statements",
)
def list_cash_flow_statements(
    enterprise_id: Optional[int] = Query(None, description="企业ID筛选"),
    company_code: Optional[str] = Query(None, description="公司代码筛选"),
    report_year: Optional[int] = Query(None, description="报告年度筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CashFlowStatementListResponse:
    """
    List cash flow statements with pagination and filters.
    支持按企业ID、公司代码、报告年度筛选。
    """
    query = db.query(CashFlowStatement)

    # Apply filters
    if enterprise_id:
        query = query.filter(CashFlowStatement.enterprise_id == enterprise_id)
    elif company_code:
        enterprise = db.query(Enterprise).filter(Enterprise.company_code == company_code).first()
        if enterprise:
            query = query.filter(CashFlowStatement.enterprise_id == enterprise.id)
        else:
            return CashFlowStatementListResponse(
                items=[], total=0, page=page, page_size=page_size, pages=0
            )

    if report_year:
        query = query.filter(CashFlowStatement.report_year == report_year)

    # Count total
    total = query.count()

    # Paginate and order
    offset = (page - 1) * page_size
    items = (
        query.order_by(CashFlowStatement.enterprise_id, desc(CashFlowStatement.report_date))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return CashFlowStatementListResponse(
        items=[CashFlowStatementResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/cash-flow-statements/{cash_flow_id}",
    response_model=CashFlowStatementResponse,
    summary="Get cash flow statement by ID",
)
def get_cash_flow_statement(
    cash_flow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CashFlowStatementResponse:
    """Get a specific cash flow statement by ID."""
    item = db.query(CashFlowStatement).filter(CashFlowStatement.id == cash_flow_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cash flow statement with id {cash_flow_id} not found",
        )
    return CashFlowStatementResponse.model_validate(item)


# ==================== Enterprise Financial Summary Endpoints ====================


@router.get(
    "/enterprises/summary",
    response_model=EnterpriseFinancialSummaryList,
    summary="List enterprises with financial data summary",
)
def list_enterprises_financial_summary(
    search: Optional[str] = Query(None, description="搜索公司代码或简称"),
    has_data: Optional[bool] = Query(None, description="是否有财务数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseFinancialSummaryList:
    """
    List enterprises with their financial data availability summary.
    显示每个企业的财务数据导入情况。
    """
    # Subqueries for counts
    balance_count_subq = (
        db.query(BalanceSheet.enterprise_id, func.count(BalanceSheet.id).label("count"))
        .group_by(BalanceSheet.enterprise_id)
        .subquery()
    )

    income_count_subq = (
        db.query(IncomeStatement.enterprise_id, func.count(IncomeStatement.id).label("count"))
        .group_by(IncomeStatement.enterprise_id)
        .subquery()
    )

    cashflow_count_subq = (
        db.query(CashFlowStatement.enterprise_id, func.count(CashFlowStatement.id).label("count"))
        .group_by(CashFlowStatement.enterprise_id)
        .subquery()
    )

    # Latest report date subquery
    latest_date_subq = (
        db.query(
            BalanceSheet.enterprise_id, func.max(BalanceSheet.report_date).label("latest_date")
        )
        .group_by(BalanceSheet.enterprise_id)
        .subquery()
    )

    # Main query
    query = (
        db.query(
            Enterprise.id.label("enterprise_id"),
            Enterprise.company_code,
            Enterprise.company_name,
            func.coalesce(balance_count_subq.c.count, 0).label("balance_sheet_count"),
            func.coalesce(income_count_subq.c.count, 0).label("income_statement_count"),
            func.coalesce(cashflow_count_subq.c.count, 0).label("cashflow_statement_count"),
            latest_date_subq.c.latest_date.label("latest_report_date"),
        )
        .outerjoin(balance_count_subq, Enterprise.id == balance_count_subq.c.enterprise_id)
        .outerjoin(income_count_subq, Enterprise.id == income_count_subq.c.enterprise_id)
        .outerjoin(cashflow_count_subq, Enterprise.id == cashflow_count_subq.c.enterprise_id)
        .outerjoin(latest_date_subq, Enterprise.id == latest_date_subq.c.enterprise_id)
    )

    # Apply filters
    if search:
        query = query.filter(
            (Enterprise.company_code.ilike(f"%{search}%"))
            | (Enterprise.company_name.ilike(f"%{search}%"))
        )

    if has_data is not None:
        if has_data:
            query = query.filter(balance_count_subq.c.count > 0)
        else:
            query = query.filter(func.coalesce(balance_count_subq.c.count, 0) == 0)

    # Count total
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    results = query.order_by(Enterprise.company_code).offset(offset).limit(page_size).all()

    items = [
        EnterpriseFinancialSummary(
            enterprise_id=r.enterprise_id,
            company_code=r.company_code,
            company_name=r.company_name,
            balance_sheet_count=r.balance_sheet_count or 0,
            income_statement_count=r.income_statement_count or 0,
            cashflow_statement_count=r.cashflow_statement_count or 0,
            latest_report_date=r.latest_report_date,
        )
        for r in results
    ]

    return EnterpriseFinancialSummaryList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/enterprises/{enterprise_id}",
    response_model=EnterpriseFinancialDetail,
    summary="Get complete financial data for an enterprise",
)
def get_enterprise_financial_detail(
    enterprise_id: int,
    years: int = Query(5, ge=1, le=10, description="获取最近N年数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseFinancialDetail:
    """
    Get complete financial data (all three statements) for a specific enterprise.
    获取指定企业的完整财务数据（三大报表）。
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )

    # Get balance sheets
    balance_sheets = (
        db.query(BalanceSheet)
        .filter(BalanceSheet.enterprise_id == enterprise_id)
        .order_by(desc(BalanceSheet.report_date))
        .limit(years)
        .all()
    )

    # Get income statements
    income_statements = (
        db.query(IncomeStatement)
        .filter(IncomeStatement.enterprise_id == enterprise_id)
        .order_by(desc(IncomeStatement.report_date))
        .limit(years)
        .all()
    )

    # Get cash flow statements
    cash_flow_statements = (
        db.query(CashFlowStatement)
        .filter(CashFlowStatement.enterprise_id == enterprise_id)
        .order_by(desc(CashFlowStatement.report_date))
        .limit(years)
        .all()
    )

    return EnterpriseFinancialDetail(
        enterprise_id=enterprise.id,
        company_code=enterprise.company_code,
        company_name=enterprise.company_name,
        balance_sheets=[BalanceSheetResponse.model_validate(bs) for bs in balance_sheets],
        income_statements=[
            IncomeStatementResponse.model_validate(is_) for is_ in income_statements
        ],
        cash_flow_statements=[
            CashFlowStatementResponse.model_validate(cf) for cf in cash_flow_statements
        ],
    )


@router.get(
    "/enterprises/code/{company_code}",
    response_model=EnterpriseFinancialDetail,
    summary="Get complete financial data by company code",
)
def get_enterprise_financial_detail_by_code(
    company_code: str,
    years: int = Query(5, ge=1, le=10, description="获取最近N年数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseFinancialDetail:
    """
    Get complete financial data by company code.
    通过公司代码获取完整财务数据。
    """
    enterprise = db.query(Enterprise).filter(Enterprise.company_code == company_code).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with code {company_code} not found",
        )

    return get_enterprise_financial_detail(enterprise.id, years, db, current_user)


# ==================== Global Statistics Endpoint ====================


class GlobalFinancialStats(BaseModel):
    """Global financial data statistics."""

    total_enterprises: int = Field(..., description="企业总数")
    enterprises_with_data: int = Field(..., description="有财务数据的企业数")
    data_coverage_rate: float = Field(..., description="数据覆盖率(%)")
    balance_sheet_records: int = Field(..., description="资产负债表记录数")
    income_statement_records: int = Field(..., description="利润表记录数")
    cashflow_statement_records: int = Field(..., description="现金流量表记录数")
    total_records: int = Field(..., description="财务报表总记录数")


@router.get(
    "/stats",
    response_model=GlobalFinancialStats,
    summary="Get global financial data statistics",
)
def get_global_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GlobalFinancialStats:
    """
    Get global statistics for all financial data.
    获取财务数据全局统计信息。
    """
    # Total enterprises
    total_enterprises = db.query(func.count(Enterprise.id)).scalar()

    # Enterprises with data (have at least one balance sheet)
    enterprises_with_data = db.query(func.count(func.distinct(BalanceSheet.enterprise_id))).scalar()

    # Record counts
    balance_sheet_records = db.query(func.count(BalanceSheet.id)).scalar()
    income_statement_records = db.query(func.count(IncomeStatement.id)).scalar()
    cashflow_statement_records = db.query(func.count(CashFlowStatement.id)).scalar()

    # Calculate coverage rate
    data_coverage_rate = (
        round(enterprises_with_data / total_enterprises * 100, 1) if total_enterprises > 0 else 0
    )

    return GlobalFinancialStats(
        total_enterprises=total_enterprises,
        enterprises_with_data=enterprises_with_data,
        data_coverage_rate=data_coverage_rate,
        balance_sheet_records=balance_sheet_records,
        income_statement_records=income_statement_records,
        cashflow_statement_records=cashflow_statement_records,
        total_records=balance_sheet_records + income_statement_records + cashflow_statement_records,
    )


# ==================== Enterprise Data Status & Update ====================


class EnterpriseDataStatus(BaseModel):
    """Enterprise financial data status."""

    enterprise_id: int
    company_code: str
    company_name: str
    has_data: bool = Field(..., description="是否有财务数据")
    latest_year: Optional[int] = Field(None, description="最新数据年度")
    earliest_year: Optional[int] = Field(None, description="最早数据年度")
    total_years: int = Field(0, description="数据年数")
    expected_years: int = Field(5, description="期望年数")
    missing_years: list[int] = Field(default_factory=list, description="缺失的年度")
    need_update: bool = Field(False, description="是否需要更新")
    status: str = Field("no_data", description="状态: no_data/partial/complete")


@router.get(
    "/enterprises/{enterprise_id}/status",
    response_model=EnterpriseDataStatus,
    summary="Get enterprise financial data status",
)
def get_enterprise_data_status(
    enterprise_id: int,
    years: int = Query(5, ge=1, le=10, description="期望的数据年数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseDataStatus:
    """
    Get the financial data status for a specific enterprise.
    获取指定企业的财务数据状态。
    """
    from datetime import datetime

    # Get enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )

    # Get existing years from balance sheets
    existing_years = [
        row[0]
        for row in db.query(BalanceSheet.report_year)
        .filter(BalanceSheet.enterprise_id == enterprise_id)
        .distinct()
        .all()
    ]

    # Calculate expected years (current year and previous years)
    current_year = datetime.now().year
    expected_years_set = set(range(current_year - years + 1, current_year + 1))

    # Calculate missing years
    existing_set = set(existing_years)
    missing_years = sorted(expected_years_set - existing_set, reverse=True)

    # Determine status
    if not existing_years:
        status = "no_data"
        has_data = False
        need_update = True
    elif len(existing_years) < years:
        status = "partial"
        has_data = True
        need_update = len(missing_years) > 0
    else:
        status = "complete"
        has_data = True
        need_update = False

    return EnterpriseDataStatus(
        enterprise_id=enterprise_id,
        company_code=enterprise.company_code,
        company_name=enterprise.company_name,
        has_data=has_data,
        latest_year=max(existing_years) if existing_years else None,
        earliest_year=min(existing_years) if existing_years else None,
        total_years=len(existing_years),
        expected_years=years,
        missing_years=missing_years,
        need_update=need_update,
        status=status,
    )


@router.post(
    "/enterprises/{enterprise_id}/refresh",
    summary="Refresh enterprise financial data",
)
def refresh_enterprise_data(
    enterprise_id: int,
    years: int = Query(5, ge=1, le=10, description="获取最近N年数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Refresh financial data for a specific enterprise.
    Only fetches missing years of data.
    刷新指定企业的财务数据，仅获取缺失年度的数据。
    """
    from app.services.batch_import import BatchImportService

    # Get enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )

    # Import data
    service = BatchImportService(db)
    result = service.import_enterprise_data_ths(enterprise, years=years, skip_existing=True)

    return {
        "enterprise_id": enterprise_id,
        "company_code": enterprise.company_code,
        "company_name": enterprise.company_name,
        "balance_count": result.get("balance_count", 0),
        "income_count": result.get("income_count", 0),
        "cashflow_count": result.get("cashflow_count", 0),
        "success": True,
        "message": f"成功更新 {result.get('balance_count', 0)} 条资产负债表、{result.get('income_count', 0)} 条利润表、{result.get('cashflow_count', 0)} 条现金流量表数据",
    }
