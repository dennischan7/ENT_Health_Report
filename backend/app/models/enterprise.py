"""
Enterprise model for listed company information.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, ForeignKey, Date, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.financial import BalanceSheet, IncomeStatement, CashFlowStatement


class Enterprise(Base, TimestampMixin):
    """Enterprise model for listed company information."""

    __tablename__ = "enterprises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 门类名称 (e.g., "农、林、牧、渔业", "制造业")
    category_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # 行业大类代码 (e.g., "01", "13", "C")
    industry_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # 行业大类名称 (e.g., "农业", "农副食品加工业")
    industry_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # 上市公司代码 (e.g., "000998", "600438") - 唯一标识
    company_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)

    # 上市公司简称 (e.g., "隆平高科", "通威股份")
    company_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # ========== 扩展字段：企业详细信息 ==========

    # 英文名称
    english_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # 法人代表
    legal_representative: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 注册资金（万元）
    registered_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)

    # 成立日期
    establish_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # 上市日期
    listing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # 官方网站
    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # 电子邮箱
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 联系电话
    phone: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # 传真
    fax: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # 注册地址
    registered_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 办公地址
    office_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 主营业务
    main_business: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 经营范围
    business_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 机构简介
    company_profile: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign key to user who created this enterprise (optional for imported data)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    creator = relationship("User", back_populates="enterprises")
    balance_sheets = relationship("BalanceSheet", back_populates="enterprise", lazy="dynamic")
    income_statements = relationship("IncomeStatement", back_populates="enterprise", lazy="dynamic")
    cash_flow_statements = relationship(
        "CashFlowStatement", back_populates="enterprise", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Enterprise {self.company_code} - {self.company_name}>"
