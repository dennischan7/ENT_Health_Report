#!/usr/bin/env python3
"""
Script to batch import financial data from AkShare.

This script imports financial statements (balance sheet, income statement,
cash flow statement) for all enterprises in the database.

Usage:
    # Import all enterprises (default: 5 years of data)
    python -m app.scripts.import_financial_data

    # Import specific enterprises
    python -m app.scripts.import_financial_data --codes 600519 000001

    # Import 3 years of data
    python -m app.scripts.import_financial_data --years 3

    # Resume from a specific index
    python -m app.scripts.import_financial_data --start-from 500

    # Show import status only
    python -m app.scripts.import_financial_data --status

    # Use custom rate limit delay
    python -m app.scripts.import_financial_data --delay 1.0
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.batch_import import BatchImportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("import_financial_data.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print script banner."""
    print("\n" + "=" * 60)
    print("  Enterprise Financial Data Batch Import")
    print("  Source: AkShare (East Money Data)")
    print("=" * 60 + "\n")


def print_status(service: BatchImportService):
    """Print current import status."""
    status = service.get_import_status()

    print("\n" + "-" * 40)
    print("  Import Status")
    print("-" * 40)
    print(f"  Total Enterprises:             {status['total_enterprises']:,}")
    print(f"  With Balance Sheet:            {status['enterprises_with_balance_sheet']:,}")
    print(f"  With Income Statement:         {status['enterprises_with_income_statement']:,}")
    print(f"  With Cash Flow Statement:      {status['enterprises_with_cashflow_statement']:,}")
    print("-" * 40)
    print(f"  Balance Sheet Records:         {status['balance_sheet_records']:,}")
    print(f"  Income Statement Records:      {status['income_statement_records']:,}")
    print(f"  Cash Flow Statement Records:   {status['cashflow_statement_records']:,}")
    print("-" * 40 + "\n")


def print_result(result: dict):
    """Print import result summary."""
    print("\n" + "=" * 60)
    print("  BATCH IMPORT COMPLETE")
    print("=" * 60)
    print(f"  Total enterprises:      {result['total']:,}")
    print(f"  Successful:             {result['success']:,}")
    print(f"  Failed:                 {result['failed']:,}")
    print(f"  Elapsed time:           {result['elapsed_time']:.1f}s")

    if result["total"] > 0:
        avg_time = result["elapsed_time"] / result["total"]
        print(f"  Average time/enterprise: {avg_time:.2f}s")

    print("=" * 60)

    if result["errors"]:
        print("\n  Errors (first 10):")
        for error in result["errors"][:10]:
            print(f"    - {error['company_code']}: {error['error']}")
        if len(result["errors"]) > 10:
            print(f"    ... and {len(result['errors']) - 10} more errors")


def main():
    """Run batch import."""
    parser = argparse.ArgumentParser(description="Batch import financial data from AkShare")
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Number of years of historical data to import (default: 5)",
    )
    parser.add_argument(
        "--codes",
        nargs="+",
        help="Specific enterprise codes to import (space-separated)",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Index to start from (for resuming interrupted import)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of enterprises to process in this run",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Rate limit delay in seconds between API calls (default: 0.5)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current import status and exit",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Do not skip existing records (will cause errors on duplicates)",
    )

    args = parser.parse_args()

    print_banner()

    db = SessionLocal()
    try:
        service = BatchImportService(db, rate_limit_delay=args.delay)

        # Show status only
        if args.status:
            print_status(service)
            return 0

        # Run import
        logger.info(
            f"Starting import: years={args.years}, delay={args.delay}s, "
            f"start_from={args.start_from}, codes={args.codes}"
        )

        result = service.run_batch_import(
            years=args.years,
            skip_existing=not args.no_skip_existing,
            batch_size=args.batch_size,
            start_from=args.start_from,
            enterprise_codes=args.codes,
        )

        print_result(result)
        print_status(service)

        # Write errors to file if any
        if result["errors"]:
            error_file = Path("import_errors.txt")
            with open(error_file, "w", encoding="utf-8") as f:
                for error in result["errors"]:
                    f.write(f"{error['company_code']}\t{error['error']}\n")
            logger.info(f"Error details written to {error_file}")

        return 0 if result["failed"] == 0 else 1

    except KeyboardInterrupt:
        logger.warning("Import interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Batch import failed: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
