"""
DAG de Airflow para entrenamiento semanal del modelo de predicción de retrasos (IA).
Entrena RandomForestRegressor usando histórico de route_delay_aggregates.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'weekly_delay_model_training',
    default_args=default_args,
    description='Entrenamiento semanal del modelo de predicción de retrasos (IA)',
    schedule_interval='@weekly',  # Cada lunes
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'ai', 'delay-prediction', 'routing'],
)

# Tarea 1: Verificar que existen datos en MongoDB
def check_mongodb_data(**context):
    """Sensor: verificar que hay suficientes datos en route_delay_aggregates."""
    from pymongo import MongoClient
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    db = client["transport_db"]
    count = db.route_delay_aggregates.count_documents({})
    client.close()
    if count < 50:
        raise ValueError(f"Solo hay {count} documentos. Se requieren al menos 50 para entrenar.")
    print(f"✓ Encontrados {count} documentos en route_delay_aggregates")
    return count

check_data = PythonOperator(
    task_id='check_mongodb_data',
    python_callable=check_mongodb_data,
    dag=dag,
)

# Tarea 2: Backup del modelo anterior
backup_old_model = BashOperator(
    task_id='backup_old_model',
    bash_command="""
    cd /home/hadoop/Documentos/ProyectoBigData
    BACKUP_DIR="routing/model_backups/$(date +%Y%m%d)"
    mkdir -p $BACKUP_DIR
    [ -f routing/model_delay.joblib ] && cp routing/model_delay.joblib $BACKUP_DIR/ || true
    [ -f routing/encoder_route.joblib ] && cp routing/encoder_route.joblib $BACKUP_DIR/ || true
    echo "Backup guardado en $BACKUP_DIR"
    """,
    dag=dag,
)

# Tarea 3: Entrenar modelo
train_model = BashOperator(
    task_id='train_delay_model',
    bash_command="""
    cd /home/hadoop/Documentos/ProyectoBigData
    source venv/bin/activate
    python -m routing.train_delay_model --min-samples 50
    """,
    dag=dag,
)

# Tarea 4: Validar modelo (comparar precisión)
def validate_model(**context):
    """Compara la precisión del nuevo modelo con el anterior (si existe)."""
    import os
    import joblib
    from pymongo import MongoClient
    import pandas as pd
    from sklearn.metrics import mean_absolute_error, r2_score
    
    model_path = "/home/hadoop/Documentos/ProyectoBigData/routing/model_delay.joblib"
    encoder_path = "/home/hadoop/Documentos/ProyectoBigData/routing/encoder_route.joblib"
    
    if not os.path.isfile(model_path):
        raise FileNotFoundError("Modelo no encontrado tras el entrenamiento")
    
    model = joblib.load(model_path)
    encoder = joblib.load(encoder_path)
    
    # Cargar datos de prueba (últimos 20% de MongoDB)
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    db = client["transport_db"]
    cursor = db.route_delay_aggregates.find().sort("window_start", -1).limit(100)
    df = pd.DataFrame(list(cursor))
    client.close()
    
    if len(df) < 10:
        print("⚠ Pocos datos para validación, pero el modelo existe")
        return
    
    df["window_start"] = pd.to_datetime(df["window_start"], utc=True)
    df["hour"] = df["window_start"].dt.hour
    df["day_of_week"] = df["window_start"].dt.dayofweek
    df["month"] = df["window_start"].dt.month
    df["delay_percentage"] = pd.to_numeric(df["delay_percentage"], errors="coerce").fillna(0)
    
    try:
        df["route_id_enc"] = encoder.transform(df["route_id"].astype(str))
    except Exception:
        print("⚠ Algunos route_id no están en el encoder (normal si hay datos nuevos)")
        return
    
    X = df[["route_id_enc", "hour", "day_of_week", "month"]]
    y_true = df["delay_percentage"]
    y_pred = model.predict(X)
    
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"✓ Validación: MAE={mae:.2f}%, R²={r2:.4f}")
    if r2 < 0.3:
        print("⚠ R² bajo: el modelo puede no ser muy preciso")
    
    return {"mae": mae, "r2": r2}

validate_new_model = PythonOperator(
    task_id='validate_new_model',
    python_callable=validate_model,
    dag=dag,
)

# Tarea 5: Notificar completación
notify_completion = BashOperator(
    task_id='notify_completion',
    bash_command="""
    echo "Entrenamiento semanal del modelo de retrasos completado"
    echo "Modelo disponible en routing/model_delay.joblib"
    """,
    dag=dag,
)

# Definir dependencias
check_data >> backup_old_model >> train_model >> validate_new_model >> notify_completion
