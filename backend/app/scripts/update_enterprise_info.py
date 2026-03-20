#!/usr/bin/env python3
"""
Script to update all enterprise information from AkShare.
This fetches detailed company information for all enterprises in the database.
"""

import sys
import time
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.enterprise import Enterprise
from app.services.enterprise_info import fetch_enterprise_info

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def update_all_enterprises():
    """Update information for all enterprises."""
    db = SessionLocal()

    try:
        # Get all enterprises
        enterprises = db.query(Enterprise).all()
        total = len(enterprises)

        logger.info(f"Starting update for {total} enterprises")

        updated_count = 0
        failed_count = 0
        skipped_count = 0

        for i, enterprise in enumerate(enterprises, 1):
            # Check if already has info
            if enterprise.legal_representative:
                logger.debug(f"[{i}/{total}] Skipping {enterprise.company_code} - already has data")
                skipped_count += 1
                continue

            try:
                logger.info(
                    f"[{i}/{total}] Fetching info for {enterprise.company_code} - {enterprise.company_name}"
                )

                # Fetch info from AkShare
                info = fetch_enterprise_info(enterprise.company_code)

                if info:
                    # Update enterprise fields
                    for key, value in info.items():
                        if value is not None:
                            setattr(enterprise, key, value)

                    db.commit()
                    updated_count += 1
                    logger.info(f"  ✓ Updated {enterprise.company_code}")
                else:
                    failed_count += 1
                    logger.warning(f"  ✗ No data found for {enterprise.company_code}")

                # Sleep to avoid rate limiting
                time.sleep(0.5)

                # Progress log every 100 companies
                if i % 100 == 0:
                    logger.info(
                        f"Progress: {i}/{total} - Updated: {updated_count}, Failed: {failed_count}, Skipped: {skipped_count}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f"  ✗ Error updating {enterprise.company_code}: {e}")
                db.rollback()
                continue

        logger.info(f"\n{'=' * 60}")
        logger.info(f"Update completed!")
        logger.info(f"Total: {total}")
        logger.info(f"Updated: {updated_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"{'=' * 60}")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    update_all_enterprises()
