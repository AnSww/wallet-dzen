from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth_depends import get_current_user
from app.api.v1.schemas.budget import BudgetMonthOut, BudgetPut, BudgetOut, BudgetUpdate
from app.core.models import User
from app.db.db_helper import get_session
from app.db.repositories.budget import BudgetRepository, BudgetUpsertItem

router = APIRouter(prefix="/budgets", tags=["budgets"])


def parse_month_param(month_str: str) -> date:
    try:
        if len(month_str) == 7:  # YYYY-MM
            y, m = month_str.split("-")
            return date(int(y), int(m), 1)
        d = date.fromisoformat(month_str)
        return d.replace(day=1)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid month format. Use YYYY-MM")


@router.put("/{month}", response_model=BudgetMonthOut)
async def upsert_month_budgets(
    month: str,
    items: list[BudgetPut],
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    m = parse_month_param(month)
    repo = BudgetRepository(session)

    try:
        await repo.validate_expense_categories(
            user_id=user.id, category_ids=[i.category_id for i in items]
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await repo.bulk_upsert_month(
        user_id=user.id,
        month=m,
        items=[
            BudgetUpsertItem(category_id=i.category_id, amount=i.amount) for i in items
        ],
    )
    return await repo.build_month_response(user_id=user.id, month=m)


@router.get("/{month}", response_model=BudgetMonthOut)
async def get_month_budgets(
    month: str,
    account_id: int | None = Query(None, ge=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    m = parse_month_param(month)
    repo = BudgetRepository(session)
    return await repo.build_month_response(
        user_id=user.id, month=m, account_id=account_id
    )


# Базовые CRUD — удобно для тестов и UI
@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(
    body: BudgetPut,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = BudgetRepository(session)
    try:
        await repo.validate_expense_categories(
            user_id=user.id, category_ids=[body.category_id]
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    obj = await repo.create(
        user_id=user.id,
        category_id=body.category_id,
        amount=body.amount,
        month=body.month,
    )
    await session.commit()
    return BudgetOut.model_validate(obj, from_attributes=True)


@router.get("/{budget_id:int}/one", response_model=BudgetOut)
async def get_budget(
    budget_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = BudgetRepository(session)
    obj = await repo.get_owned(user_id=user.id, budget_id=budget_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Budget not found")
    return BudgetOut.model_validate(obj, from_attributes=True)


@router.patch("/{budget_id:int}", response_model=BudgetOut)
async def patch_budget(
    budget_id: int,
    body: BudgetUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = BudgetRepository(session)
    if body.category_id is not None:
        try:
            await repo.validate_expense_categories(
                user_id=user.id, category_ids=[body.category_id]
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    obj = await repo.patch_owned(
        user_id=user.id,
        budget_id=budget_id,
        category_id=body.category_id,
        amount=body.amount,
        month=body.month,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Budget not found")
    await session.commit()
    return BudgetOut.model_validate(obj, from_attributes=True)


@router.delete("/{budget_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = BudgetRepository(session)
    deleted = await repo.delete_owned(user_id=user.id, budget_id=budget_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")
    await session.commit()
