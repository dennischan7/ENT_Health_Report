"""
AI Configuration schemas for request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    """Supported AI providers."""

    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOONSHOT = "moonshot"
    ZHIPU = "zhipu"
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    TENCENT = "tencent"


class AIConfigBase(BaseModel):
    """Base AI configuration schema."""

    config_name: str = Field(..., min_length=1, max_length=100, description="Configuration name")
    provider: AIProvider = Field(..., description="AI provider")
    model_name: str = Field(..., min_length=1, max_length=100, description="Model name")
    is_default: bool = Field(default=False, description="Whether this is the default configuration")
    description: Optional[str] = Field(
        None, max_length=500, description="Configuration description"
    )


class AIConfigCreate(AIConfigBase):
    """Schema for creating an AI configuration."""

    api_key: str = Field(
        ..., min_length=1, max_length=500, description="API key (plain text input)"
    )


class AIConfigUpdate(BaseModel):
    """Schema for updating an AI configuration."""

    config_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Configuration name"
    )
    provider: Optional[AIProvider] = Field(None, description="AI provider")
    model_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Model name")
    api_key: Optional[str] = Field(
        None, min_length=1, max_length=500, description="API key (plain text input)"
    )
    is_default: Optional[bool] = Field(
        None, description="Whether this is the default configuration"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Configuration description"
    )


class AIConfigResponse(BaseModel):
    """Schema for AI configuration response.

    Note: API key is never exposed in response, only whether it's set.
    """

    id: int
    config_name: str
    provider: AIProvider
    model_name: str
    api_key_set: bool = Field(..., description="Whether API key is configured")
    is_default: bool
    description: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIConfigListResponse(BaseModel):
    """Schema for paginated AI configuration list."""

    items: list[AIConfigResponse]
    total: int
    page: int
    page_size: int
    pages: int
