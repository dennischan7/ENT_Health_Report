#!/usr/bin/env python3
"""
补充缺失的利润表数据。

针对有资产负债表但利润表数据为空的企业进行补充。
使用同花顺(THS)数据源，备用Sina数据源。
"""

import argparse
import logging
import re
import time
from decimal import Decimal
from typing import Optional

import akshare as ak
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enterprise import Enterprise
from app.models.financial import IncomeStatement, BalanceSheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# THS利润表字段映射 (不包含报告期，报告期在process_ths_data中单独处理)
THS_INCOME_MAPPING = {
    "其中：营业收入": "operating_revenue",
    "其中：营业成本": "operating_cost",
    "销售费用": "selling_expenses",
    "管理费用": "administrative_expenses",
    "研发费用": "rd_expenses",
    "财务费用": "financial_expenses",
    "三、营业利润": "operating_profit",
    "四、利润总额": "total_profit",
    "减：所得税费用": "income_tax_expense",
    "五、净利润": "net_profit",
    "归属于母公司所有者的净利润": "net_profit_parent",
    "（一）基本每股收益": "basic_eps",
}

# Sina利润表字段映射
SINA_INCOME_MAPPING = {
    "营业收入": "operating_revenue",
    "营业成本": "operating_cost",
    "销售费用": "selling_expenses",
    "管理费用": "administrative_expenses",
    "财务费用": "financial_expenses",
    "营业利润": "operating_profit",
    "利润总额": "total_profit",
    "所得税费用": "income_tax_expense",
    "净利润": "net_profit",
    "归属于母公司所有者的净利润": "net_profit_parent",
    "基本每股收益": "basic_eps",
}


def _parse_chinese_number(value) -> Optional[Decimal]:
    """解析中文数字格式（如 '668.99亿'）。"""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (ValueError, TypeError):
        pass

    if value == "-" or value == "":
        return None
    if isinstance(value, (int, float)):
        if value == 0:
            return None
        return Decimal(str(value))

    try:
        s = str(value).replace(",", "").strip()
        if s == "" or s == "-":
            return None

        multiplier = 1
        if "亿" in s:
            multiplier = 100000000
            s = s.replace("亿", "")
        elif "万" in s:
            multiplier = 10000
            s = s.replace("万", "")

        return Decimal(str(float(s) * multiplier))
    except (ValueError, TypeError):
        return None


def format_stock_code(code: str) -> str:
    """格式化股票代码。"""
    code = str(code)
    if code.startswith('6'):
        return f'sh{code}'
    elif code.startswith('0') or code.startswith('3'):
        return f'sz{code}'
    elif code.startswith('68'):
        return f'sh{code}'
    else:
        return f'sz{code}'


def fetch_ths_income_statement(stock_code: str) -> Optional[pd.DataFrame]:
    """使用THS数据源获取利润表数据。"""
    try:
        df = ak.stock_financial_benefit_ths(symbol=stock_code, indicator='按报告期')
        if df.empty:
            return None
        return df
    except Exception as e:
        logger.debug(f"THS获取失败 {stock_code}: {e}")
        return None


def fetch_sina_income_statement(stock_code: str) -> Optional[pd.DataFrame]:
    """使用Sina数据源获取利润表数据。"""
    try:
        sina_code = format_stock_code(stock_code)
        df = ak.stock_financial_report_sina(stock=sina_code, symbol='利润表')
        if df.empty:
            return None
        return df
    except Exception as e:
        logger.debug(f"Sina获取失败 {stock_code}: {e}")
        return None


def process_ths_data(df: pd.DataFrame) -> list:
    """处理THS数据并返回记录列表。"""
    records = []

    # 筛选年报数据（12月31日报告）
    df['报告期'] = pd.to_datetime(df['报告期'])
    annual_reports = df[df['报告期'].dt.month == 12].copy()
    annual_reports = annual_reports.sort_values('报告期', ascending=False).head(5)

    for _, row in annual_reports.iterrows():
        record = {
            'report_date': row['报告期'].date(),
            'report_year': row['报告期'].year,
        }

        for ths_col, db_field in THS_INCOME_MAPPING.items():
            if ths_col in df.columns:
                record[db_field] = _parse_chinese_number(row.get(ths_col))

        records.append(record)

    return records


def process_sina_data(df: pd.DataFrame) -> list:
    """处理Sina数据并返回记录列表。"""
    records = []

    # 筛选年报数据
    df['报告日'] = pd.to_datetime(df['报告日'])
    annual_reports = df[df['报告日'].dt.month == 12].copy()
    annual_reports = annual_reports.sort_values('报告日', ascending=False).head(5)

    for _, row in annual_reports.iterrows():
        record = {
            'report_date': row['报告日'].date(),
            'report_year': row['报告日'].year,
        }

        for sina_col, db_field in SINA_INCOME_MAPPING.items():
            if sina_col in df.columns:
                value = row.get(sina_col)
                if isinstance(value, str):
                    record[db_field] = _parse_chinese_number(value)
                else:
                    try:
                        record[db_field] = Decimal(str(value)) if value and not pd.isna(value) else None
                    except:
                        record[db_field] = None

        records.append(record)

    return records


def supplement_income_statements(
    db: Session,
    batch_size: int = 50,
    delay: float = 0.5,
):
    """补充缺失的利润表数据。"""
    # 找出需要补充的企业
    enterprises_with_balance = (
        db.query(BalanceSheet.enterprise_id).distinct()
    ).subquery()

    enterprises_with_income = (
        db.query(IncomeStatement.enterprise_id)
        .filter(IncomeStatement.operating_revenue.isnot(None))
        .distinct()
    ).subquery()

    query = (
        db.query(Enterprise)
        .filter(
            Enterprise.id.in_(select(enterprises_with_balance)),
            ~Enterprise.id.in_(select(enterprises_with_income))
        )
        .order_by(Enterprise.company_code)
    )

    total = query.count()
    logger.info(f"需要补充利润表的企业总数: {total}")

    if total == 0:
        logger.info("所有企业已有利润表数据，无需补充")
        return

    processed = 0
    success = 0
    failed = 0
    consecutive_failures = 0

    offset = 0
    while offset < total:
        enterprises = query.offset(offset).limit(batch_size).all()

        for enterprise in enterprises:
            try:
                if consecutive_failures >= 10:
                    logger.warning("连续失败次数过多，等待60秒后重试...")
                    time.sleep(60)
                    consecutive_failures = 0

                logger.info(f"处理 {enterprise.company_code} - {enterprise.company_name}")

                # 优先使用THS数据源
                df = fetch_ths_income_statement(enterprise.company_code)
                data_source = 'ths'

                if df is None or df.empty:
                    # 备用Sina数据源
                    df = fetch_sina_income_statement(enterprise.company_code)
                    data_source = 'sina'

                if df is None or df.empty:
                    logger.warning(f"{enterprise.company_code}: 利润表数据为空")
                    failed += 1
                    consecutive_failures += 1
                    continue

                # 处理数据
                if data_source == 'ths':
                    records = process_ths_data(df)
                else:
                    records = process_sina_data(df)

                if not records:
                    logger.warning(f"{enterprise.company_code}: 无有效数据")
                    failed += 1
                    consecutive_failures += 1
                    continue

                # 检查已有记录
                existing_dates = set(
                    r[0] for r in db.query(IncomeStatement.report_date)
                    .filter(IncomeStatement.enterprise_id == enterprise.id)
                    .all()
                )

                # 插入新记录
                records_to_insert = []
                for record in records:
                    if record['report_date'] in existing_dates:
                        continue

                    records_to_insert.append({
                        "enterprise_id": enterprise.id,
                        "report_date": record['report_date'],
                        "report_year": record['report_year'],
                        "operating_revenue": record.get('operating_revenue'),
                        "operating_cost": record.get('operating_cost'),
                        "selling_expenses": record.get('selling_expenses'),
                        "admin_expenses": record.get('administrative_expenses'),
                        "financial_expenses": record.get('financial_expenses'),
                        "operating_profit": record.get('operating_profit'),
                        "total_profit": record.get('total_profit'),
                        "income_tax": record.get('income_tax_expense'),
                        "net_profit": record.get('net_profit'),
                        "net_profit_parent": record.get('net_profit_parent'),
                        "basic_eps": record.get('basic_eps'),
                        "data_source": "akshare",
                    })

                if records_to_insert:
                    db.bulk_insert_mappings(IncomeStatement, records_to_insert)
                    db.commit()
                    logger.info(f"{enterprise.company_code}: 插入 {len(records_to_insert)} 条利润表记录 [{data_source}]")
                    success += 1
                    consecutive_failures = 0
                else:
                    logger.info(f"{enterprise.company_code}: 无新记录需要插入")
                    success += 1
                    consecutive_failures = 0

                processed += 1
                time.sleep(delay)

            except Exception as e:
                db.rollback()
                logger.error(f"{enterprise.company_code}: 处理失败 - {e}")
                failed += 1
                processed += 1
                consecutive_failures += 1

        offset += batch_size
        logger.info(f"进度: {processed}/{total} ({processed/total*100:.1f}%), 成功: {success}, 失败: {failed}")

        if offset < total:
            logger.info("休息5秒后继续...")
            time.sleep(5)

    logger.info(f"补充完成! 总计: {total}, 处理: {processed}, 成功: {success}, 失败: {failed}")


def main():
    parser = argparse.ArgumentParser(description="补充缺失的利润表数据")
    parser.add_argument("--batch-size", type=int, default=50, help="每批处理的企业数量")
    parser.add_argument("--delay", type=float, default=0.5, help="API调用间隔（秒）")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        supplement_income_statements(db, batch_size=args.batch_size, delay=args.delay)
    finally:
        db.close()


if __name__ == "__main__":
    main()