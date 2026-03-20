#!/usr/bin/env python3
"""
Verify imported financial data integrity.

Usage:
    python -m app.scripts.verify_financial_data
"""

import sys
import logging
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enterprise import Enterprise
from app.models.financial import BalanceSheet, IncomeStatement, CashFlowStatement

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def verify_data_integrity(db: Session) -> dict:
    """
    Verify the integrity of imported financial data.

    Returns:
        dict: Verification results with statistics and issues found.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_enterprises": 0,
        "enterprises_with_data": 0,
        "enterprises_missing_data": 0,
        "balance_sheet_count": 0,
        "income_statement_count": 0,
        "cashflow_statement_count": 0,
        "issues": [],
        "status": "pending",
    }

    # Get total enterprises
    total_enterprises = db.query(func.count(Enterprise.id)).scalar()
    results["total_enterprises"] = total_enterprises
    logger.info(f"Total enterprises in database: {total_enterprises}")

    # Count records in each table
    balance_count = db.query(func.count(BalanceSheet.id)).scalar()
    income_count = db.query(func.count(IncomeStatement.id)).scalar()
    cashflow_count = db.query(func.count(CashFlowStatement.id)).scalar()

    results["balance_sheet_count"] = balance_count
    results["income_statement_count"] = income_count
    results["cashflow_statement_count"] = cashflow_count

    logger.info(f"Balance sheets: {balance_count} records")
    logger.info(f"Income statements: {income_count} records")
    logger.info(f"Cash flow statements: {cashflow_count} records")

    # Get enterprises with data
    enterprises_with_balance = db.query(
        func.count(func.distinct(BalanceSheet.enterprise_id))
    ).scalar()

    enterprises_with_income = db.query(
        func.count(func.distinct(IncomeStatement.enterprise_id))
    ).scalar()

    enterprises_with_cashflow = db.query(
        func.count(func.distinct(CashFlowStatement.enterprise_id))
    ).scalar()

    results["enterprises_with_data"] = enterprises_with_balance

    # Check for enterprises missing any of the three statements
    if enterprises_with_balance != enterprises_with_income:
        issue = f"Data mismatch: {enterprises_with_balance} have balance sheets, but {enterprises_with_income} have income statements"
        results["issues"].append(issue)
        logger.warning(issue)

    if enterprises_with_balance != enterprises_with_cashflow:
        issue = f"Data mismatch: {enterprises_with_balance} have balance sheets, but {enterprises_with_cashflow} have cash flow statements"
        results["issues"].append(issue)
        logger.warning(issue)

    # Calculate missing enterprises
    results["enterprises_missing_data"] = total_enterprises - enterprises_with_balance

    # Check for enterprises with incomplete years (less than 5 years of data)
    enterprises_with_less_than_5_years = (
        db.query(BalanceSheet.enterprise_id)
        .group_by(BalanceSheet.enterprise_id)
        .having(func.count(BalanceSheet.id) < 4)
        .all()
    )

    if enterprises_with_less_than_5_years:
        issue = (
            f"{len(enterprises_with_less_than_5_years)} enterprises have less than 4 years of data"
        )
        results["issues"].append(issue)
        logger.warning(issue)

    # Determine status
    if results["enterprises_missing_data"] == 0 and len(results["issues"]) == 0:
        results["status"] = "complete"
        logger.info("✅ All enterprises have complete financial data!")
    elif results["enterprises_missing_data"] > 0:
        results["status"] = "incomplete"
        logger.warning(f"⚠️ {results['enterprises_missing_data']} enterprises missing data")
    else:
        results["status"] = "issues_found"
        logger.warning("⚠️ Data integrity issues found")

    return results


def print_summary(results: dict):
    """Print a formatted summary of verification results."""
    print("\n" + "=" * 60)
    print("FINANCIAL DATA VERIFICATION REPORT")
    print("=" * 60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Status: {results['status'].upper()}")
    print()
    print("ENTERPRISE STATISTICS:")
    print(f"  Total enterprises:     {results['total_enterprises']:,}")
    print(f"  With financial data:   {results['enterprises_with_data']:,}")
    print(f"  Missing data:          {results['enterprises_missing_data']:,}")
    print(
        f"  Coverage:              {results['enterprises_with_data'] / results['total_enterprises'] * 100:.1f}%"
    )
    print()
    print("RECORD COUNTS:")
    print(f"  Balance sheets:        {results['balance_sheet_count']:,}")
    print(f"  Income statements:     {results['income_statement_count']:,}")
    print(f"  Cash flow statements:  {results['cashflow_statement_count']:,}")
    print()

    if results["issues"]:
        print("ISSUES FOUND:")
        for issue in results["issues"]:
            print(f"  - {issue}")
    else:
        print("No issues found.")

    print("=" * 60)

    if results["status"] == "complete":
        print("✅ DATA VERIFICATION PASSED")
    elif results["status"] == "incomplete":
        print("⚠️ DATA IMPORT INCOMPLETE - Continue importing")
    else:
        print("⚠️ DATA INTEGRITY ISSUES - Review required")

    print("=" * 60 + "\n")


def main():
    """Run verification and print results."""
    db = SessionLocal()
    try:
        logger.info("Starting financial data verification...")
        results = verify_data_integrity(db)
        print_summary(results)

        # Exit with appropriate code
        if results["status"] == "complete":
            return 0
        elif results["status"] == "incomplete":
            return 1  # Import still in progress
        else:
            return 2  # Issues found

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 3
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
