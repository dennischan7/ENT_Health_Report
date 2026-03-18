"""
Batch import service for importing financial data from AkShare.

This module provides functionality to batch import financial statements
(balance sheet, income statement, cash flow statement) for all enterprises
from the AkShare data source.
"""

import logging
import time
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from app.models.enterprise import Enterprise
from app.models.financial import BalanceSheet, IncomeStatement, CashFlowStatement
from app.services.akshare_client import AkShareFinancialClient
from app.services.data_cleaner import (
    transform_balance_sheet,
    transform_income_statement,
    transform_cashflow_statement,
    transform_balance_sheet_ths,
    transform_income_statement_ths,
    transform_cashflow_statement_ths,
)

logger = logging.getLogger(__name__)


# Field mapping from data_cleaner output to IncomeStatement model fields
INCOME_STATEMENT_FIELD_MAP = {
    "operating_revenue": "operating_revenue",
    "operating_cost": "operating_cost",
    "selling_expenses": "selling_expenses",
    "administrative_expenses": "admin_expenses",  # Different name in model
    "rd_expenses": None,  # Not in current model
    "financial_expenses": "financial_expenses",
    "operating_profit": "operating_profit",
    "total_profit": "total_profit",
    "income_tax_expense": "income_tax",  # Different name in model
    "net_profit": "net_profit",
    "net_profit_parent": "net_profit_parent",
    "basic_eps": "basic_eps",
    "total_revenue": None,  # Not in current model
}

# Field mapping from data_cleaner output to CashFlowStatement model fields
CASHFLOW_STATEMENT_FIELD_MAP = {
    "operating_cash_inflow": None,  # Different granularity in model
    "operating_cash_outflow": None,  # Different granularity in model
    "operating_cash_flow": "net_cash_operating",
    "investing_cash_inflow": None,  # Different granularity in model
    "investing_cash_outflow": None,  # Different granularity in model
    "investing_cash_flow": "net_cash_investing",
    "financing_cash_inflow": None,  # Different granularity in model
    "financing_cash_outflow": None,  # Different granularity in model
    "financing_cash_flow": "net_cash_financing",
    "cash_increase": "net_cash_increase",
    "ending_cash": "cash_end_period",
}


