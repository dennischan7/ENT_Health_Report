"""
Data cleaning and transformation services for financial data.

This module provides functions to clean, transform, and prepare
financial data from AkShare for database insertion.
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# Column mapping from Sina Chinese names to database fields for balance sheet
# Sina API returns Chinese column names
BALANCE_SHEET_MAPPING: Dict[str, str] = {
    "报告日": "report_date",
    "货币资金": "cash",
    "交易性金融资产": "trading_financial_assets",
    "应收账款": "accounts_receivable",
    "存货": "inventory",
    "流动资产合计": "total_current_assets",
    "固定资产净额": "fixed_assets",
    "资产总计": "total_assets",
    "短期借款": "short_term_borrowings",
    "应付账款": "accounts_payable",
    "流动负债合计": "total_current_liabilities",
    "长期借款": "long_term_borrowings",
    "负债合计": "total_liabilities",
    "实收资本(或股本)": "paid_in_capital",
    "未分配利润": "retained_earnings",
    "所有者权益(或股东权益)合计": "total_equity",
}

# Column mapping from Sina Chinese names to database fields for income statement
INCOME_STATEMENT_MAPPING: Dict[str, str] = {
    "报告日": "report_date",
    "营业总收入": "total_revenue",
    "营业收入": "operating_revenue",
    "营业成本": "operating_cost",
    "销售费用": "selling_expenses",
    "管理费用": "administrative_expenses",
    "研发费用": "rd_expenses",
    "财务费用": "financial_expenses",
    "营业利润": "operating_profit",
    "利润总额": "total_profit",
    "所得税费用": "income_tax_expense",
    "净利润": "net_profit",
    "归属于母公司所有者的净利润": "net_profit_parent",
    "基本每股收益": "basic_eps",
}

# Column mapping from Sina Chinese names to database fields for cash flow statement
CASHFLOW_STATEMENT_MAPPING: Dict[str, str] = {
    "报告日": "report_date",
    "经营活动现金流入小计": "operating_cash_inflow",
    "经营活动现金流出小计": "operating_cash_outflow",
    "经营活动产生的现金流量净额": "operating_cash_flow",
    "投资活动现金流入小计": "investing_cash_inflow",
    "投资活动现金流出小计": "investing_cash_outflow",
    "投资活动产生的现金流量净额": "investing_cash_flow",
    "筹资活动现金流入小计": "financing_cash_inflow",
    "筹资活动现金流出小计": "financing_cash_outflow",
    "筹资活动产生的现金流量净额": "financing_cash_flow",
    "现金及现金等价物净增加额": "cash_increase",
    "期末现金及现金等价物余额": "ending_cash",
}


# ============================================================================
# Tonghuashun (同花顺) Column Mappings
# THS data uses different column names and value formats
# ============================================================================

# Column mapping from Tonghuashun Chinese names to database fields for balance sheet
# THS column names are slightly different from Sina
BALANCE_SHEET_THS_MAPPING: Dict[str, str] = {
    "报告期": "report_date",
    "货币资金": "cash",
    "交易性金融资产": "trading_financial_assets",
    "应收账款": "accounts_receivable",
    "存货": "inventory",
    "流动资产合计": "total_current_assets",
    "固定资产": "fixed_assets",
    "资产合计": "total_assets",
    "短期借款": "short_term_borrowings",
    "应付账款": "accounts_payable",
    "流动负债合计": "total_current_liabilities",
    "长期借款": "long_term_borrowings",
    "负债合计": "total_liabilities",
    "实收资本（或股本）": "paid_in_capital",
    "未分配利润": "retained_earnings",
    "所有者权益（或股东权益）合计": "total_equity",
}

# Column mapping from Tonghuashun Chinese names to database fields for income statement
# THS返回的列名带有前缀，如"其中：营业收入"、"一、营业总收入"等
INCOME_STATEMENT_THS_MAPPING: Dict[str, str] = {
    "报告期": "report_date",
    "一、营业总收入": "total_revenue",
    "*营业总收入": "total_revenue",
    "其中：营业收入": "operating_revenue",
    "其中：营业成本": "operating_cost",
    "销售费用": "selling_expenses",
    "管理费用": "administrative_expenses",
    "研发费用": "rd_expenses",
    "财务费用": "financial_expenses",
    "营业利润": "operating_profit",
    "*营业利润": "operating_profit",
    "利润总额": "total_profit",
    "*利润总额": "total_profit",
    "所得税费用": "income_tax_expense",
    "*净利润": "net_profit",
    "净利润": "net_profit",
    "归属于母公司所有者的净利润": "net_profit_parent",
    "*归属于母公司所有者的净利润": "net_profit_parent",
    "基本每股收益": "basic_eps",
}

# Column mapping from Tonghuashun Chinese names to database fields for cash flow statement
CASHFLOW_STATEMENT_THS_MAPPING: Dict[str, str] = {
    "报告期": "report_date",
    "经营活动现金流入小计": "operating_cash_inflow",
    "经营活动现金流出小计": "operating_cash_outflow",
    "经营活动产生的现金流量净额": "operating_cash_flow",
    "投资活动现金流入小计": "investing_cash_inflow",
    "投资活动现金流出小计": "investing_cash_outflow",
    "投资活动产生的现金流量净额": "investing_cash_flow",
    "筹资活动现金流入小计": "financing_cash_inflow",
    "筹资活动现金流出小计": "financing_cash_outflow",
    "筹资活动产生的现金流量净额": "financing_cash_flow",
    "现金及现金等价物净增加额": "cash_increase",
    "期末现金及现金等价物余额": "ending_cash",
}


def filter_annual_reports(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter DataFrame to keep only annual reports (December 31st).

    Annual reports are identified by the month being December (12).

    Args:
        df: DataFrame with a '报告日' column containing report dates.

    Returns:
        DataFrame containing only annual reports.

    Example:
        >>> df = pd.DataFrame({'报告日': ['2023-12-31', '2023-09-30']})
        >>> filtered = filter_annual_reports(df)
        >>> len(filtered)
        1
    """
    df = df.copy()
    if "报告日" not in df.columns:
        logger.warning("'报告日' column not found in DataFrame")
        return df

    df["report_date_temp"] = pd.to_datetime(df["报告日"])
    df = df[df["report_date_temp"].dt.month == 12]
    df.drop(columns=["report_date_temp"], inplace=True)
    return df


