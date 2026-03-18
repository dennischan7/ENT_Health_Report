"""
Script to import listed companies from JSON file into database.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.enterprise import Enterprise


def import_companies(json_file: str, batch_size: int = 500) -> dict:
    """
    Import listed companies from JSON file.

    Args:
        json_file: Path to JSON file with company data
        batch_size: Number of records to insert per batch

    Returns:
        Dictionary with import statistics
    """
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)

    # Load JSON data
    with open(json_file, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} companies from JSON file")

    db: Session = SessionLocal()
    stats = {"total": len(companies), "imported": 0, "skipped": 0, "errors": 0}

    try:
        # Get existing company codes
        existing_codes = set(code[0] for code in db.query(Enterprise.company_code).all())
        print(f"Found {len(existing_codes)} existing companies in database")

        # Prepare batch insert
        batch = []
        for company in companies:
            company_code = company.get("company_code", "")

            # Skip if already exists
            if company_code in existing_codes:
                stats["skipped"] += 1
                continue

            # Create enterprise record
            enterprise = Enterprise(
                category_name=company.get("category_name", ""),
                industry_code=company.get("industry_code", ""),
                industry_name=company.get("industry_name", ""),
                company_code=company_code,
                company_name=company.get("company_name", ""),
                created_by=None,  # System import
            )
            batch.append(enterprise)

            # Insert batch
            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                stats["imported"] += len(batch)
                print(f"Imported {stats['imported']} / {stats['total']} companies...")
                batch = []

        # Insert remaining records
        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            stats["imported"] += len(batch)

        print(f"\nImport completed!")
        print(f"  Total: {stats['total']}")
        print(f"  Imported: {stats['imported']}")
        print(f"  Skipped (duplicates): {stats['skipped']}")

    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
        stats["errors"] = 1
    finally:
        db.close()

    return stats


if __name__ == "__main__":
    json_file = Path(__file__).parent.parent.parent / "listed_companies.json"

    if not json_file.exists():
        print(f"JSON file not found: {json_file}")
        sys.exit(1)

    result = import_companies(str(json_file))
    sys.exit(0 if result["errors"] == 0 else 1)
