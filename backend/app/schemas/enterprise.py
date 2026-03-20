"""
Enterprise schemas for request/response validation.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# Base schema with common fields
class EnterpriseBase(BaseModel):
    """Base enterprise schema."""

    category_name: str = Field(..., min_length=1, max_length=100, description="门类名称")
    industry_code: str = Field(..., min_length=1, max_length=10, description="行业大类代码")
    industry_name: str = Field(..., min_length=1, max_length=100, description="行业大类名称")
    company_code: str = Field(..., min_length=1, max_length=10, description="上市公司代码")
    company_name: str = Field(..., min_length=1, max_length=100, description="上市公司简称")


# Schema for creating an enterprise
class EnterpriseCreate(EnterpriseBase):
    """Schema for creating an enterprise."""

    pass


# Schema for updating an enterprise
class EnterpriseUpdate(BaseModel):
    """Schema for updating an enterprise."""

    # Basic fields
    category_name: Optional[str] = Field(None, min_length=1, max_length=100, description="门类名称")
    industry_code: Optional[str] = Field(
        None, min_length=1, max_length=10, description="行业大类代码"
    )
    industry_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="行业大类名称"
    )
    company_code: Optional[str] = Field(
        None, min_length=1, max_length=10, description="上市公司代码"
    )
    company_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="上市公司简称"
    )

    # Extended fields
    english_name: Optional[str] = Field(None, max_length=200, description="英文名称")
    legal_representative: Optional[str] = Field(None, max_length=50, description="法人代表")
    registered_capital: Optional[Decimal] = Field(None, description="注册资金(万元)")
    establish_date: Optional[date] = Field(None, description="成立日期")
    listing_date: Optional[date] = Field(None, description="上市日期")
    website: Optional[str] = Field(None, max_length=200, description="官方网站")
    email: Optional[str] = Field(None, max_length=100, description="电子邮箱")
    phone: Optional[str] = Field(None, max_length=200, description="联系电话")
    fax: Optional[str] = Field(None, max_length=200, description="传真")
    registered_address: Optional[str] = Field(None, max_length=500, description="注册地址")
    office_address: Optional[str] = Field(None, max_length=500, description="办公地址")
    main_business: Optional[str] = Field(None, description="主营业务")
    business_scope: Optional[str] = Field(None, description="经营范围")
    company_profile: Optional[str] = Field(None, description="机构简介")


# Schema for enterprise response
class EnterpriseResponse(EnterpriseBase):
    """Schema for enterprise response."""

    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema for enterprise detail (with full information)
class EnterpriseDetail(EnterpriseResponse):
    """Schema for enterprise detail with full information."""

    # Extended fields
    english_name: Optional[str] = Field(None, description="英文名称")
    legal_representative: Optional[str] = Field(None, description="法人代表")
    registered_capital: Optional[Decimal] = Field(None, description="注册资金(万元)")
    establish_date: Optional[date] = Field(None, description="成立日期")
    listing_date: Optional[date] = Field(None, description="上市日期")
    website: Optional[str] = Field(None, description="官方网站")
    email: Optional[str] = Field(None, description="电子邮箱")
    phone: Optional[str] = Field(None, description="联系电话")
    fax: Optional[str] = Field(None, description="传真")
    registered_address: Optional[str] = Field(None, description="注册地址")
    office_address: Optional[str] = Field(None, description="办公地址")
    main_business: Optional[str] = Field(None, description="主营业务")
    business_scope: Optional[str] = Field(None, description="经营范围")
    company_profile: Optional[str] = Field(None, description="机构简介")

    model_config = {"from_attributes": True}


# Schema for paginated enterprise list
class EnterpriseListResponse(BaseModel):
    """Schema for paginated enterprise list."""

    items: list[EnterpriseResponse]
    total: int
    page: int
    page_size: int
    pages: int