def filter_recent_years(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Filter DataFrame to keep only recent N years of data.

    Args:
        df: DataFrame with a '报告日' column containing report dates.
        years: Number of recent years to keep. Default is 5.

    Returns:
        DataFrame containing only data from recent years.

    Example:
        >>> df = pd.DataFrame({'报告日': ['2023-12-31', '2015-12-31']})
        >>> filtered = filter_recent_years(df, years=5)
        >>> len(filtered)
        1
    """
    df = df.copy()
    if "报告日" not in df.columns:
        logger.warning("'报告日' column not found in DataFrame")
        return df

    current_year = datetime.now().year
    df["report_date_temp"] = pd.to_datetime(df["报告日"])
    df["year"] = df["report_date_temp"].dt.year
    result = df[df["year"] >= current_year - years].copy()
    result.drop(columns=["year", "report_date_temp"], inplace=True)
    return result


def clean_numeric_value(value) -> Optional[float]:
    """
    Clean and convert numeric values to float.

    Handles various formats including strings with commas,
    None values, and already numeric types.

    Args:
        value: Value to clean (can be str, int, float, or None).

    Returns:
        Cleaned float value, or None if conversion fails.

    Example:
        >>> clean_numeric_value("1,234,567.89")
        1234567.89
        >>> clean_numeric_value(None)
        None
        >>> clean_numeric_value(100)
        100.0
    """
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    # Remove commas and other non-numeric characters (except decimal point and minus)
    try:
        cleaned = str(value).replace(",", "").strip()
        if cleaned == "" or cleaned == "-":
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        logger.debug(f"Could not convert value to float: {value}")
        return None


def transform_balance_sheet(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Transform balance sheet data for database insertion.

    This function:
    1. Filters to keep only annual reports (December 31st)
    2. Filters to keep only recent N years
    3. Renames Chinese columns to English
    4. Converts numeric values to proper float type
    5. Adds report_year column

    Args:
        df: Raw balance sheet DataFrame from AkShare.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Cleaned and transformed DataFrame ready for database insertion.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_df = client.fetch_balance_sheet("600519")
        >>> clean_df = transform_balance_sheet(raw_df)
        >>> print(clean_df.columns.tolist())
    """
    df = filter_annual_reports(df)
    df = filter_recent_years(df, years=years)

    if df.empty:
        logger.warning("No annual reports found in the specified years")
        return df

    # Select and rename columns that exist
    available_cols = [col for col in BALANCE_SHEET_MAPPING.keys() if col in df.columns]
    if not available_cols:
        logger.error("No matching columns found in balance sheet")
        return pd.DataFrame()

    df = df[available_cols].copy()
    df.rename(columns=BALANCE_SHEET_MAPPING, inplace=True)

    # Convert string date to date object
    # "20241231" -> date(2024, 12, 31)
    df["report_date"] = pd.to_datetime(df["report_date"], format="%Y%m%d").dt.date

    # Convert numeric columns
    numeric_cols = [col for col in df.columns if col != "report_date"]
    for col in numeric_cols:
        df[col] = df[col].apply(clean_numeric_value)

    # Add report_year
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year

    logger.info(f"Transformed balance sheet: {len(df)} records")
    return df


def transform_income_statement(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Transform income statement data for database insertion.

    This function:
    1. Filters to keep only annual reports (December 31st)
    2. Filters to keep only recent N years
    3. Renames Chinese columns to English
    4. Converts numeric values to proper float type
    5. Adds report_year column

    Args:
        df: Raw income statement DataFrame from AkShare.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Cleaned and transformed DataFrame ready for database insertion.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_df = client.fetch_income_statement("600519")
        >>> clean_df = transform_income_statement(raw_df)
        >>> print(clean_df.columns.tolist())
    """
    df = filter_annual_reports(df)
    df = filter_recent_years(df, years=years)

    if df.empty:
        logger.warning("No annual reports found in the specified years")
        return df

    # Select and rename columns that exist
    available_cols = [col for col in INCOME_STATEMENT_MAPPING.keys() if col in df.columns]
    if not available_cols:
        logger.error("No matching columns found in income statement")
        return pd.DataFrame()

    df = df[available_cols].copy()
    df.rename(columns=INCOME_STATEMENT_MAPPING, inplace=True)

    # Convert string date to date object
    # "20241231" -> date(2024, 12, 31)
    df["report_date"] = pd.to_datetime(df["report_date"], format="%Y%m%d").dt.date

    # Convert numeric columns
    numeric_cols = [col for col in df.columns if col != "report_date"]
    for col in numeric_cols:
        df[col] = df[col].apply(clean_numeric_value)

    # Add report_year
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year

    logger.info(f"Transformed income statement: {len(df)} records")
    return df


def transform_cashflow_statement(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Transform cash flow statement data for database insertion.

    This function:
    1. Filters to keep only annual reports (December 31st)
    2. Filters to keep only recent N years
    3. Renames Chinese columns to English
    4. Converts numeric values to proper float type
    5. Adds report_year column

    Args:
        df: Raw cash flow statement DataFrame from AkShare.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Cleaned and transformed DataFrame ready for database insertion.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_df = client.fetch_cashflow_statement("600519")
        >>> clean_df = transform_cashflow_statement(raw_df)
        >>> print(clean_df.columns.tolist())
    """
    df = filter_annual_reports(df)
    df = filter_recent_years(df, years=years)

    if df.empty:
        logger.warning("No annual reports found in the specified years")
        return df

    # Select and rename columns that exist
    available_cols = [col for col in CASHFLOW_STATEMENT_MAPPING.keys() if col in df.columns]
    if not available_cols:
        logger.error("No matching columns found in cash flow statement")
        return pd.DataFrame()

    df = df[available_cols].copy()
    df.rename(columns=CASHFLOW_STATEMENT_MAPPING, inplace=True)

    # Convert string date to date object
    # "20241231" -> date(2024, 12, 31)
    df["report_date"] = pd.to_datetime(df["report_date"], format="%Y%m%d").dt.date

    # Convert numeric columns
    numeric_cols = [col for col in df.columns if col != "report_date"]
    for col in numeric_cols:
        df[col] = df[col].apply(clean_numeric_value)

    # Add report_year
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year

    logger.info(f"Transformed cash flow statement: {len(df)} records")
    return df


def transform_all_statements(
    statements: Dict[str, pd.DataFrame], years: int = 5
) -> Dict[str, pd.DataFrame]:
    """
    Transform all three financial statements.

    Convenience function to transform balance sheet, income statement,
    and cash flow statement in a single call.

    Args:
        statements: Dictionary with keys 'balance_sheet', 'income_statement',
                   'cash_flow' containing raw DataFrames from AkShare.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Dictionary with the same keys containing transformed DataFrames.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_statements = client.fetch_all_statements("600519")
        >>> clean_statements = transform_all_statements(raw_statements)
        >>> print(clean_statements['balance_sheet'].shape)
    """
    logger.info("Transforming all financial statements")

    result = {}

    if "balance_sheet" in statements:
        result["balance_sheet"] = transform_balance_sheet(statements["balance_sheet"], years=years)

    if "income_statement" in statements:
        result["income_statement"] = transform_income_statement(
            statements["income_statement"], years=years
        )

    if "cash_flow" in statements:
        result["cash_flow"] = transform_cashflow_statement(statements["cash_flow"], years=years)

    return result


# ============================================================================
# Tonghuashun (同花顺) Transform Functions
# THS data has different date format ("2024-12-31") and value format ("517.53亿")
# ============================================================================


def parse_chinese_number(value) -> Optional[float]:
    """
    Parse Chinese number format from Tonghuashun data.

    THS returns values in Chinese format like "517.53亿" or "1234.56万".
    This function converts them to actual numeric values.

    Args:
        value: Value to parse (can be str, int, float, or None).
               Chinese formats: "517.53亿", "1234.56万", "-".

    Returns:
        Float value or None if conversion fails.

    Example:
        >>> parse_chinese_number("517.53亿")
        51753000000.0
        >>> parse_chinese_number("1234.56万")
        12345600.0
        >>> parse_chinese_number("-")
        None
    """
    # Handle pandas Series or array - should not happen but be safe
    if isinstance(value, (pd.Series, list, tuple)):
        if len(value) == 1:
            value = value[0]
        else:
            return None

    try:
        if pd.isna(value):
            return None
    except (ValueError, TypeError):
        pass

    if value == "-" or value == "" or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    try:
        s = str(value).replace(",", "").strip()
        if s == "" or s == "-":
            return None

        # Handle Chinese unit suffixes
        if "亿" in s:
            return float(s.replace("亿", "")) * 100000000
        elif "万" in s:
            return float(s.replace("万", "")) * 10000
        else:
            return float(s)
    except (ValueError, TypeError):
        logger.debug(f"Could not parse Chinese number: {value}")
        return None


def filter_annual_reports_ths(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter THS DataFrame to keep only annual reports (December 31st).

    THS date format is "2024-12-31" (string with hyphens).

    Args:
        df: DataFrame with a '报告期' column containing report dates.

    Returns:
        DataFrame containing only annual reports.
    """
    df = df.copy()
    if "报告期" not in df.columns:
        logger.warning("'报告期' column not found in THS DataFrame")
        return df

    # Filter rows containing "12-31" in the date string
    df = df[df["报告期"].astype(str).str.contains("12-31", na=False)].copy()
    return df


def filter_recent_years_ths(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Filter THS DataFrame to keep only recent N years of data.

    Args:
        df: DataFrame with a '报告期' column containing report dates.
        years: Number of recent years to keep. Default is 5.

    Returns:
        DataFrame containing only data from recent years.
    """
    df = df.copy()
    if "报告期" not in df.columns:
        logger.warning("'报告期' column not found in THS DataFrame")
        return df

    current_year = datetime.now().year
    df["report_date_temp"] = pd.to_datetime(df["报告期"])
    df["year"] = df["report_date_temp"].dt.year
    result = df[df["year"] >= current_year - years].copy()
    result.drop(columns=["year", "report_date_temp"], inplace=True)
    return result


def transform_balance_sheet_ths(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Transform Tonghuashun balance sheet data for database insertion.

    This function:
    1. Filters to keep only annual reports (December 31st)
    2. Filters to keep only recent N years
    3. Renames Chinese columns to English
    4. Parses Chinese number formats ("517.53亿" -> 51753000000.0)
    5. Adds report_year column

    Args:
        df: Raw balance sheet DataFrame from THS API.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Cleaned and transformed DataFrame ready for database insertion.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_df = client.fetch_balance_sheet_ths("600519")
        >>> clean_df = transform_balance_sheet_ths(raw_df)
        >>> print(clean_df.columns.tolist())
    """
    df = filter_annual_reports_ths(df)
    df = filter_recent_years_ths(df, years=years)

    if df.empty:
        logger.warning("No annual reports found in THS balance sheet for the specified years")
        return df

    # Select and rename columns that exist
    available_cols = [col for col in BALANCE_SHEET_THS_MAPPING.keys() if col in df.columns]
    if not available_cols:
        logger.error("No matching columns found in THS balance sheet")
        return pd.DataFrame()

    df = df[available_cols].copy()
    df.rename(columns=BALANCE_SHEET_THS_MAPPING, inplace=True)

    # Convert date string to date object
    # THS format: "2024-12-31" -> date(2024, 12, 31)
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date

    # Parse Chinese number formats
    numeric_cols = [col for col in df.columns if col != "report_date"]
    for col in numeric_cols:
        df[col] = df[col].apply(parse_chinese_number)

    # Add report_year
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year

    logger.info(f"Transformed THS balance sheet: {len(df)} records")
    return df


def transform_income_statement_ths(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Transform Tonghuashun income statement data for database insertion.

    This function:
    1. Filters to keep only annual reports (December 31st)
    2. Filters to keep only recent N years
    3. Renames Chinese columns to English
    4. Parses Chinese number formats ("517.53亿" -> 51753000000.0)
    5. Adds report_year column

    Args:
        df: Raw income statement DataFrame from THS API.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Cleaned and transformed DataFrame ready for database insertion.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_df = client.fetch_income_statement_ths("600519")
        >>> clean_df = transform_income_statement_ths(raw_df)
        >>> print(clean_df.columns.tolist())
    """
    df = filter_annual_reports_ths(df)
    df = filter_recent_years_ths(df, years=years)

    if df.empty:
        logger.warning("No annual reports found in THS income statement for the specified years")
        return df

    # Select and rename columns that exist
    available_cols = [col for col in INCOME_STATEMENT_THS_MAPPING.keys() if col in df.columns]
    if not available_cols:
        logger.error("No matching columns found in THS income statement")
        return pd.DataFrame()

    df = df[available_cols].copy()
    df.rename(columns=INCOME_STATEMENT_THS_MAPPING, inplace=True)

    # Convert date string to date object
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date

    # Parse Chinese number formats
    numeric_cols = [col for col in df.columns if col != "report_date"]
    for col in numeric_cols:
        df[col] = df[col].apply(parse_chinese_number)

    # Add report_year
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year

    logger.info(f"Transformed THS income statement: {len(df)} records")
    return df


def transform_cashflow_statement_ths(df: pd.DataFrame, years: int = 5) -> pd.DataFrame:
    """
    Transform Tonghuashun cash flow statement data for database insertion.

    This function:
    1. Filters to keep only annual reports (December 31st)
    2. Filters to keep only recent N years
    3. Renames Chinese columns to English
    4. Parses Chinese number formats ("517.53亿" -> 51753000000.0)
    5. Adds report_year column

    Args:
        df: Raw cash flow statement DataFrame from THS API.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Cleaned and transformed DataFrame ready for database insertion.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_df = client.fetch_cashflow_statement_ths("600519")
        >>> clean_df = transform_cashflow_statement_ths(raw_df)
        >>> print(clean_df.columns.tolist())
    """
    df = filter_annual_reports_ths(df)
    df = filter_recent_years_ths(df, years=years)

    if df.empty:
        logger.warning("No annual reports found in THS cash flow statement for the specified years")
        return df

    # Select and rename columns that exist
    available_cols = [col for col in CASHFLOW_STATEMENT_THS_MAPPING.keys() if col in df.columns]
    if not available_cols:
        logger.error("No matching columns found in THS cash flow statement")
        return pd.DataFrame()

    df = df[available_cols].copy()
    df.rename(columns=CASHFLOW_STATEMENT_THS_MAPPING, inplace=True)

    # Convert date string to date object
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date

    # Parse Chinese number formats
    numeric_cols = [col for col in df.columns if col != "report_date"]
    for col in numeric_cols:
        df[col] = df[col].apply(parse_chinese_number)

    # Add report_year
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year

    logger.info(f"Transformed THS cash flow statement: {len(df)} records")
    return df


def transform_all_statements_ths(
    statements: Dict[str, pd.DataFrame], years: int = 5
) -> Dict[str, pd.DataFrame]:
    """
    Transform all three financial statements from Tonghuashun.

    Convenience function to transform balance sheet, income statement,
    and cash flow statement in a single call.

    Args:
        statements: Dictionary with keys 'balance_sheet', 'income_statement',
                   'cash_flow' containing raw DataFrames from THS API.
        years: Number of recent years to keep. Default is 5.

    Returns:
        Dictionary with the same keys containing transformed DataFrames.

    Example:
        >>> from app.services.akshare_client import AkShareFinancialClient
        >>> client = AkShareFinancialClient()
        >>> raw_statements = client.fetch_all_statements_ths("600519")
        >>> clean_statements = transform_all_statements_ths(raw_statements)
        >>> print(clean_statements['balance_sheet'].shape)
    """
    logger.info("Transforming all financial statements (THS)")

    result = {}

    if "balance_sheet" in statements:
        result["balance_sheet"] = transform_balance_sheet_ths(
            statements["balance_sheet"], years=years
        )

    if "income_statement" in statements:
        result["income_statement"] = transform_income_statement_ths(
            statements["income_statement"], years=years
        )

    if "cash_flow" in statements:
        result["cash_flow"] = transform_cashflow_statement_ths(statements["cash_flow"], years=years)

    return result
