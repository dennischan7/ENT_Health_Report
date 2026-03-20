#!/usr/bin/env python3
"""
Import financial data using Tonghuashun API.
This script imports data for enterprises that don't have data yet,
specifically targeting Shanghai and ChiNext markets that Sina API fails to fetch.
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
    """Run THS import for remaining enterprises."""
    db = SessionLocal()

    try:
        service = BatchImportService(db)

        # Get remaining enterprises
        remaining = service.get_remaining_enterprises()
        total_remaining = len(remaining)

        if total_remaining == 0:
            logger.info("All enterprises have financial data!")
            return 0

        # Filter for Shanghai (6xx) and ChiNext (300/301) and STAR (688) markets
        target_enterprises = [
            e for e in remaining if e.company_code.startswith(("6", "300", "301", "688"))
        ]

        logger.info(
            f"Total remaining: {total_remaining}, Target markets: {len(target_enterprises)}"
        )

        if not target_enterprises:
            logger.info("No target market enterprises to import")
            return 0

        imported_count = 0
        failed_count = 0
        start_time = time.time()

        for i, enterprise in enumerate(target_enterprises):
            try:
                result = service.import_enterprise_data_ths(enterprise, years=5, skip_existing=True)

                if result["balance_count"] > 0 or result["income_count"] > 0:
                    imported_count += 1
                    logger.info(
                        f"[{i + 1}/{len(target_enterprises)}] Imported {enterprise.company_code}: "
                        f"balance={result['balance_count']}, income={result['income_count']}, cashflow={result['cashflow_count']}"
                    )
                else:
                    logger.debug(
                        f"[{i + 1}/{len(target_enterprises)}] No data for {enterprise.company_code}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"[{i + 1}/{len(target_enterprises)}] Failed {enterprise.company_code}: {e}"
                )

            # Progress report every 100 enterprises
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining_time = (len(target_enterprises) - i - 1) / rate if rate > 0 else 0
                logger.info(
                    f"Progress: {i + 1}/{len(target_enterprises)} ({100 * (i + 1) / len(target_enterprises):.1f}%) - "
                    f"Imported: {imported_count}, Failed: {failed_count} - "
                    f"Elapsed: {elapsed / 60:.1f}min, Remaining: {remaining_time / 60:.1f}min"
                )

        elapsed = time.time() - start_time
        logger.info(
            f"\n{'=' * 60}\n"
            f"THS Import completed!\n"
            f"Total: {len(target_enterprises)}\n"
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
