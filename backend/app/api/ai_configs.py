"""
AI Configuration management API routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.ai_config import AIConfig, AIConfigAuditLog, AIProvider
from app.schemas.ai_config import (
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    AIConfigListResponse,
)
from app.api.deps import get_current_user, get_current_admin_user
from app.core.encryption import encrypt


router = APIRouter()


def _create_audit_log(
    db: Session,
    ai_config_id: int,
    user_id: Optional[int],
    action: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AIConfigAuditLog:
    """Create an audit log entry for AI config operations."""
    audit_log = AIConfigAuditLog(
        ai_config_id=ai_config_id,
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
    )
    db.add(audit_log)
    return audit_log


def _mask_config_response(config: AIConfig) -> AIConfigResponse:
    """Convert AIConfig model to response with masked API key."""
    from app.schemas.ai_config import AIProvider as SchemaAIProvider

    # Map model provider to schema provider (both are string enums)
    # The model stores the string value, we need to convert to schema enum
    provider_value = (
        config.provider.value if hasattr(config.provider, "value") else str(config.provider)
    )

    # Try to match with schema enum, fallback to OPENAI if not found
    try:
        schema_provider = SchemaAIProvider(provider_value)
    except ValueError:
        # If the provider value isn't in schema enum, use OPENAI as default
        schema_provider = SchemaAIProvider.OPENAI

    return AIConfigResponse(
        id=config.id,
        config_name=config.config_name,
        provider=schema_provider,
        model_name=config.model_name,
        api_key_set=bool(config.encrypted_api_key),
        is_active=config.is_active,
        is_default=config.is_default,
        description=None,  # Model doesn't have description field
        created_by=None,  # Model doesn't have created_by field
        created_at=config.created_at,  # type: ignore
        updated_at=config.updated_at,  # type: ignore
    )


@router.get("", response_model=AIConfigListResponse, summary="List AI configurations")
def list_ai_configs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIConfigListResponse:
    """
    List all AI configurations with pagination.
    API keys are masked (only shows whether set or not).
    """
    query = db.query(AIConfig)

    # Count total
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    configs = query.order_by(AIConfig.id.desc()).offset(offset).limit(page_size).all()

    # Note: List operations are not audit logged as they don't expose sensitive data

    return AIConfigListResponse(
        items=[_mask_config_response(c) for c in configs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/{config_id}", response_model=AIConfigResponse, summary="Get AI configuration by ID")
def get_ai_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIConfigResponse:
    """
    Get a specific AI configuration by ID.
    API key is masked (only shows whether set or not).
    """
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI configuration with id {config_id} not found",
        )

    # Create audit log
    _create_audit_log(
        db=db,
        ai_config_id=config_id,
        user_id=current_user.id,
        action="view",
        details=f"Viewed AI config: {config.config_name}",
    )
    db.commit()

    return _mask_config_response(config)


@router.post(
    "",
    response_model=AIConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI configuration",
)
def create_ai_config(
    config_data: AIConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> AIConfigResponse:
    """
    Create a new AI configuration.
    API key will be encrypted before storage.
    Only admins can create AI configurations.
    """
    # Check config name uniqueness
    existing = db.query(AIConfig).filter(AIConfig.config_name == config_data.config_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI configuration with name '{config_data.config_name}' already exists",
        )

    # Encrypt API key
    encrypted_key = encrypt(config_data.api_key)

    # If this is set as default, unset other defaults
    if config_data.is_default:
        db.query(AIConfig).filter(AIConfig.is_default == True).update({"is_default": False})

    # Create config
    config = AIConfig(
        config_name=config_data.config_name,
        provider=config_data.provider,
        encrypted_api_key=encrypted_key,
        model_name=config_data.model_name,
        is_default=config_data.is_default,
        is_active=False,  # New configs start inactive
    )

    db.add(config)
    db.flush()  # Get the ID

    # Create audit log
    _create_audit_log(
        db=db,
        ai_config_id=config.id,
        user_id=current_user.id,
        action="create",
        details=f"Created AI config: {config.config_name}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(config)

    return _mask_config_response(config)


@router.put("/{config_id}", response_model=AIConfigResponse, summary="Update AI configuration")
def update_ai_config(
    config_id: int,
    config_data: AIConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> AIConfigResponse:
    """
    Update an AI configuration.
    API key will be encrypted before storage if provided.
    Only admins can update AI configurations.
    """
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI configuration with id {config_id} not found",
        )

    update_data = config_data.model_dump(exclude_unset=True)

    # Check config name uniqueness if being updated
    if "config_name" in update_data and update_data["config_name"]:
        existing = (
            db.query(AIConfig)
            .filter(
                AIConfig.config_name == update_data["config_name"],
                AIConfig.id != config_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AI configuration with name '{update_data['config_name']}' already exists",
            )

    # Encrypt API key if provided
    if "api_key" in update_data and update_data["api_key"]:
        update_data["encrypted_api_key"] = encrypt(update_data.pop("api_key"))
    elif "api_key" in update_data:
        del update_data["api_key"]  # Remove empty api_key

    # Handle is_default update
    if "is_default" in update_data and update_data["is_default"]:
        db.query(AIConfig).filter(
            AIConfig.is_default == True,
            AIConfig.id != config_id,
        ).update({"is_default": False})

    # Apply updates
    for key, value in update_data.items():
        setattr(config, key, value)

    # Create audit log
    _create_audit_log(
        db=db,
        ai_config_id=config_id,
        user_id=current_user.id,
        action="update",
        details=f"Updated AI config: {config.config_name}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(config)

    return _mask_config_response(config)


@router.delete(
    "/{config_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete AI configuration"
)
def delete_ai_config(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> None:
    """
    Delete an AI configuration.
    Only admins can delete AI configurations.
    Cannot delete the active configuration without activating another first.
    """
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI configuration with id {config_id} not found",
        )

    # Prevent deletion of active config
    if config.is_active:
        # Check if there's another config to activate
        other_config = (
            db.query(AIConfig).filter(AIConfig.id != config_id, AIConfig.is_default == True).first()
        )
        if not other_config:
            other_config = db.query(AIConfig).filter(AIConfig.id != config_id).first()

        if not other_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only AI configuration. Create another first.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete active configuration. Activate '{other_config.config_name}' first.",
        )

    # Store config name for logging before deletion
    config_name = config.config_name

    # Log the deletion action
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"AI config deleted: id={config_id}, name={config_name}, "
        f"by user_id={current_user.id}, ip={request.client.host if request.client else None}"
    )

    # Use raw SQL to delete to avoid SQLAlchemy's session issues with CASCADE
    from sqlalchemy import text

    db.execute(text("DELETE FROM ai_configs WHERE id = :id"), {"id": config_id})
    db.commit()


@router.post(
    "/{config_id}/activate",
    response_model=AIConfigResponse,
    summary="Activate AI configuration",
)
def activate_ai_config(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> AIConfigResponse:
    """
    Activate an AI configuration.
    This sets the configuration as the active one for the system.
    Only one configuration can be active at a time.
    Only admins can activate AI configurations.
    """
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI configuration with id {config_id} not found",
        )

    # Check if config has API key set
    if not config.encrypted_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate configuration without an API key",
        )

    # Deactivate all other configs
    db.query(AIConfig).filter(AIConfig.is_active == True).update({"is_active": False})

    # Activate this config
    config.is_active = True
    config.is_default = True  # Active config becomes default

    # Create audit log
    _create_audit_log(
        db=db,
        ai_config_id=config_id,
        user_id=current_user.id,
        action="activate",
        details=f"Activated AI config: {config.config_name}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(config)

    return _mask_config_response(config)
