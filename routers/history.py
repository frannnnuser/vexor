import csv
import json
import io
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func, col
from dependencies import require_session, require_admin_session
from models import PredictionRecord


router = APIRouter(prefix="/history", tags=["history"])
templates = Jinja2Templates(directory="templates")


def get_predictions_paginated(
    session: Session,
    page: int,
    page_size: int,
    search: str,
    filter_prediction: int | None,
) -> tuple[list[dict], int]:
    query = select(PredictionRecord)
    count_query = select(func.count(PredictionRecord.id))

    if filter_prediction is not None:
        query = query.where(PredictionRecord.prediction == filter_prediction)
        count_query = count_query.where(PredictionRecord.prediction == filter_prediction)

    total = session.exec(count_query).one()
    offset = (page - 1) * page_size
    records = session.exec(
        query.order_by(col(PredictionRecord.created_at).desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    items = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "prediction": r.prediction,
            "probability": r.probability,
            "model_version": r.model_version,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "input_data": json.loads(r.input_data),
        }
        for r in records
    ]

    if search:
        items = [
            item for item in items
            if search.lower() in json.dumps(item).lower()
        ]

    return items, total


@router.get("/", response_class=HTMLResponse)
async def history_page(
    request: Request,
    current_user: dict = Depends(require_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    search: str = Query(default=""),
    filter_prediction: int | None = Query(default=None),
) -> HTMLResponse:
    from main import get_db_session
    with get_db_session() as session:
        items, total = get_predictions_paginated(
            session, page, page_size, search, filter_prediction
        )

    total_pages = (total + page_size - 1) // page_size

    return templates.TemplateResponse(
        "pages/history.html",
        {
            "request": request,
            "user": current_user,
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "search": search,
            "filter_prediction": filter_prediction,
        },
    )


@router.get("/export", response_class=StreamingResponse)
async def export_history(
    request: Request,
    current_user: dict = Depends(require_session),
    filter_prediction: int | None = Query(default=None),
) -> StreamingResponse:
    from main import get_db_session
    with get_db_session() as session:
        query = select(PredictionRecord)
        if filter_prediction is not None:
            query = query.where(PredictionRecord.prediction == filter_prediction)
        records = session.exec(
            query.order_by(col(PredictionRecord.created_at).desc())
        ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "prediction", "probability", "model_version", "created_at", "input_data"])
    for r in records:
        writer.writerow([
            r.id,
            r.user_id,
            r.prediction,
            r.probability,
            r.model_version,
            r.created_at.strftime("%Y-%m-%d %H:%M"),
            r.input_data,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"},
    )


@router.delete("/{prediction_id}")
async def delete_prediction(
    prediction_id: int,
    current_user: dict = Depends(require_admin_session),
) -> JSONResponse:
    from main import get_db_session
    with get_db_session() as session:
        record = session.get(PredictionRecord, prediction_id)
        if not record:
            raise HTTPException(status_code=404, detail="Prediccion no encontrada")
        session.delete(record)
        session.commit()

    return JSONResponse(content={"message": "Prediccion eliminada correctamente"})