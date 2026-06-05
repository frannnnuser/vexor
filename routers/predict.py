import json
import asyncio
import pandas as pd
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from dependencies import require_session
from models import PredictionRecord, BulkPredictionResponse
from ml_engine import engine
from config import get_settings, Settings
from datetime import datetime
import io


router = APIRouter(prefix="/predict", tags=["predict"])
templates = Jinja2Templates(directory="templates")


def save_prediction(
    session: Session,
    user_id: str,
    input_data: dict,
    prediction: int,
    probability: float,
    model_version: str,
) -> None:
    record = PredictionRecord(
        user_id=user_id,
        input_data=json.dumps(input_data),
        prediction=prediction,
        probability=probability,
        model_version=model_version,
    )
    session.add(record)
    session.commit()


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


@router.get("/", response_class=HTMLResponse)
async def predict_page(
    request: Request,
    current_user: dict = Depends(require_session),
) -> HTMLResponse:
    if not engine.model:
        engine.load()
    feature_columns = engine.feature_columns if engine.model else []
    return templates.TemplateResponse(
        "pages/predict.html",
        {
            "request": request,
            "user": current_user,
            "feature_columns": feature_columns,
            "model_loaded": engine.model is not None,
        },
    )


@router.post("/single", response_class=JSONResponse)
async def predict_single(
    request: Request,
    current_user: dict = Depends(require_session),
) -> JSONResponse:
    if not engine.model:
        engine.load()
    if not engine.model:
        raise HTTPException(status_code=503, detail="Modelo no disponible")

    body = await request.json()
    input_data = body.get("input_data", {})
    if not input_data:
        raise HTTPException(status_code=400, detail="Datos de entrada requeridos")

    loop = asyncio.get_event_loop()
    prediction, probability = await loop.run_in_executor(
        None, engine.predict_single, input_data
    )

    from main import get_db_session
    with get_db_session() as session:
        save_prediction(
            session,
            current_user["user_id"],
            input_data,
            prediction,
            probability,
            engine.model_version,
        )

    return JSONResponse(
        content={
            "prediction": prediction,
            "probability": probability,
            "model_version": engine.model_version,
        }
    )


@router.get("/bulk", response_class=HTMLResponse)
async def predict_bulk_page(
    request: Request,
    current_user: dict = Depends(require_session),
) -> HTMLResponse:
    if not engine.model:
        engine.load()
    return templates.TemplateResponse(
        "pages/predict_bulk.html",
        {
            "request": request,
            "user": current_user,
            "model_loaded": engine.model is not None,
        },
    )


@router.post("/bulk", response_class=JSONResponse)
async def predict_bulk(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_session),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not engine.model:
        engine.load()
    if not engine.model:
        raise HTTPException(status_code=503, detail="Modelo no disponible")

    validate_upload_file(file, settings)
    df = await read_dataframe(file)

    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo no contiene datos")

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, engine.predict_bulk, df)

    from main import get_db_session
    with get_db_session() as session:
        for row in results:
            input_data = {k: v for k, v in row.items() if not k.startswith("_")}
            save_prediction(
                session,
                current_user["user_id"],
                input_data,
                row["_prediction"],
                row["_probability"],
                engine.model_version,
            )

    total = len(results)
    positive = sum(1 for r in results if r["_prediction"] == 1)
    negative = total - positive

    return JSONResponse(
        content={
            "total": total,
            "positive": positive,
            "negative": negative,
            "results": results,
        }
    )