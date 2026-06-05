import pickle
import uuid
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from config import get_settings


class PredictionEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model: Pipeline | None = None
        self.feature_columns: list[str] = []
        self.target_column: str = ""
        self.model_version: str = ""
        self.numeric_cols: list[str] = []
        self.categorical_cols: list[str] = []

    def load(self) -> bool:
        path = Path(self.settings.model_path)
        if not path.exists():
            return False
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.feature_columns = data["feature_columns"]
        self.target_column = data["target_column"]
        self.model_version = data["model_version"]
        self.numeric_cols = data["numeric_cols"]
        self.categorical_cols = data["categorical_cols"]
        return True

    def save(self) -> None:
        path = Path(self.settings.model_path)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "feature_columns": self.feature_columns,
                    "target_column": self.target_column,
                    "model_version": self.model_version,
                    "numeric_cols": self.numeric_cols,
                    "categorical_cols": self.categorical_cols,
                },
                f,
            )

    def _clean_dataframe(self, df: pd.DataFrame, target_column: str) -> pd.DataFrame:
        threshold = 0.6
        df = df.dropna(subset=[target_column])
        cols_to_drop = [
            col
            for col in df.columns
            if col != target_column and df[col].isnull().mean() > threshold
        ]
        df = df.drop(columns=cols_to_drop)
        return df

    def _detect_column_types(
        self, df: pd.DataFrame, target_column: str
    ) -> tuple[list[str], list[str]]:
        feature_cols = [c for c in df.columns if c != target_column]
        numeric_cols = df[feature_cols].select_dtypes(include=np.number).columns.tolist()
        categorical_cols = [c for c in feature_cols if c not in numeric_cols]
        return numeric_cols, categorical_cols

    def _build_pipeline(
        self, numeric_cols: list[str], categorical_cols: list[str]
    ) -> Pipeline:
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
            ]
        )
        transformers = []
        if numeric_cols:
            transformers.append(("num", numeric_transformer, numeric_cols))
        if categorical_cols:
            transformers.append(("cat", categorical_transformer, categorical_cols))

        preprocessor = ColumnTransformer(transformers=transformers)
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
            ]
        )
        return pipeline

    def train(self, df: pd.DataFrame, target_column: str) -> dict:
        df = self._clean_dataframe(df, target_column)
        numeric_cols, categorical_cols = self._detect_column_types(df, target_column)
        feature_cols = numeric_cols + categorical_cols
        X = df[feature_cols]
        y = df[target_column]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        pipeline = self._build_pipeline(numeric_cols, categorical_cols)
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        metrics = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "f1_score": round(float(f1_score(y_test, y_pred, average="weighted")), 4),
            "precision": round(float(precision_score(y_test, y_pred, average="weighted")), 4),
            "recall": round(float(recall_score(y_test, y_pred, average="weighted")), 4),
        }
        self.model = pipeline
        self.feature_columns = feature_cols
        self.target_column = target_column
        self.model_version = str(uuid.uuid4())[:8]
        self.numeric_cols = numeric_cols
        self.categorical_cols = categorical_cols
        self.save()
        return metrics

    def predict_single(self, input_data: dict) -> tuple[int, float]:
        if self.model is None:
            raise RuntimeError("Modelo no cargado")
        df = pd.DataFrame([input_data])
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = np.nan
        df = df[self.feature_columns]
        prediction = int(self.model.predict(df)[0])
        probability = round(float(self.model.predict_proba(df)[0][1]), 4)
        return prediction, probability

    def predict_bulk(self, df: pd.DataFrame) -> list[dict]:
        if self.model is None:
            raise RuntimeError("Modelo no cargado")
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = np.nan
        df_input = df[self.feature_columns]
        predictions = self.model.predict(df_input).tolist()
        probabilities = self.model.predict_proba(df_input)[:, 1].tolist()
        results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            row = df.iloc[i].to_dict()
            row["_prediction"] = int(pred)
            row["_probability"] = round(float(prob), 4)
            results.append(row)
        return results

    def get_confusion_matrix_data(self, df: pd.DataFrame) -> dict:
        if self.model is None:
            raise RuntimeError("Modelo no cargado")
        if self.target_column not in df.columns:
            return {}
        X = df[self.feature_columns]
        y = df[self.target_column]
        y_pred = self.model.predict(X)
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y, y_pred)
        return {
            "tn": int(cm[0][0]),
            "fp": int(cm[0][1]),
            "fn": int(cm[1][0]),
            "tp": int(cm[1][1]),
        }


engine = PredictionEngine()