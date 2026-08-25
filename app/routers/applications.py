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
    JobApplicationStatusUpdate,
)
from app.schemas.pagination import CursorPage
from app.services import job_application_service as service
from app.schemas.audit_log import AuditLogRead

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

@router.get("/search", response_model=CursorPage[JobApplicationRead])
async def search_applications(
    q: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    include_deleted: bool = False,
    cursor: str | None = None,
    limit: int = 20,
):
    return await service.search_applications(
        db, current_user.id, q, include_deleted, cursor, limit
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

@router.patch("/{application_id}/status", response_model=JobApplicationRead)
async def change_application_status(
    application_id: uuid.UUID,
    data: JobApplicationStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.change_status(db, current_user.id, application_id, data.status)



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


@router.get("/{application_id}/history", response_model=list[AuditLogRead])
async def get_application_history(
    application_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.get_application_history(db, current_user.id, application_id)