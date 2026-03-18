"""
User schemas for request/response validation.
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Email validation regex pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> str:
    """Validate email format."""
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Invalid email format")
    return email.lower()


# Base schema with common fields
class UserBase(BaseModel):
    """Base user schema."""

    email: str = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User full name")

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


# Schema for creating a user
class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=6, max_length=100, description="User password")
    role: Optional[str] = Field(default="user", description="User role: 'admin' or 'user'")


# Schema for updating a user
class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: Optional[str] = Field(None, description="User email address")
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User full name"
    )
    role: Optional[str] = Field(None, description="User role: 'admin' or 'user'")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="New password")

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_email(v)
        return v


# Schema for user response
class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema for login request
class LoginRequest(BaseModel):
    """Schema for login request."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


# Schema for login response
class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse


# Schema for refresh token request
class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


# Schema for token response
class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
