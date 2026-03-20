"""
Enterprise management API routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.enterprise import Enterprise
from app.schemas.enterprise import (
    EnterpriseCreate,
    EnterpriseUpdate,
    EnterpriseResponse,
    EnterpriseListResponse,
    EnterpriseDetail,
)
from app.api.deps import get_current_user


router = APIRouter()


@router.get("", response_model=EnterpriseListResponse, summary="List enterprises")
def list_enterprises(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="搜索公司代码或简称"),
    category_name: Optional[str] = Query(None, description="按门类筛选"),
    industry_name: Optional[str] = Query(None, description="按行业大类筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseListResponse:
    """
    List all enterprises with pagination and filters.
    """
    query = db.query(Enterprise)

    # Apply filters
    if search:
        query = query.filter(
            (Enterprise.company_code.ilike(f"%{search}%"))
            | (Enterprise.company_name.ilike(f"%{search}%"))
        )

    if category_name:
        query = query.filter(Enterprise.category_name == category_name)

    if industry_name:
        query = query.filter(Enterprise.industry_name == industry_name)

    # Count total
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    enterprises = query.order_by(Enterprise.company_code).offset(offset).limit(page_size).all()

    return EnterpriseListResponse(
        items=[EnterpriseResponse.model_validate(e) for e in enterprises],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{enterprise_id}", response_model=EnterpriseResponse, summary="Get enterprise by ID")
def get_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseResponse:
    """
    Get a specific enterprise by ID.
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )
    return EnterpriseResponse.model_validate(enterprise)


@router.get(
    "/code/{company_code}", response_model=EnterpriseResponse, summary="Get enterprise by code"
)
def get_enterprise_by_code(
    company_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseResponse:
    """
    Get a specific enterprise by company code.
    """
    enterprise = db.query(Enterprise).filter(Enterprise.company_code == company_code).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with code {company_code} not found",
        )
    return EnterpriseResponse.model_validate(enterprise)


@router.post(
    "",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create enterprise",
)
def create_enterprise(
    enterprise_data: EnterpriseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseResponse:
    """
    Create a new enterprise.
    """
    # Check company code uniqueness
    existing = (
        db.query(Enterprise).filter(Enterprise.company_code == enterprise_data.company_code).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"上市公司代码 {enterprise_data.company_code} 已存在",
        )

    # Create enterprise
    enterprise = Enterprise(**enterprise_data.model_dump(), created_by=current_user.id)

    db.add(enterprise)
    db.commit()
    db.refresh(enterprise)

    return EnterpriseResponse.model_validate(enterprise)


@router.put("/{enterprise_id}", response_model=EnterpriseResponse, summary="Update enterprise")
def update_enterprise(
    enterprise_id: int,
    enterprise_data: EnterpriseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseResponse:
    """
    Update an enterprise.
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )

    # Update fields
    update_data = enterprise_data.model_dump(exclude_unset=True)

    # Check company code uniqueness
    if "company_code" in update_data and update_data["company_code"]:
        existing = (
            db.query(Enterprise)
            .filter(
                Enterprise.company_code == update_data["company_code"],
                Enterprise.id != enterprise_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"上市公司代码 {update_data['company_code']} 已存在",
            )

    for key, value in update_data.items():
        setattr(enterprise, key, value)

    db.commit()
    db.refresh(enterprise)

    return EnterpriseResponse.model_validate(enterprise)


@router.delete(
    "/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete enterprise"
)
def delete_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an enterprise. Only admins can delete enterprises.
    删除企业。仅管理员可删除企业。
    """
    # Check admin permission
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员才能删除企业",
        )

    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )

    db.delete(enterprise)
    db.commit()


@router.get("/categories/list", response_model=list[str], summary="List categories")
def list_categories(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[str]:
    """
    Get list of distinct category names.
    """
    categories = db.query(Enterprise.category_name).distinct().all()
    return [c[0] for c in categories if c[0]]


@router.get("/industries/list", response_model=list[str], summary="List industries")
def list_industries(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[str]:
    """
    Get list of distinct industry names.
    """
    industries = db.query(Enterprise.industry_name).distinct().all()
    return [i[0] for i in industries if i[0]]


@router.get(
    "/{enterprise_id}/detail", response_model=EnterpriseDetail, summary="Get enterprise detail"
)
def get_enterprise_detail(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnterpriseDetail:
    """
    Get detailed information for a specific enterprise.
    获取指定企业的详细信息（包含扩展字段）。
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enterprise with id {enterprise_id} not found",
        )
    return EnterpriseDetail.model_validate(enterprise)
