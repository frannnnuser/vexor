import csv
import io
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func, col
from dependencies import require_admin_session
from models import AuditLog


router = APIRouter(prefix="/audit", tags=["audit"])
templates = Jinja2Templates(directory="templates")


def log_action(
    session: Session,
    user_id: str,
    email: str,
    action: str,
    detail: str,
    ip_address: str,
) -> None:
    record = AuditLog(
        user_id=user_id,
        email=email,
        action=action,
        detail=detail,
        ip_address=ip_address,
    )
    session.add(record)
    session.commit()


def get_audit_logs_paginated(
    session: Session,
    page: int,
    page_size: int,
    search: str,
    filter_action: str,
) -> tuple[list[dict], int]:
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if filter_action:
        query = query.where(AuditLog.action == filter_action)
        count_query = count_query.where(AuditLog.action == filter_action)

    total = session.exec(count_query).one()
    offset = (page - 1) * page_size
    records = session.exec(
        query.order_by(col(AuditLog.created_at).desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    items = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "email": r.email,
            "action": r.action,
            "detail": r.detail,
            "ip_address": r.ip_address,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for r in records
    ]

    if search:
        items = [
            item for item in items
            if search.lower() in str(item).lower()
        ]

    return items, total


def get_unique_actions(session: Session) -> list[str]:
    records = session.exec(select(AuditLog.action).distinct()).all()
    return list(records)


@router.get("/", response_class=HTMLResponse)
async def audit_page(
    request: Request,
    current_user: dict = Depends(require_admin_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    search: str = Query(default=""),
    filter_action: str = Query(default=""),
) -> HTMLResponse:
    from main import get_db_session
    with get_db_session() as session:
        items, total = get_audit_logs_paginated(
            session, page, page_size, search, filter_action
        )
        actions = get_unique_actions(session)

    total_pages = (total + page_size - 1) // page_size

    return templates.TemplateResponse(
        "pages/audit.html",
        {
            "request": request,
            "user": current_user,
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "search": search,
            "filter_action": filter_action,
            "actions": actions,
        },
    )


@router.get("/export", response_class=StreamingResponse)
async def export_audit(
    request: Request,
    current_user: dict = Depends(require_admin_session),
    filter_action: str = Query(default=""),
) -> StreamingResponse:
    from main import get_db_session
    with get_db_session() as session:
        query = select(AuditLog)
        if filter_action:
            query = query.where(AuditLog.action == filter_action)
        records = session.exec(
            query.order_by(col(AuditLog.created_at).desc())
        ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "email", "action", "detail", "ip_address", "created_at"])
    for r in records:
        writer.writerow([
            r.id,
            r.user_id,
            r.email,
            r.action,
            r.detail,
            r.ip_address,
            r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )