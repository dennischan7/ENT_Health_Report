"""
Financial data models for enterprise health diagnosis.
Includes Balance Sheet, Income Statement, and Cash Flow Statement models.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DateTime, Date, Integer, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BalanceSheet(Base, TimestampMixin):
    """
    Balance Sheet model (资产负债表).
    Contains asset, liability, and equity information.
    """

    __tablename__ = "fin_balance_sheets"

    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enterprise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enterprises.id"), nullable=False, index=True
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Assets (资产项目)
    cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # 货币资金
    trading_financial_assets: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 交易性金融资产
    accounts_receivable: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 应收账款
    inventory: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # 存货
    total_current_assets: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 流动资产合计
    fixed_assets: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 固定资产
    total_assets: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 资产总计

    # Liabilities (负债项目)
    short_term_borrowings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 短期借款
    accounts_payable: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 应付账款
    total_current_liabilities: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 流动负债合计
    long_term_borrowings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 长期借款
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 负债合计

    # Equity (所有者权益)
    paid_in_capital: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 实收资本
    retained_earnings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 未分配利润
    total_equity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 所有者权益合计

    # Metadata
    data_source: Mapped[str] = mapped_column(String(50), default="akshare", nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="balance_sheets")

    # Table constraints
    __table_args__ = (
        UniqueConstraint("enterprise_id", "report_date", name="uq_balance_sheet_enterprise_date"),
        Index("ix_balance_sheets_enterprise_year", "enterprise_id", "report_year"),
    )

    def __repr__(self) -> str:
        return f"<BalanceSheet enterprise_id={self.enterprise_id} date={self.report_date}>"


class IncomeStatement(Base, TimestampMixin):
    """
    Income Statement model (利润表).
    Contains revenue, expense, and profit information.
    """

    __tablename__ = "fin_income_statements"

    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enterprise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enterprises.id"), nullable=False, index=True
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Revenue (收入项目)
    operating_revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 营业收入
    operating_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 营业成本
    selling_expenses: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 销售费用
    admin_expenses: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 管理费用
    financial_expenses: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 财务费用

    # Profit (利润项目)
    operating_profit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 营业利润
    total_profit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 利润总额
    income_tax: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 所得税费用
    net_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # 净利润
    net_profit_parent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 归属于母公司股东的净利润

    # Per share (每股指标)
    basic_eps: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 4), nullable=True
    )  # 基本每股收益
    diluted_eps: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 4), nullable=True
    )  # 稀释每股收益

    # Metadata
    data_source: Mapped[str] = mapped_column(String(50), default="akshare", nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="income_statements")

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "enterprise_id", "report_date", name="uq_income_statement_enterprise_date"
        ),
        Index("ix_income_statements_enterprise_year", "enterprise_id", "report_year"),
    )

    def __repr__(self) -> str:
        return f"<IncomeStatement enterprise_id={self.enterprise_id} date={self.report_date}>"


class CashFlowStatement(Base, TimestampMixin):
    """
    Cash Flow Statement model (现金流量表).
    Contains cash inflow and outflow information.
    """

    __tablename__ = "fin_cash_flow_statements"

    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enterprise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enterprises.id"), nullable=False, index=True
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Operating activities (经营活动现金流)
    cash_received_sales: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 销售商品、提供劳务收到的现金
    tax_refund_received: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 收到的税费返还
    cash_paid_goods: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 购买商品、接受劳务支付的现金
    cash_paid_employees: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 支付给职工的现金
    cash_paid_taxes: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 支付的各项税费
    net_cash_operating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 经营活动产生的现金流量净额

    # Investing activities (投资活动现金流)
    cash_received_investments: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 收回投资收到的现金
    cash_paid_assets: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 购建固定资产支付的现金
    cash_paid_investments: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 投资支付的现金
    net_cash_investing: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 投资活动产生的现金流量净额

    # Financing activities (筹资活动现金流)
    cash_received_borrowings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 取得借款收到的现金
    cash_paid_debt: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 偿还债务支付的现金
    cash_paid_dividends: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 分配股利支付的现金
    net_cash_financing: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 筹资活动产生的现金流量净额

    # Summary (汇总)
    net_cash_increase: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 现金及现金等价物净增加额
    cash_end_period: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # 期末现金及现金等价物余额

    # Metadata
    data_source: Mapped[str] = mapped_column(String(50), default="akshare", nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="cash_flow_statements")

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "enterprise_id", "report_date", name="uq_cash_flow_statement_enterprise_date"
        ),
        Index("ix_cash_flow_statements_enterprise_year", "enterprise_id", "report_year"),
    )

    def __repr__(self) -> str:
        return f"<CashFlowStatement enterprise_id={self.enterprise_id} date={self.report_date}>"
