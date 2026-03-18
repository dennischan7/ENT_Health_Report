"""
AkShare client for fetching Chinese stock financial data.

This module provides a client for fetching financial statements from
Chinese stock markets using the AkShare library (Sina data source).
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


class AkShareFinancialClient:
    """
    Client for fetching financial statements from AkShare.

    This client fetches financial data from Sina (新浪财经) via AkShare.
    It includes rate limiting to avoid overwhelming the data source.

    Attributes:
        rate_limit_delay: Delay in seconds between API calls.

    Example:
        >>> client = AkShareFinancialClient()
        >>> balance_sheet = client.fetch_balance_sheet("600519")
        >>> print(balance_sheet.shape)
    """

    def __init__(self, rate_limit_delay: float = 0.0):
        """
        Initialize the AkShare client.

        Args:
            rate_limit_delay: DEPRECATED - No longer used. Sina API is lenient.
        """
        self.rate_limit_delay = rate_limit_delay  # Kept for backward compatibility but not used

    def format_stock_code(self, code: str) -> str:
        """
        Format stock code with market prefix for Sina API.

        Sina API requires stock codes with lowercase market prefixes:
        - sh: Shanghai Stock Exchange (codes starting with 6)
        - sz: Shenzhen Stock Exchange (codes starting with 0 or 3)
        - bj: Beijing Stock Exchange (other codes)

        Args:
            code: 6-digit stock code (e.g., "600000", "000001", "430047").

        Returns:
            Code with market prefix: "sh600000", "sz000001", or "bj430047".

        Example:
            >>> client = AkShareFinancialClient()
            >>> client.format_stock_code("600519")
            'sh600519'
            >>> client.format_stock_code("000001")
            'sz000001'
        """
        code = code.strip()
        if code.startswith("6"):
            return f"sh{code}"
        elif code.startswith(("0", "3")):
            return f"sz{code}"
        else:
            return f"bj{code}"

    def fetch_balance_sheet(self, stock_code: str) -> pd.DataFrame:
        """
        Fetch balance sheet (资产负债表) from Sina.

        Retrieves the balance sheet data for a given stock,
        containing assets, liabilities, and equity information.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            DataFrame containing balance sheet data with Chinese columns like:
            - 报告日: Report date
            - 货币资金: Cash and cash equivalents
            - 应收账款: Accounts receivable
            - 存货: Inventory
            - 资产总计: Total assets
            - 负债合计: Total liabilities
            - 所有者权益合计: Total equity

        Raises:
            ValueError: If stock_code is invalid.
            Exception: If API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> df = client.fetch_balance_sheet("600519")
            >>> print(df.columns.tolist())
        """
        sina_code = self.format_stock_code(stock_code)
        logger.info(f"Fetching balance sheet for {sina_code}")

        try:
            df = ak.stock_financial_report_sina(stock=sina_code, symbol="资产负债表")
            logger.info(f"Successfully fetched balance sheet: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch balance sheet for {sina_code}: {e}")
            raise

    def fetch_income_statement(self, stock_code: str) -> pd.DataFrame:
        """
        Fetch income statement (利润表) from Sina.

        Retrieves the income statement data for a given stock,
        containing revenue, costs, and profit information.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            DataFrame containing income statement data with Chinese columns like:
            - 报告日: Report date
            - 营业收入: Operating revenue
            - 营业成本: Operating cost
            - 营业利润: Operating profit
            - 净利润: Net profit
            - 基本每股收益: Basic EPS

        Raises:
            ValueError: If stock_code is invalid.
            Exception: If API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> df = client.fetch_income_statement("600519")
            >>> print(df.columns.tolist())
        """
        sina_code = self.format_stock_code(stock_code)
        logger.info(f"Fetching income statement for {sina_code}")

        try:
            df = ak.stock_financial_report_sina(stock=sina_code, symbol="利润表")
            logger.info(f"Successfully fetched income statement: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch income statement for {sina_code}: {e}")
            raise

    def fetch_cashflow_statement(self, stock_code: str) -> pd.DataFrame:
        """
        Fetch cash flow statement (现金流量表) from Sina.

        Retrieves the cash flow statement data for a given stock,
        containing operating, investing, and financing cash flows.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            DataFrame containing cash flow statement data with Chinese columns like:
            - 报告日: Report date
            - 经营活动产生的现金流量净额: Operating cash flow
            - 投资活动产生的现金流量净额: Investing cash flow
            - 筹资活动产生的现金流量净额: Financing cash flow
            - 期末现金及现金等价物余额: Ending cash balance

        Raises:
            ValueError: If stock_code is invalid.
            Exception: If API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> df = client.fetch_cashflow_statement("600519")
            >>> print(df.columns.tolist())
        """
        sina_code = self.format_stock_code(stock_code)
        logger.info(f"Fetching cash flow statement for {sina_code}")

        try:
            df = ak.stock_financial_report_sina(stock=sina_code, symbol="现金流量表")
            logger.info(f"Successfully fetched cash flow statement: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch cash flow statement for {sina_code}: {e}")
            raise

    def fetch_all_statements(self, stock_code: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch all three financial statements for a stock.

        Convenience method to fetch balance sheet, income statement,
        and cash flow statement in a single call.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            Dictionary with keys:
            - "balance_sheet": Balance sheet DataFrame
            - "income_statement": Income statement DataFrame
            - "cash_flow": Cash flow statement DataFrame

        Raises:
            ValueError: If stock_code is invalid.
            Exception: If any API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> statements = client.fetch_all_statements("600519")
            >>> print(statements["balance_sheet"].shape)
            >>> print(statements["income_statement"].shape)
            >>> print(statements["cash_flow"].shape)
        """
        logger.info(f"Fetching all financial statements for {stock_code}")

        return {
            "balance_sheet": self.fetch_balance_sheet(stock_code),
            "income_statement": self.fetch_income_statement(stock_code),
            "cash_flow": self.fetch_cashflow_statement(stock_code),
        }

    def fetch_all_statements_parallel(self, stock_code: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch all three financial statements in parallel using ThreadPoolExecutor.

        This method fetches balance sheet, income statement, and cash flow statement
        simultaneously, reducing total fetch time by ~2-3x compared to sequential fetch.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            Dictionary with keys:
            - "balance_sheet": Balance sheet DataFrame (empty on error)
            - "income_statement": Income statement DataFrame (empty on error)
            - "cash_flow": Cash flow statement DataFrame (empty on error)

        Example:
            >>> client = AkShareFinancialClient()
            >>> statements = client.fetch_all_statements_parallel("600519")
            >>> print(statements["balance_sheet"].shape)
        """
        logger.info(f"Fetching all financial statements in parallel for {stock_code}")
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.fetch_balance_sheet, stock_code): "balance_sheet",
                executor.submit(self.fetch_income_statement, stock_code): "income_statement",
                executor.submit(self.fetch_cashflow_statement, stock_code): "cash_flow",
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"Failed to fetch {key} for {stock_code}: {e}")
                    results[key] = pd.DataFrame()

        return results

    def fetch_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch basic stock information.

        Args:
            stock_code: 6-digit stock code.

        Returns:
            Dictionary containing stock basic information or None if not found.

        Note:
            This is a placeholder for future implementation.
        """
        # TODO: Implement using ak.stock_individual_info_em()
        logger.warning("fetch_stock_info not yet implemented")
        return None

    # ==================== Tonghuashun (同花顺) API Methods ====================

    def fetch_balance_sheet_ths(self, stock_code: str) -> pd.DataFrame:
        """
        Fetch balance sheet (资产负债表) from Tonghuashun.

        Retrieves the balance sheet data for a given stock using the
        Tonghuashun data source via AkShare.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            DataFrame containing balance sheet data with Chinese columns like:
            - 报告期: Report date (format: "2024-12-31")
            - 货币资金: Cash and cash equivalents (format: "517.53亿")
            - 存货: Inventory
            - 资产合计: Total assets
            - 负债合计: Total liabilities
            - 所有者权益（或股东权益）合计: Total equity

        Raises:
            Exception: If API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> df = client.fetch_balance_sheet_ths("600519")
            >>> print(df.columns.tolist())
        """
        logger.info(f"Fetching balance sheet (THS) for {stock_code}")

        try:
            df = ak.stock_financial_debt_ths(symbol=stock_code, indicator="按报告期")
            logger.info(f"Successfully fetched balance sheet (THS): {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch balance sheet (THS) for {stock_code}: {e}")
            raise

    def fetch_income_statement_ths(self, stock_code: str) -> pd.DataFrame:
        """
        Fetch income statement (利润表) from Tonghuashun.

        Retrieves the income statement data for a given stock using the
        Tonghuashun data source via AkShare.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            DataFrame containing income statement data with Chinese columns like:
            - 报告期: Report date (format: "2024-12-31")
            - 营业收入: Operating revenue (format: "1505.60亿")
            - 营业成本: Operating cost
            - 营业利润: Operating profit
            - 净利润: Net profit

        Raises:
            Exception: If API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> df = client.fetch_income_statement_ths("600519")
            >>> print(df.columns.tolist())
        """
        logger.info(f"Fetching income statement (THS) for {stock_code}")

        try:
            df = ak.stock_financial_benefit_ths(symbol=stock_code, indicator="按报告期")
            logger.info(f"Successfully fetched income statement (THS): {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch income statement (THS) for {stock_code}: {e}")
            raise

    def fetch_cashflow_statement_ths(self, stock_code: str) -> pd.DataFrame:
        """
        Fetch cash flow statement (现金流量表) from Tonghuashun.

        Retrieves the cash flow statement data for a given stock using the
        Tonghuashun data source via AkShare.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            DataFrame containing cash flow statement data with Chinese columns like:
            - 报告期: Report date (format: "2024-12-31")
            - 经营活动产生的现金流量净额: Operating cash flow
            - 投资活动产生的现金流量净额: Investing cash flow
            - 筹资活动产生的现金流量净额: Financing cash flow

        Raises:
            Exception: If API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> df = client.fetch_cashflow_statement_ths("600519")
            >>> print(df.columns.tolist())
        """
        logger.info(f"Fetching cash flow statement (THS) for {stock_code}")

        try:
            df = ak.stock_financial_cash_ths(symbol=stock_code, indicator="按报告期")
            logger.info(f"Successfully fetched cash flow statement (THS): {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch cash flow statement (THS) for {stock_code}: {e}")
            raise

    def fetch_all_statements_ths(self, stock_code: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch all three financial statements from Tonghuashun.

        Convenience method to fetch balance sheet, income statement,
        and cash flow statement in a single call using THS API.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            Dictionary with keys:
            - "balance_sheet": Balance sheet DataFrame
            - "income_statement": Income statement DataFrame
            - "cash_flow": Cash flow statement DataFrame

        Raises:
            Exception: If any API request fails.

        Example:
            >>> client = AkShareFinancialClient()
            >>> statements = client.fetch_all_statements_ths("600519")
            >>> print(statements["balance_sheet"].shape)
        """
        logger.info(f"Fetching all financial statements (THS) for {stock_code}")

        return {
            "balance_sheet": self.fetch_balance_sheet_ths(stock_code),
            "income_statement": self.fetch_income_statement_ths(stock_code),
            "cash_flow": self.fetch_cashflow_statement_ths(stock_code),
        }

    def fetch_all_statements_ths_parallel(self, stock_code: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch all three financial statements in parallel using Tonghuashun API.

        This method fetches balance sheet, income statement, and cash flow statement
        simultaneously using ThreadPoolExecutor, reducing total fetch time.

        Args:
            stock_code: 6-digit stock code (e.g., "600519" for 贵州茅台).

        Returns:
            Dictionary with keys:
            - "balance_sheet": Balance sheet DataFrame (empty on error)
            - "income_statement": Income statement DataFrame (empty on error)
            - "cash_flow": Cash flow statement DataFrame (empty on error)

        Example:
            >>> client = AkShareFinancialClient()
            >>> statements = client.fetch_all_statements_ths_parallel("600519")
            >>> print(statements["balance_sheet"].shape)
        """
        logger.info(f"Fetching all financial statements in parallel (THS) for {stock_code}")
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.fetch_balance_sheet_ths, stock_code): "balance_sheet",
                executor.submit(self.fetch_income_statement_ths, stock_code): "income_statement",
                executor.submit(self.fetch_cashflow_statement_ths, stock_code): "cash_flow",
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"Failed to fetch {key} (THS) for {stock_code}: {e}")
                    results[key] = pd.DataFrame()

        return results
