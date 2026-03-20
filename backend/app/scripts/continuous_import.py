#!/usr/bin/env python3
"""
Continuous import script for remaining enterprises.
Imports financial data for enterprises that don't have data yet.
"""

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.batch_import import BatchImportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    """Run continuous import for remaining enterprises."""
    db = SessionLocal()

    try:
        service = BatchImportService(db)

        # Get remaining enterprises
        remaining = service.get_remaining_enterprises()
        total_remaining = len(remaining)

        if total_remaining == 0:
            logger.info("All enterprises have financial data!")
            return 0

        logger.info(f"Starting import for {total_remaining} remaining enterprises")

        imported_count = 0
        failed_count = 0
        start_time = time.time()

        for i, enterprise in enumerate(remaining):
            try:
                result = service.import_enterprise_data(enterprise, years=5, skip_existing=True)

                if result["balance_count"] > 0:
                    imported_count += 1
                    logger.info(
                        f"[{i + 1}/{total_remaining}] Imported {enterprise.company_code}: "
                        f"balance={result['balance_count']}, income={result['income_count']}, cashflow={result['cashflow_count']}"
                    )
                else:
                    # No data (ST/delisted stocks)
                    logger.debug(
                        f"[{i + 1}/{total_remaining}] No data for {enterprise.company_code}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f"[{i + 1}/{total_remaining}] Failed {enterprise.company_code}: {e}")

            # Progress report every 100 enterprises
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining_time = (total_remaining - i - 1) / rate if rate > 0 else 0
                logger.info(
                    f"Progress: {i + 1}/{total_remaining} ({100 * (i + 1) / total_remaining:.1f}%) - "
                    f"Imported: {imported_count}, Failed: {failed_count} - "
                    f"Elapsed: {elapsed / 60:.1f}min, Remaining: {remaining_time / 60:.1f}min"
                )

        elapsed = time.time() - start_time
        logger.info(
            f"\n{'=' * 60}\n"
            f"Import completed!\n"
            f"Total: {total_remaining}\n"
            f"Imported: {imported_count}\n"
            f"Failed: {failed_count}\n"
            f"Elapsed: {elapsed / 60:.1f} minutes\n"
            f"{'=' * 60}"
        )

        return 0 if failed_count == 0 else 1

    except KeyboardInterrupt:
        logger.info("\nImport interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
