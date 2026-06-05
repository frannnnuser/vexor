from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func, case
from dependencies import require_session
from models import PredictionRecord, ModelRecord
from datetime import datetime, timedelta


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


def get_dashboard_stats(session: Session) -> dict:
    total = session.exec(select(func.count(PredictionRecord.id))).one()
    positive = session.exec(
        select(func.count(PredictionRecord.id)).where(PredictionRecord.prediction == 1)
    ).one()
    negative = total - positive
    positive_rate = round((positive / total * 100), 2) if total > 0 else 0.0

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": positive_rate,
    }


def get_trend_data(session: Session) -> dict:
    since = datetime.utcnow() - timedelta(days=30)
    records = session.exec(
        select(PredictionRecord).where(PredictionRecord.created_at >= since)
    ).all()

    trend: dict[str, int] = {}
    for record in records:
        day = record.created_at.strftime("%Y-%m-%d")
        trend[day] = trend.get(day, 0) + 1

    sorted_days = sorted(trend.keys())
    return {
        "labels": sorted_days,
        "values": [trend[d] for d in sorted_days],
    }


def get_probability_distribution(session: Session) -> dict:
    records = session.exec(select(PredictionRecord.probability)).all()
    buckets = [0] * 10
    for prob in records:
        index = min(int(prob * 10), 9)
        buckets[index] += 1
    labels = [f"{i*10}-{i*10+10}%" for i in range(10)]
    return {"labels": labels, "values": buckets}


def get_confusion_matrix(session: Session) -> dict:
    records = session.exec(
        select(PredictionRecord.prediction, PredictionRecord.probability)
    ).all()
    tp = sum(1 for p, prob in records if p == 1 and prob >= 0.5)
    fp = sum(1 for p, prob in records if p == 1 and prob < 0.5)
    fn = sum(1 for p, prob in records if p == 0 and prob >= 0.5)
    tn = sum(1 for p, prob in records if p == 0 and prob < 0.5)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def get_active_model(session: Session) -> ModelRecord | None:
    return session.exec(
        select(ModelRecord).where(ModelRecord.is_active == True)
    ).first()


def get_confidence_label(f1: float) -> str:
    if f1 >= 0.9:
        return "Alta"
    if f1 >= 0.75:
        return "Media"
    return "Baja"


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: dict = Depends(require_session),
) -> HTMLResponse:
    from main import get_db_session
    with get_db_session() as session:
        stats = get_dashboard_stats(session)
        trend = get_trend_data(session)
        distribution = get_probability_distribution(session)
        confusion = get_confusion_matrix(session)
        active_model = get_active_model(session)

    confidence = ""
    if active_model:
        confidence = get_confidence_label(active_model.f1_score)

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "trend": trend,
            "distribution": distribution,
            "confusion": confusion,
            "active_model": active_model,
            "confidence": confidence,
        },
    )