"""
Enterprise schemas for request/response validation.
"""

from datetime import datetime
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


# Schema for enterprise response
class EnterpriseResponse(EnterpriseBase):
    """Schema for enterprise response."""

    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema for paginated enterprise list
class EnterpriseListResponse(BaseModel):
    """Schema for paginated enterprise list."""

    items: list[EnterpriseResponse]
    total: int
    page: int
    page_size: int
    pages: int
