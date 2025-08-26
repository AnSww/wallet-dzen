from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.depends import get_current_user
from app.api.v1.schemas.category import CategoryOut, CategoryCreate, CategoryUpdate
from app.core.models import Category, User
from app.db.db_helper import get_session
from app.db.repositories.category_repo import CategoryRepository
from app.db.types import CategoryKind

router = APIRouter(prefix="/categories", tags=["categories"])


# ---------- helpers / validation ----------


async def _ensure_parent_valid(
    repo: CategoryRepository,
    user_id: int,
    kind: CategoryKind,
    parent_id: int | None = ...,
) -> Category | None:
    if parent_id is None:
        return None
    parent = await repo.get_by_id(user_id, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="parent not found")
    if parent.kind != kind:
        raise HTTPException(status_code=422, detail="parent kind mismatch")
    if parent.archived:
        raise HTTPException(status_code=422, detail="parent is archived")
    return parent


# ---------- endpoints ----------


@router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию (уникальна по name+kind в рамках пользователя)",
)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = CategoryRepository(session)

    exists = await repo.get_by_name_kind(user.id, payload.name, payload.kind)
    if exists:
        raise HTTPException(
            status_code=409, detail="category with this name and kind already exists"
        )

    parent = await _ensure_parent_valid(
        repo,
        user.id,
        payload.kind,
        payload.parent_id,
    )

    try:
        cat = await repo.create(
            user_id=user.id,
            name=payload.name,
            kind=payload.kind,
            parent=parent,
        )
        await session.commit()
    except:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="conflict",
        )

    return CategoryOut.model_validate(cat)


@router.get(
    "",
    response_model=list[CategoryOut],
)
async def list_categories(
    kind: CategoryKind | None = Query(default=None),
    parent_id: int | None = Query(default=None),
    include_archived: bool = Query(default=False),
    search: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = CategoryRepository(session)
    items = await repo.list(
        user_id=user.id,
        kind=kind,
        include_archived=include_archived,
        search=search,
        parent_id=parent_id,
        limit=limit,
        offset=offset,
    )
    return [CategoryOut.model_validate(c) for c in items]


@router.get(
    "{category_id}",
    response_model=CategoryOut,
)
async def get_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(user.id, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="category not found")
    return CategoryOut.model_validate(cat)


@router.patch(
    "/{category_id}",
    response_model=CategoryOut,
)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(user.id, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="category not found")

    if payload.name:
        exists = await repo.get_by_name_kind(user.id, payload.name, cat.kind)
        if exists and exists.id != cat.id:
            raise HTTPException(
                status_code=409,
                detail="category with this name and kind already exists",
            )

    parent = ...
    if payload.parent_id is not None:
        parent = await _ensure_parent_valid(repo, user.id, cat.kind, payload.parent_id)

    try:
        updated = await repo.update(
            cat,
            name=payload.name,
            parent=parent,
            archived=payload.archived,
        )
        await session.commit()
    except:
        await session.rollback()
        raise HTTPException(status_code=409, detail="conflict")

    return CategoryOut.model_validate(updated)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Архивировать категорию (soft delete)",
)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(user.id, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="category not found")

    try:
        await repo.soft_delete(cat)  # дочерние тоже архивируются
    except:
        await session.rollback()
        raise HTTPException(status_code=409, detail="conflict")
    return
