from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth_depends import get_current_user
from app.api.v1.schemas.transaction import TransactionOut, TransactionCreate, TransactionsPage, TransactionUpdate
from app.db.db_helper import get_session
from app.db.repositories.transaction_repo import TransactionRepository, NotFound, ValidationError, InsufficientFunds, \
    Conflict
from app.db.types import Direction

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    repo = TransactionRepository(session, enforce_non_negative=True)
    try:
        tx = await repo.create(
            user.id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            direction=payload.direction,
            amount=payload.amount,
            note=payload.note,
            occurred_at=payload.occurred_at,
        )
        await session.commit()
        return tx
    except NotFound as e:
        raise HTTPException(status_code=404, detail=f"{e.args[0]} not found")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InsufficientFunds:
        raise HTTPException(
            status_code=409,
            detail={"code": "INSUFFICIENT_FUNDS", "message": "not enough balance for this expense"}
        )

@router.get("", response_model=TransactionsPage)
async def list_transactions(
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None),
    account_id: int | None = None,
    category_id: int | None = None,
    direction: Direction | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    repo = TransactionRepository(session)
    items, next_cursor = await repo.list(
        user.id,
        limit=limit,
        cursor=cursor,
        account_id=account_id,
        category_id=category_id,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )
    return TransactionsPage(items=items, next_cursor=next_cursor)

@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction(
    tx_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    repo = TransactionRepository(session)
    try:
        tx = await repo.get(user.id, tx_id)
        return tx
    except NotFound:
        raise HTTPException(status_code=404, detail="transaction not found")

@router.patch("/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id: int,
    payload: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    repo = TransactionRepository(session, enforce_non_negative=True)
    try:
        tx = await repo.update(
            user.id,
            tx_id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            direction=payload.direction,
            amount=payload.amount,
            note=payload.note,
            occurred_at=payload.occurred_at,
        )
        await session.commit()
        return tx
    except NotFound as e:
        raise HTTPException(status_code=404, detail=f"{e.args[0]} not found")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InsufficientFunds:
        raise HTTPException(
            status_code=409,
            detail={"code": "INSUFFICIENT_FUNDS", "message": "not enough balance for this change"}
        )


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    tx_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    repo = TransactionRepository(session)
    try:
        await repo.delete(user.id, tx_id)
        await session.commit()
        return
    except NotFound:
        raise HTTPException(status_code=404, detail="transaction not found")