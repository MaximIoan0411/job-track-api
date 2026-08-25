import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select, tuple_ , func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.enums import AuditAction
from app.exceptions import (
    ApplicationNotFoundError,
    InvalidStateError,
    VersionConflictError,
)
from app.models import AuditLog, JobApplication
from app.schemas.job_application import JobApplicationCreate, JobApplicationUpdate
from app.schemas.pagination import CursorPage
from app.utils import decode_cursor, encode_cursor

from app.enums import ApplicationStatus, AuditAction

MAX_PAGE_SIZE = 100


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "value"):  
        return value.value
    return value


async def _get_owned_application(
    db: AsyncSession, application_id: uuid.UUID, user_id: uuid.UUID
) -> JobApplication:
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == user_id,
        )
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise ApplicationNotFoundError("Aplicarea nu a fost găsită")
    return application


async def create_application(
    db: AsyncSession, user_id: uuid.UUID, data: JobApplicationCreate
) -> JobApplication:
    application = JobApplication(user_id=user_id, **data.model_dump())
    db.add(application)
    await db.flush() 

    db.add(
        AuditLog(
            application_id=application.id,
            action=AuditAction.CREATED,
            changes=None,
        )
    )
    await db.commit()
    await db.refresh(application)
    return application


async def get_application(
    db: AsyncSession, user_id: uuid.UUID, application_id: uuid.UUID
) -> JobApplication:
    return await _get_owned_application(db, application_id, user_id)


async def list_applications(
    db: AsyncSession,
    user_id: uuid.UUID,
    status_filter,
    include_deleted: bool,
    cursor: str | None,
    limit: int,
) -> CursorPage:
    limit = min(max(limit, 1), MAX_PAGE_SIZE)

    query = select(JobApplication).where(JobApplication.user_id == user_id)

    if not include_deleted:
        query = query.where(JobApplication.deleted_at.is_(None))

    if status_filter:
        query = query.where(JobApplication.status == status_filter)

    if cursor:
        cursor_created_at, cursor_id = decode_cursor(cursor)
        query = query.where(
            tuple_(JobApplication.created_at, JobApplication.id)
            < (cursor_created_at, cursor_id)
        )

    query = query.order_by(
        JobApplication.created_at.desc(), JobApplication.id.desc()
    ).limit(limit + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorPage(items=items, next_cursor=next_cursor, has_more=has_more)


async def update_application(
    db: AsyncSession,
    user_id: uuid.UUID,
    application_id: uuid.UUID,
    data: JobApplicationUpdate,
) -> JobApplication:
    application = await _get_owned_application(db, application_id, user_id)

    if application.deleted_at is not None:
        raise InvalidStateError("Nu poți edita o aplicare ștearsă. Restaureaz-o mai întâi.")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return application

    changes: dict[str, dict[str, Any]] = {}
    for field, new_value in update_data.items():
        old_value = getattr(application, field)
        if old_value != new_value:
            changes[field] = {"old": _serialize(old_value), "new": _serialize(new_value)}
            setattr(application, field, new_value)

    if not changes:
        return application

    db.add(
        AuditLog(
            application_id=application.id,
            action=AuditAction.UPDATED,
            changes=changes,
        )
    )

    try:
        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise VersionConflictError(
            "Aplicarea a fost modificată între timp. Reîncarcă și încearcă din nou."
        )

    await db.refresh(application)
    return application

async def change_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    application_id: uuid.UUID,
    new_status: ApplicationStatus,
) -> JobApplication:
    application = await _get_owned_application(db, application_id, user_id)

    if application.deleted_at is not None:
        raise InvalidStateError(
            "Nu poți schimba statusul unei aplicări șterse. Restaureaz-o mai întâi."
        )

    if application.status == new_status:
        return application

    old_status = application.status
    application.status = new_status

    db.add(
        AuditLog(
            application_id=application.id,
            action=AuditAction.STATUS_CHANGED,
            changes={"status": {"old": old_status.value, "new": new_status.value}},
        )
    )

    try:
        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise VersionConflictError(
            "Aplicarea a fost modificată între timp. Reîncarcă și încearcă din nou."
        )

    await db.refresh(application)
    return application


async def soft_delete_application(
    db: AsyncSession, user_id: uuid.UUID, application_id: uuid.UUID
) -> None:
    application = await _get_owned_application(db, application_id, user_id)

    if application.deleted_at is not None:
        raise InvalidStateError("Aplicarea este deja ștearsă")

    application.deleted_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            application_id=application.id,
            action=AuditAction.SOFT_DELETED,
            changes=None,
        )
    )

    try:
        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise VersionConflictError(
            "Aplicarea a fost modificată între timp. Reîncarcă și încearcă din nou."
        )


async def restore_application(
    db: AsyncSession, user_id: uuid.UUID, application_id: uuid.UUID
) -> JobApplication:
    application = await _get_owned_application(db, application_id, user_id)

    if application.deleted_at is None:
        raise InvalidStateError("Aplicarea nu este ștearsă")

    application.deleted_at = None
    db.add(
        AuditLog(
            application_id=application.id,
            action=AuditAction.RESTORED,
            changes=None,
        )
    )

    try:
        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise VersionConflictError(
            "Aplicarea a fost modificată între timp. Reîncarcă și încearcă din nou."
        )

    await db.refresh(application)
    return application



async def search_applications(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    include_deleted: bool,
    cursor: str | None,
    limit: int,
) -> CursorPage:
    limit = min(max(limit, 1), MAX_PAGE_SIZE)

    ts_query = func.plainto_tsquery("english", query)

    stmt = select(JobApplication).where(
        JobApplication.user_id == user_id,
        JobApplication.search_vector.op("@@")(ts_query),
    )

    if not include_deleted:
        stmt = stmt.where(JobApplication.deleted_at.is_(None))

    if cursor:
        cursor_created_at, cursor_id = decode_cursor(cursor)
        stmt = stmt.where(
            tuple_(JobApplication.created_at, JobApplication.id)
            < (cursor_created_at, cursor_id)
        )

    stmt = stmt.order_by(
        JobApplication.created_at.desc(), JobApplication.id.desc()
    ).limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorPage(items=items, next_cursor=next_cursor, has_more=has_more)