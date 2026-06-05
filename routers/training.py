import asyncio
import io
import pandas as pd
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from dependencies import require_session, require_admin_session
from models import ModelRecord
from ml_engine import engine
from config import get_settings, Settings


router = APIRouter(prefix="/training", tags=["training"])
templates = Jinja2Templates(directory="templates")


def validate_upload_file(file: UploadFile, settings: Settings) -> None:
    allowed_types = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    if ".." in (file.filename or "") or "/" in (file.filename or ""):
        raise HTTPException(status_code=400, detail="Nombre de archivo invalido")


async def read_dataframe(file: UploadFile) -> pd.DataFrame:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El archivo esta vacio")
    filename = file.filename or ""
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if filename.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(content), engine="openpyxl")
    if filename.endswith(".xls"):
        return pd.read_excel(io.BytesIO(content), engine="xlrd")
    raise HTTPException(status_code=400, detail="Extension de archivo no soportada")


def deactivate_all_models(session: Session) -> None:
    records = session.exec(select(ModelRecord)).all()
    for record in records:
        record.is_active = False
        session.add(record)
    session.commit()


def save_model_record(
    session: Session,
    metrics: dict,
    target_column: str,
    feature_columns: list[str],
    trained_by: str,
    version: str,
) -> ModelRecord:
    deactivate_all_models(session)
    record = ModelRecord(
        version=version,
        accuracy=metrics["accuracy"],
        f1_score=metrics["f1_score"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        target_column=target_column,
        feature_columns=",".join(feature_columns),
        trained_by=trained_by,
        is_active=True,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("/", response_class=HTMLResponse)
async def training_page(
    request: Request,
    current_user: dict = Depends(require_admin_session),
) -> HTMLResponse:
    return templates.TemplateResponse(
        "pages/training.html",
        {"request": request, "user": current_user},
    )


@router.post("/detect-columns", response_class=JSONResponse)
async def detect_columns(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin_session),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    validate_upload_file(file, settings)
    df = await read_dataframe(file)
    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo no contiene datos")
    columns = df.columns.tolist()
    return JSONResponse(content={"columns": columns})


@router.post("/train", response_class=JSONResponse)
async def train_model(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin_session),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    validate_upload_file(file, settings)
    df = await read_dataframe(file)

    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo no contiene datos")

    form = await request.form()
    target_column = str(form.get("target_column", "")).strip()

    if not target_column:
        raise HTTPException(status_code=400, detail="Columna objetivo requerida")

    if target_column not in df.columns:
        raise HTTPException(status_code=400, detail="Columna objetivo no encontrada en el dataset")

    unique_values = df[target_column].nunique()
    if unique_values != 2:
        raise HTTPException(
            status_code=400,
            detail=f"La columna objetivo debe tener exactamente 2 valores unicos, encontrados: {unique_values}",
        )

    loop = asyncio.get_event_loop()
    try:
        metrics = await loop.run_in_executor(
            None, engine.train, df, target_column
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el entrenamiento: {str(e)}")

    from main import get_db_session
    with get_db_session() as session:
        record = save_model_record(
            session,
            metrics,
            target_column,
            engine.feature_columns,
            current_user["user_id"],
            engine.model_version,
        )

    return JSONResponse(
        content={
            "version": engine.model_version,
            "accuracy": metrics["accuracy"],
            "f1_score": metrics["f1_score"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "message": "Modelo entrenado exitosamente",
        }
    )


@router.get("/models", response_class=HTMLResponse)
async def model_history_page(
    request: Request,
    current_user: dict = Depends(require_admin_session),
) -> HTMLResponse:
    from main import get_db_session
    with get_db_session() as session:
        records = session.exec(
            select(ModelRecord).order_by(ModelRecord.trained_at.desc())
        ).all()

    models = [
        {
            "id": r.id,
            "version": r.version,
            "accuracy": r.accuracy,
            "f1_score": r.f1_score,
            "precision": r.precision,
            "recall": r.recall,
            "target_column": r.target_column,
            "trained_at": r.trained_at.strftime("%Y-%m-%d %H:%M"),
            "is_active": r.is_active,
        }
        for r in records
    ]

    return templates.TemplateResponse(
        "pages/model_history.html",
        {"request": request, "user": current_user, "models": models},
    )