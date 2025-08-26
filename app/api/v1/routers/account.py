from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.account import AccountCreate, AccountOut, AccountPatch
from app.api.v1.auth_depends import get_db, get_current_user, get_session
from app.core.models import User
from app.db.repositories.account_repo import AccountRepository

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = AccountRepository(session)

    try:
        acc = await repo.create(
            user=user,
            name=payload.name,
            currency=payload.currency,
            type_=payload.type,
            initial_balance=payload.initial_balance,
        )
        await session.commit()
    except:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="conflict",
        )

    return AccountOut.model_validate(acc)


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    include_archived: bool = Query(False),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = AccountRepository(session)
    accounts = await repo.list_for_user(
        user_id=user.id,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    return [AccountOut.model_validate(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    archived: bool = False,
):
    repo = AccountRepository(session)
    acc = await repo.get_owned(user.id, account_id, archived=archived)
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="account not found"
        )
    return AccountOut.model_validate(acc)


@router.patch("/{account_id}", response_model=AccountOut)
async def patch_account(
    account_id: int,
    payload: AccountPatch,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = AccountRepository(session)
    acc = await repo.get_owned(user.id, account_id)
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="account not found"
        )

    updated = await repo.patch(
        account=acc, name=payload.name, archived=payload.archived
    )
    return AccountOut.model_validate(updated)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = AccountRepository(session)
    acc = await repo.get_owned(user.id, account_id)
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="account not found"
        )

    await repo.archive(account=acc)
    return None
