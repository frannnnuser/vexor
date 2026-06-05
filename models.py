from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class PredictionRecord(SQLModel, table=True):
    __tablename__ = "predictions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    input_data: str
    prediction: int
    probability: float
    model_version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelRecord(SQLModel, table=True):
    __tablename__ = "models"

    id: Optional[int] = Field(default=None, primary_key=True)
    version: str = Field(index=True, unique=True)
    accuracy: float
    f1_score: float
    precision: float
    recall: float
    target_column: str
    feature_columns: str
    trained_by: str
    trained_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=False)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    email: str
    action: str
    detail: str
    ip_address: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class PredictionRequest(BaseModel):
    input_data: dict


class BulkPredictionResponse(BaseModel):
    total: int
    positive: int
    negative: int
    results: list[dict]


class TrainingResponse(BaseModel):
    version: str
    accuracy: float
    f1_score: float
    precision: float
    recall: float
    message: str


class PaginatedPredictions(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[dict]