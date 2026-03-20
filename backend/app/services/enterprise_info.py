"""
Enterprise information service for fetching detailed company data from AkShare.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str or pd.isna(date_str):
        return None
    try:
        # Handle formats: '1987-12-22', '1991-04-03'
        return pd.to_datetime(date_str).date()
    except Exception as e:
        logger.warning(f"Failed to parse date: {date_str}, error: {e}")
        return None


def parse_capital(capital_str: Optional[str]) -> Optional[Decimal]:
    """Parse capital string to Decimal."""
    if not capital_str or pd.isna(capital_str):
        return None
    try:
        # Handle formats: '1940591.8198', already numeric
        return Decimal(str(capital_str))
    except Exception as e:
        logger.warning(f"Failed to parse capital: {capital_str}, error: {e}")
        return None


def fetch_enterprise_info(company_code: str) -> Optional[Dict[str, Any]]:
    """
    Fetch enterprise detailed information from AkShare.

    Args:
        company_code: Company stock code (e.g., '000001', '600519')

    Returns:
        Dictionary with enterprise info or None if failed
    """
    try:
        logger.info(f"Fetching enterprise info for {company_code}")

        # Get company profile from AkShare
        df = ak.stock_profile_cninfo(symbol=company_code)

        if df.empty:
            logger.warning(f"No data found for company {company_code}")
            return None

        row = df.iloc[0]

        # Map Chinese column names to English field names
        info = {
            "english_name": row.get("英文名称") if pd.notna(row.get("英文名称")) else None,
            "legal_representative": row.get("法人代表") if pd.notna(row.get("法人代表")) else None,
            "registered_capital": parse_capital(row.get("注册资金")),
            "establish_date": parse_date(row.get("成立日期")),
            "listing_date": parse_date(row.get("上市日期")),
            "website": row.get("官方网站") if pd.notna(row.get("官方网站")) else None,
            "email": row.get("电子邮箱") if pd.notna(row.get("电子邮箱")) else None,
            "phone": row.get("联系电话") if pd.notna(row.get("联系电话")) else None,
            "fax": row.get("传真") if pd.notna(row.get("传真")) else None,
            "registered_address": row.get("注册地址") if pd.notna(row.get("注册地址")) else None,
            "office_address": row.get("办公地址") if pd.notna(row.get("办公地址")) else None,
            "main_business": row.get("主营业务") if pd.notna(row.get("主营业务")) else None,
            "business_scope": row.get("经营范围") if pd.notna(row.get("经营范围")) else None,
            "company_profile": row.get("机构简介") if pd.notna(row.get("机构简介")) else None,
        }

        logger.info(
            f"Successfully fetched info for {company_code}: {info.get('legal_representative', 'N/A')}"
        )
        return info

    except Exception as e:
        logger.error(f"Failed to fetch enterprise info for {company_code}: {e}", exc_info=True)
        return None


def test_fetch():
    """Test function to verify the service works."""
    test_codes = ["000001", "600519"]

    for code in test_codes:
        print(f"\n=== Testing {code} ===")
        info = fetch_enterprise_info(code)
        if info:
            print(f"Name: {info.get('legal_representative')}")
            print(f"Industry: {info.get('main_business', '')[:50]}...")
            print(f"Phone: {info.get('phone')}")
        else:
            print("Failed to fetch")
