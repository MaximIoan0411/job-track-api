import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.enums import ApplicationStatus
from app.models import User
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationRead,
    JobApplicationUpdate,
)
from app.schemas.pagination import CursorPage
from app.services import job_application_service as service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=JobApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: JobApplicationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.create_application(db, current_user.id, data)


@router.get("", response_model=CursorPage[JobApplicationRead])
async def list_applications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    include_deleted: bool = False,
    cursor: str | None = None,
    limit: int = 20,
):
    return await service.list_applications(
        db, current_user.id, status_filter, include_deleted, cursor, limit
    )


@router.get("/{application_id}", response_model=JobApplicationRead)
async def get_application(
    application_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.get_application(db, current_user.id, application_id)


@router.patch("/{application_id}", response_model=JobApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    data: JobApplicationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.update_application(db, current_user.id, application_id, data)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await service.soft_delete_application(db, current_user.id, application_id)
    return None


@router.post("/{application_id}/restore", response_model=JobApplicationRead)
async def restore_application(
    application_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.restore_application(db, current_user.id, application_id)