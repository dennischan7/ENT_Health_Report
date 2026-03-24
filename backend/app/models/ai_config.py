"""
AI Configuration models for LLM provider settings and audit logging.
"""

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AIProvider(str, enum.Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"  # 阿里千问
    KIMI = "kimi"  # Moonshot
    GLM = "glm"  # 智谱
    BAIDU = "baidu"
    TENCENT = "tencent"
    MINIMAX = "minimax"
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai-compatible"


class AIConfig(Base, TimestampMixin):
    """AI Configuration model for LLM provider settings."""

    __tablename__ = "ai_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    provider: Mapped[AIProvider] = mapped_column(
        Enum(AIProvider), nullable=False, default=AIProvider.OPENAI
    )
    api_base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    encrypted_api_key: Mapped[str] = mapped_column(String(500), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)

    # Relationships
    audit_logs = relationship("AIConfigAuditLog", back_populates="ai_config", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<AIConfig {self.config_name} ({self.provider.value})>"


class AIConfigAuditLog(Base):
    """Audit log for AI configuration access."""

    __tablename__ = "ai_config_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ai_config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_configs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "view", "edit", "delete", "use"
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ai_config = relationship("AIConfig", back_populates="audit_logs")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AIConfigAuditLog {self.action} on config_id={self.ai_config_id}>"
