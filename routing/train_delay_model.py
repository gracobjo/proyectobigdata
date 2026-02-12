"""
Paso 2 (IA): Entrenar modelo de predicción de retrasos a partir de route_delay_aggregates.
Features: route_id (codificado), hour, day_of_week, month. Target: delay_percentage.
Guarda el modelo en routing/model_delay.joblib y el LabelEncoder en routing/encoder_route.joblib.
"""
import os
import argparse
from datetime import datetime
from pymongo import MongoClient
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

MONGO_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "transport_db"
COLLECTION = "route_delay_aggregates"
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model_delay.joblib")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoder_route.joblib")


def load_dataset_from_mongodb(limit=None):
    """Carga agregados de retrasos desde MongoDB y construye DataFrame."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    coll = client[DB_NAME][COLLECTION]
    cursor = coll.find({}, {"_id": 0, "window_start": 1, "route_id": 1, "delay_percentage": 1, "avg_speed": 1})
    if limit:
        cursor = cursor.limit(limit)
    rows = list(cursor)
    if not rows:
        raise ValueError("No hay documentos en route_delay_aggregates. Ejecuta el pipeline (delay_analysis + consumer MongoDB).")
    df = pd.DataFrame(rows)
    df["window_start"] = pd.to_datetime(df["window_start"], utc=True)
    df["hour"] = df["window_start"].dt.hour
    df["day_of_week"] = df["window_start"].dt.dayofweek
    df["month"] = df["window_start"].dt.month
    df["delay_percentage"] = pd.to_numeric(df["delay_percentage"], errors="coerce").fillna(0)
    return df[["route_id", "hour", "day_of_week", "month", "delay_percentage"]]


def train_and_save(min_samples=50):
    """
    Entrena RandomForestRegressor para predecir delay_percentage.
    Guarda modelo y encoder en routing/.
    """
    df = load_dataset_from_mongodb()
    if len(df) < min_samples:
        print(f"Advertencia: solo {len(df)} muestras. Se recomienda al menos {min_samples}.")
    le = LabelEncoder()
    df["route_id_enc"] = le.fit_transform(df["route_id"].astype(str))
    X = df[["route_id_enc", "hour", "day_of_week", "month"]]
    y = df["delay_percentage"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"Modelo guardado en {MODEL_PATH}. R² test: {score:.4f}")
    return model, le


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenar modelo de predicción de retrasos")
    parser.add_argument("--min-samples", type=int, default=50, help="Mínimo de muestras recomendado")
    args = parser.parse_args()
    train_and_save(min_samples=args.min_samples)