class BatchImportService:
    """
    Service for batch importing financial data from AkShare.

    This service handles:
    - Fetching financial data via AkShare
    - Transforming and cleaning data
    - Importing to database with error handling
    - Resume support (skipping existing records)
    - Progress tracking and statistics

    Attributes:
        db: SQLAlchemy database session.
        client: AkShare financial client.
        stats: Import statistics dictionary.

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> service = BatchImportService(db)
        >>> result = service.run_batch_import(years=5)
    """

    def __init__(self, db: Session, rate_limit_delay: float = 0.0):
        """
        Initialize the batch import service.

        Args:
            db: SQLAlchemy database session.
            rate_limit_delay: DEPRECATED - No longer used. Sina API is lenient.
        """
        self.db = db
        self.client = AkShareFinancialClient(
            rate_limit_delay=rate_limit_delay
        )  # Backward compatible
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

    def get_all_enterprises(self) -> List[Enterprise]:
        """
        Get all enterprises from database.

        Returns:
            List of all Enterprise records.
        """
        return self.db.query(Enterprise).order_by(Enterprise.company_code).all()

    def get_enterprises_batch(self, offset: int = 0, limit: int = 100) -> List[Enterprise]:
        """
        Get a batch of enterprises for incremental processing.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Enterprise records.
        """
        return (
            self.db.query(Enterprise)
            .order_by(Enterprise.company_code)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def check_existing_data(self, enterprise_id: int, model_class: type, years: int = 5) -> set:
        """
        Check which report dates already exist for an enterprise.

        Args:
            enterprise_id: ID of the enterprise.
            model_class: SQLAlchemy model class (BalanceSheet, IncomeStatement, etc.)
            years: Number of years to check.

        Returns:
            Set of existing report dates.
        """
        current_year = datetime.now().year
        start_year = current_year - years

        existing = (
            self.db.query(model_class.report_date)
            .filter(
                and_(
                    model_class.enterprise_id == enterprise_id,
                    model_class.report_year >= start_year,
                )
            )
            .all()
        )

        return {row[0] for row in existing}

    def import_enterprise_data(
        self,
        enterprise: Enterprise,
        years: int = 5,
        skip_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Import financial data for a single enterprise.

        This method fetches all three financial statements (balance sheet,
        income statement, cash flow statement) and imports them to the database.

        Args:
            enterprise: Enterprise model instance.
            years: Number of years of historical data to import.
            skip_existing: Whether to skip records that already exist.

        Returns:
            Dictionary with import results:
            - success: Boolean indicating overall success
            - enterprise_id: ID of the enterprise
            - company_code: Stock code of the enterprise
            - balance_count: Number of balance sheet records imported
            - income_count: Number of income statement records imported
            - cashflow_count: Number of cash flow records imported
            - error: Error message if failed
        """
        result = {
            "success": False,
            "enterprise_id": enterprise.id,
            "company_code": enterprise.company_code,
            "company_name": enterprise.company_name,
            "balance_count": 0,
            "income_count": 0,
            "cashflow_count": 0,
            "skipped_count": 0,
            "error": None,
        }

        try:
            logger.info(f"Importing data for {enterprise.company_code} - {enterprise.company_name}")

            # Fetch all three statements in parallel (3x faster than sequential)
            statements = self.client.fetch_all_statements_parallel(enterprise.company_code)

            # Transform data
            balance_df = transform_balance_sheet(statements["balance_sheet"], years=years)
            income_df = transform_income_statement(statements["income_statement"], years=years)
            cashflow_df = transform_cashflow_statement(statements["cash_flow"], years=years)

            # Check existing data if skip_existing is enabled
            existing_balance = set()
            existing_income = set()
            existing_cashflow = set()

            if skip_existing:
                existing_balance = self.check_existing_data(enterprise.id, BalanceSheet, years)
                existing_income = self.check_existing_data(enterprise.id, IncomeStatement, years)
                existing_cashflow = self.check_existing_data(
                    enterprise.id, CashFlowStatement, years
                )

            # Import to database
            balance_count, balance_skipped = self._import_balance_sheets(
                enterprise.id, balance_df, existing_balance
            )
            income_count, income_skipped = self._import_income_statements(
                enterprise.id, income_df, existing_income
            )
            cashflow_count, cashflow_skipped = self._import_cashflow_statements(
                enterprise.id, cashflow_df, existing_cashflow
            )

            self.db.commit()

            result.update(
                {
                    "success": True,
                    "balance_count": balance_count,
                    "income_count": income_count,
                    "cashflow_count": cashflow_count,
                    "skipped_count": balance_skipped + income_skipped + cashflow_skipped,
                }
            )

            logger.info(
                f"Successfully imported {enterprise.company_code}: "
                f"balance={balance_count}, income={income_count}, cashflow={cashflow_count}"
            )

        except Exception as e:
            self.db.rollback()
            error_msg = str(e)
            logger.error(f"Failed to import {enterprise.company_code}: {error_msg}")
            result["error"] = error_msg

        return result

    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """
        Safely convert a value to Decimal.

        Args:
            value: Value to convert.

        Returns:
            Decimal value or None if conversion fails.
        """
        if value is None or pd.isna(value):
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

    def _import_balance_sheets(
        self,
        enterprise_id: int,
        df: pd.DataFrame,
        existing_dates: set,
    ) -> tuple[int, int]:
        """
        Import balance sheet data to database using bulk insert.

        Args:
            enterprise_id: ID of the enterprise.
            df: DataFrame with transformed balance sheet data.
            existing_dates: Set of existing report dates to skip.

        Returns:
            Tuple of (imported_count, skipped_count).
        """
        if df.empty:
            return 0, 0

        records = []
        skipped = 0

        for _, row in df.iterrows():
            report_date = row.get("report_date")

            # Skip if already exists
            if report_date in existing_dates:
                skipped += 1
                continue

            # Convert report_date to date if it's a Timestamp
            if isinstance(report_date, pd.Timestamp):
                report_date = report_date.date()

            records.append(
                {
                    "enterprise_id": enterprise_id,
                    "report_date": report_date,
                    "report_year": int(row.get("report_year", report_date.year)),
                    "cash": self._safe_decimal(row.get("cash")),
                    "trading_financial_assets": self._safe_decimal(
                        row.get("trading_financial_assets")
                    ),
                    "accounts_receivable": self._safe_decimal(row.get("accounts_receivable")),
                    "inventory": self._safe_decimal(row.get("inventory")),
                    "total_current_assets": self._safe_decimal(row.get("total_current_assets")),
                    "fixed_assets": self._safe_decimal(row.get("fixed_assets")),
                    "total_assets": self._safe_decimal(row.get("total_assets")),
                    "short_term_borrowings": self._safe_decimal(row.get("short_term_borrowings")),
                    "accounts_payable": self._safe_decimal(row.get("accounts_payable")),
                    "total_current_liabilities": self._safe_decimal(
                        row.get("total_current_liabilities")
                    ),
                    "long_term_borrowings": self._safe_decimal(row.get("long_term_borrowings")),
                    "total_liabilities": self._safe_decimal(row.get("total_liabilities")),
                    "paid_in_capital": self._safe_decimal(row.get("paid_in_capital")),
                    "retained_earnings": self._safe_decimal(row.get("retained_earnings")),
                    "total_equity": self._safe_decimal(row.get("total_equity")),
                }
            )

        if records:
            self.db.bulk_insert_mappings(BalanceSheet, records)

        return len(records), skipped

    def _import_income_statements(
        self,
        enterprise_id: int,
        df: pd.DataFrame,
        existing_dates: set,
    ) -> tuple[int, int]:
        """
        Import income statement data to database using bulk insert.

        Maps data_cleaner output fields to IncomeStatement model fields.

        Args:
            enterprise_id: ID of the enterprise.
            df: DataFrame with transformed income statement data.
            existing_dates: Set of existing report dates to skip.

        Returns:
            Tuple of (imported_count, skipped_count).
        """
        if df.empty:
            return 0, 0

        records = []
        skipped = 0

        for _, row in df.iterrows():
            report_date = row.get("report_date")

            # Skip if already exists
            if report_date in existing_dates:
                skipped += 1
                continue

            # Convert report_date to date if it's a Timestamp
            if isinstance(report_date, pd.Timestamp):
                report_date = report_date.date()

            records.append(
                {
                    "enterprise_id": enterprise_id,
                    "report_date": report_date,
                    "report_year": int(row.get("report_year", report_date.year)),
                    "operating_revenue": self._safe_decimal(row.get("operating_revenue")),
                    "operating_cost": self._safe_decimal(row.get("operating_cost")),
                    "selling_expenses": self._safe_decimal(row.get("selling_expenses")),
                    "admin_expenses": self._safe_decimal(
                        row.get("administrative_expenses")
                    ),  # Mapped field
                    "financial_expenses": self._safe_decimal(row.get("financial_expenses")),
                    "operating_profit": self._safe_decimal(row.get("operating_profit")),
                    "total_profit": self._safe_decimal(row.get("total_profit")),
                    "income_tax": self._safe_decimal(row.get("income_tax_expense")),  # Mapped field
                    "net_profit": self._safe_decimal(row.get("net_profit")),
                    "net_profit_parent": self._safe_decimal(row.get("net_profit_parent")),
                    "basic_eps": self._safe_decimal(row.get("basic_eps")),
                }
            )

        if records:
            self.db.bulk_insert_mappings(IncomeStatement, records)

        return len(records), skipped

    def _import_cashflow_statements(
        self,
        enterprise_id: int,
        df: pd.DataFrame,
        existing_dates: set,
    ) -> tuple[int, int]:
        """
        Import cash flow statement data to database using bulk insert.

        Maps data_cleaner output fields to CashFlowStatement model fields.

        Args:
            enterprise_id: ID of the enterprise.
            df: DataFrame with transformed cash flow data.
            existing_dates: Set of existing report dates to skip.

        Returns:
            Tuple of (imported_count, skipped_count).
        """
        if df.empty:
            return 0, 0

        records = []
        skipped = 0

        for _, row in df.iterrows():
            report_date = row.get("report_date")

            # Skip if already exists
            if report_date in existing_dates:
                skipped += 1
                continue

            # Convert report_date to date if it's a Timestamp
            if isinstance(report_date, pd.Timestamp):
                report_date = report_date.date()

            records.append(
                {
                    "enterprise_id": enterprise_id,
                    "report_date": report_date,
                    "report_year": int(row.get("report_year", report_date.year)),
                    "net_cash_operating": self._safe_decimal(
                        row.get("operating_cash_flow")
                    ),  # Mapped field
                    "net_cash_investing": self._safe_decimal(
                        row.get("investing_cash_flow")
                    ),  # Mapped field
                    "net_cash_financing": self._safe_decimal(
                        row.get("financing_cash_flow")
                    ),  # Mapped field
                    "net_cash_increase": self._safe_decimal(
                        row.get("cash_increase")
                    ),  # Mapped field
                    "cash_end_period": self._safe_decimal(row.get("ending_cash")),  # Mapped field
                }
            )

        if records:
            self.db.bulk_insert_mappings(CashFlowStatement, records)

        return len(records), skipped

    def run_batch_import(
        self,
        years: int = 5,
        skip_existing: bool = True,
        batch_size: int = None,
        start_from: int = 0,
        enterprise_codes: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Run batch import for all enterprises.

        This method imports financial data for all enterprises in the database,
        with support for resuming interrupted imports and filtering by stock codes.

        Args:
            years: Number of years of historical data to import.
            skip_existing: Whether to skip records that already exist.
            batch_size: Number of enterprises to process at once (None = all).
            start_from: Index to start from (for resuming).
            enterprise_codes: Optional list of specific enterprise codes to import.

        Returns:
            Dictionary with import statistics:
            - total: Total number of enterprises processed
            - success: Number of successful imports
            - failed: Number of failed imports
            - skipped: Number of enterprises skipped
            - elapsed_time: Total time in seconds
            - errors: List of error details for failed imports
        """
        # Get enterprises to process
        if enterprise_codes:
            enterprises = (
                self.db.query(Enterprise)
                .filter(Enterprise.company_code.in_(enterprise_codes))
                .all()
            )
        elif batch_size:
            enterprises = self.get_enterprises_batch(start_from, batch_size)
        else:
            enterprises = self.get_all_enterprises()

        self.stats["total"] = len(enterprises)
        self.stats["errors"] = []

        if not enterprises:
            logger.warning("No enterprises found to import")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "elapsed_time": 0,
                "errors": [],
            }

        logger.info(f"Starting batch import for {len(enterprises)} enterprises")
        start_time = time.time()

        for i, enterprise in enumerate(enterprises):
            result = self.import_enterprise_data(
                enterprise, years=years, skip_existing=skip_existing
            )

            if result["success"]:
                self.stats["success"] += 1
            else:
                self.stats["failed"] += 1
                self.stats["errors"].append(
                    {
                        "company_code": result["company_code"],
                        "error": result.get("error", "Unknown error"),
                    }
                )

            # Progress logging every 100 enterprises
            if (i + 1) % 100 == 0:
                progress = (i + 1) / len(enterprises) * 100
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                remaining = avg_time * (len(enterprises) - i - 1)
                logger.info(
                    f"Progress: {progress:.1f}% ({i + 1}/{len(enterprises)}) - "
                    f"Elapsed: {elapsed:.0f}s - Est. remaining: {remaining:.0f}s"
                )

        elapsed = time.time() - start_time

        logger.info(
            f"Batch import completed in {elapsed:.0f}s - "
            f"Success: {self.stats['success']}, Failed: {self.stats['failed']}"
        )

        return {
            "total": self.stats["total"],
            "success": self.stats["success"],
            "failed": self.stats["failed"],
            "skipped": self.stats["skipped"],
            "elapsed_time": elapsed,
            "errors": self.stats["errors"][:100],  # Limit error list size
        }

    def import_single_enterprise(self, company_code: str, years: int = 5) -> Dict[str, Any]:
        """
        Import financial data for a single enterprise by company code.

        Convenience method to import data for a specific enterprise.

        Args:
            company_code: Stock code of the enterprise.
            years: Number of years of historical data to import.

        Returns:
            Dictionary with import results.
        """
        enterprise = (
            self.db.query(Enterprise).filter(Enterprise.company_code == company_code).first()
        )

        if not enterprise:
            return {
                "success": False,
                "error": f"Enterprise with code {company_code} not found",
            }

        return self.import_enterprise_data(enterprise, years=years)

    def get_import_status(self) -> Dict[str, Any]:
        """
        Get current import status and statistics.

        Returns:
            Dictionary with import statistics.
        """
        total_enterprises = self.db.query(Enterprise).count()
        enterprises_with_balance = self.db.query(BalanceSheet.enterprise_id).distinct().count()
        enterprises_with_income = self.db.query(IncomeStatement.enterprise_id).distinct().count()
        enterprises_with_cashflow = (
            self.db.query(CashFlowStatement.enterprise_id).distinct().count()
        )

        return {
            "total_enterprises": total_enterprises,
            "enterprises_with_balance_sheet": enterprises_with_balance,
            "enterprises_with_income_statement": enterprises_with_income,
            "enterprises_with_cashflow_statement": enterprises_with_cashflow,
            "balance_sheet_records": self.db.query(BalanceSheet).count(),
            "income_statement_records": self.db.query(IncomeStatement).count(),
            "cashflow_statement_records": self.db.query(CashFlowStatement).count(),
        }

    # ==================== Tonghuashun API Methods ====================

    def get_imported_enterprise_ids(self) -> set:
        """
        Get IDs of enterprises that already have financial data imported.

        An enterprise is considered "imported" if it has at least one
        balance sheet record in the database.

        Returns:
            Set of enterprise IDs that have existing financial data.
        """
        result = self.db.query(BalanceSheet.enterprise_id).distinct().all()
        return {r[0] for r in result}

    def get_remaining_enterprises(self) -> List[Enterprise]:
        """
        Get enterprises that don't have financial data yet.

        Returns:
            List of Enterprise records without financial data.
        """
        imported_ids = self.get_imported_enterprise_ids()
        if imported_ids:
            return (
                self.db.query(Enterprise)
                .filter(~Enterprise.id.in_(imported_ids))
                .order_by(Enterprise.company_code)
                .all()
            )
        else:
            return self.get_all_enterprises()

    def import_enterprise_data_ths(
        self,
        enterprise: Enterprise,
        years: int = 5,
        skip_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Import financial data for a single enterprise using Tonghuashun API.

        This method fetches all three financial statements (balance sheet,
        income statement, cash flow statement) from THS and imports them to the database.

        Args:
            enterprise: Enterprise model instance.
            years: Number of years of historical data to import.
            skip_existing: Whether to skip records that already exist.

        Returns:
            Dictionary with import results:
            - success: Boolean indicating overall success
            - enterprise_id: ID of the enterprise
            - company_code: Stock code of the enterprise
            - balance_count: Number of balance sheet records imported
            - income_count: Number of income statement records imported
            - cashflow_count: Number of cash flow records imported
            - error: Error message if failed
        """
        result = {
            "success": False,
            "enterprise_id": enterprise.id,
            "company_code": enterprise.company_code,
            "company_name": enterprise.company_name,
            "balance_count": 0,
            "income_count": 0,
            "cashflow_count": 0,
            "skipped_count": 0,
            "error": None,
        }

        try:
            logger.info(
                f"Importing data (THS) for {enterprise.company_code} - {enterprise.company_name}"
            )

            # Fetch all three statements using THS API
            statements = self.client.fetch_all_statements_ths_parallel(enterprise.company_code)

            # Transform data using THS transform functions
            balance_df = transform_balance_sheet_ths(statements["balance_sheet"], years=years)
            income_df = transform_income_statement_ths(statements["income_statement"], years=years)
            cashflow_df = transform_cashflow_statement_ths(statements["cash_flow"], years=years)

            # Check existing data if skip_existing is enabled
            existing_balance = set()
            existing_income = set()
            existing_cashflow = set()

            if skip_existing:
                existing_balance = self.check_existing_data(enterprise.id, BalanceSheet, years)
                existing_income = self.check_existing_data(enterprise.id, IncomeStatement, years)
                existing_cashflow = self.check_existing_data(
                    enterprise.id, CashFlowStatement, years
                )

            # Import to database
            balance_count, balance_skipped = self._import_balance_sheets(
                enterprise.id, balance_df, existing_balance
            )
            income_count, income_skipped = self._import_income_statements(
                enterprise.id, income_df, existing_income
            )
            cashflow_count, cashflow_skipped = self._import_cashflow_statements(
                enterprise.id, cashflow_df, existing_cashflow
            )

            self.db.commit()

            result.update(
                {
                    "success": True,
                    "balance_count": balance_count,
                    "income_count": income_count,
                    "cashflow_count": cashflow_count,
                    "skipped_count": balance_skipped + income_skipped + cashflow_skipped,
                }
            )

            logger.info(
                f"Successfully imported (THS) {enterprise.company_code}: "
                f"balance={balance_count}, income={income_count}, cashflow={cashflow_count}"
            )

        except Exception as e:
            self.db.rollback()
            error_msg = str(e)
            logger.error(f"Failed to import (THS) {enterprise.company_code}: {error_msg}")
            result["error"] = error_msg

        return result

    def run_batch_import_ths(
        self,
        years: int = 5,
        skip_existing: bool = True,
        skip_imported_enterprises: bool = True,
        batch_size: int = None,
        start_from: int = 0,
        enterprise_codes: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Run batch import using Tonghuashun API.

        This method imports financial data for enterprises using THS API,
        with support for skipping enterprises that already have data.

        Args:
            years: Number of years of historical data to import.
            skip_existing: Whether to skip records that already exist.
            skip_imported_enterprises: Whether to skip enterprises that already have data.
            batch_size: Number of enterprises to process at once (None = all).
            start_from: Index to start from (for resuming).
            enterprise_codes: Optional list of specific enterprise codes to import.

        Returns:
            Dictionary with import statistics:
            - total: Total number of enterprises processed
            - success: Number of successful imports
            - failed: Number of failed imports
            - skipped_enterprises: Number of enterprises skipped (already imported)
            - elapsed_time: Total time in seconds
            - errors: List of error details for failed imports
        """
        # Get enterprises to process
        if enterprise_codes:
            enterprises = (
                self.db.query(Enterprise)
                .filter(Enterprise.company_code.in_(enterprise_codes))
                .all()
            )
        elif skip_imported_enterprises:
            # Skip enterprises that already have financial data
            enterprises = self.get_remaining_enterprises()
            logger.info(f"Skipping {86 - len(enterprises)} enterprises with existing data")
        elif batch_size:
            enterprises = self.get_enterprises_batch(start_from, batch_size)
        else:
            enterprises = self.get_all_enterprises()

        self.stats["total"] = len(enterprises)
        self.stats["errors"] = []
        skipped_enterprises = 0

        if not enterprises:
            logger.warning("No enterprises found to import")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped_enterprises": 0,
                "elapsed_time": 0,
                "errors": [],
            }

        logger.info(f"Starting THS batch import for {len(enterprises)} enterprises")
        start_time = time.time()

        for i, enterprise in enumerate(enterprises):
            result = self.import_enterprise_data_ths(
                enterprise, years=years, skip_existing=skip_existing
            )

            if result["success"]:
                self.stats["success"] += 1
            else:
                self.stats["failed"] += 1
                self.stats["errors"].append(
                    {
                        "company_code": result["company_code"],
                        "error": result.get("error", "Unknown error"),
                    }
                )

            # Progress logging every 50 enterprises
            if (i + 1) % 50 == 0:
                progress = (i + 1) / len(enterprises) * 100
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                remaining = avg_time * (len(enterprises) - i - 1)
                logger.info(
                    f"Progress: {progress:.1f}% ({i + 1}/{len(enterprises)}) - "
                    f"Elapsed: {elapsed:.0f}s - Est. remaining: {remaining:.0f}s"
                )

        elapsed = time.time() - start_time

        # Calculate skipped enterprises
        if skip_imported_enterprises and not enterprise_codes:
            total_enterprises = self.db.query(Enterprise).count()
            skipped_enterprises = total_enterprises - len(enterprises)

        logger.info(
            f"THS Batch import completed in {elapsed:.0f}s - "
            f"Success: {self.stats['success']}, Failed: {self.stats['failed']}, "
            f"Skipped: {skipped_enterprises}"
        )

        return {
            "total": self.stats["total"],
            "success": self.stats["success"],
            "failed": self.stats["failed"],
            "skipped_enterprises": skipped_enterprises,
            "elapsed_time": elapsed,
            "errors": self.stats["errors"][:100],  # Limit error list size
        }
