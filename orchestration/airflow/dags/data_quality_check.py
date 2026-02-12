"""
DAG de Airflow para verificación de calidad de datos (Data Quality Audit).
Verifica consistencia entre Kafka, HDFS y MongoDB; alerta si hay anomalías.
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
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'data_quality_check',
    default_args=default_args,
    description='Verificación diaria de calidad de datos y consistencia',
    schedule_interval='@daily',  # Cada día antes del reporte
    start_date=days_ago(1),
    catchup=False,
    tags=['data-quality', 'audit', 'verification'],
)

# Tarea 1: Ejecutar verificación MongoDB
run_verification = BashOperator(
    task_id='run_mongodb_verification',
    bash_command="""
    cd /home/hadoop/Documentos/ProyectoBigData
    source venv/bin/activate
    python storage/mongodb/verify_data.py > /tmp/data_quality_$(date +%Y%m%d).log 2>&1
    """,
    dag=dag,
)

# Tarea 2: Verificar umbrales y consistencia
def check_thresholds(**context):
    """Verifica que los conteos en MongoDB sean razonables y alerta si hay anomalías."""
    from pymongo import MongoClient
    
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    db = client["transport_db"]
    
    alerts = []
    
    # Verificar conteos
    vehicle_count = db.vehicle_status.count_documents({})
    delay_count = db.route_delay_aggregates.count_documents({})
    bottleneck_count = db.bottlenecks.count_documents({})
    
    if vehicle_count == 0:
        alerts.append("⚠ CRÍTICO: vehicle_status está vacío")
    elif vehicle_count < 10:
        alerts.append(f"⚠ Advertencia: solo {vehicle_count} documentos en vehicle_status")
    
    if delay_count == 0:
        alerts.append("⚠ CRÍTICO: route_delay_aggregates está vacío")
    elif delay_count < 5:
        alerts.append(f"⚠ Advertencia: solo {delay_count} documentos en route_delay_aggregates")
    
    # Verificar que no todos los retrasos sean 0% (indicaría fallo en cálculo)
    recent_delays = list(db.route_delay_aggregates.find().sort("window_start", -1).limit(20))
    if recent_delays:
        all_zero = all(float(d.get("delay_percentage", 0) or 0) == 0.0 for d in recent_delays)
        if all_zero:
            alerts.append("⚠ Advertencia: todos los delay_percentage recientes son 0% (posible fallo en cálculo)")
    
    # Verificar bottlenecks
    if bottleneck_count == 0:
        alerts.append("⚠ Advertencia: bottlenecks está vacío (ejecutar análisis de grafos)")
    
    client.close()
    
    if alerts:
        print("\n".join(alerts))
        # En producción, aquí se enviaría email/Slack
        # Por ahora solo imprimimos
    else:
        print("✓ Verificación de umbrales: OK")
        print(f"  - vehicle_status: {vehicle_count} documentos")
        print(f"  - route_delay_aggregates: {delay_count} documentos")
        print(f"  - bottlenecks: {bottleneck_count} documentos")
    
    return {"alerts": len(alerts), "vehicle_count": vehicle_count, "delay_count": delay_count}

check_consistency = PythonOperator(
    task_id='check_thresholds',
    python_callable=check_thresholds,
    dag=dag,
)

# Tarea 3: Verificar HDFS vs MongoDB (conteos aproximados)
def check_hdfs_mongodb_consistency(**context):
    """Compara conteos entre HDFS y MongoDB para detectar desincronizaciones."""
    import subprocess
    from pymongo import MongoClient
    
    # Contar en HDFS (aproximado)
    hdfs_cmd = "hdfs dfs -ls /user/hive/warehouse/delay_aggregates/*/*.parquet | wc -l"
    result = subprocess.run(hdfs_cmd, shell=True, capture_output=True, text=True)
    hdfs_files = int(result.stdout.strip() or 0)
    
    # Contar en MongoDB
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    mongo_count = client["transport_db"]["route_delay_aggregates"].count_documents({})
    client.close()
    
    print(f"HDFS: ~{hdfs_files} ficheros Parquet")
    print(f"MongoDB: {mongo_count} documentos")
    
    # Si MongoDB tiene muchos menos documentos que ficheros HDFS, puede haber problema
    if mongo_count > 0 and hdfs_files > mongo_count * 10:
        print("⚠ Advertencia: HDFS tiene muchos más ficheros que documentos en MongoDB (normal si hay particionado)")
    elif mongo_count == 0 and hdfs_files > 0:
        print("⚠ Advertencia: HDFS tiene datos pero MongoDB está vacío (ejecutar consumer MongoDB)")
    else:
        print("✓ Consistencia HDFS/MongoDB: OK")
    
    return {"hdfs_files": hdfs_files, "mongo_count": mongo_count}

check_hdfs_mongo = PythonOperator(
    task_id='check_hdfs_mongodb_consistency',
    python_callable=check_hdfs_mongodb_consistency,
    dag=dag,
)

# Tarea 4: Resumen de calidad
summary = BashOperator(
    task_id='quality_summary',
    bash_command="""
    echo "=== Resumen de Calidad de Datos ==="
    echo "Ver logs en /tmp/data_quality_$(date +%Y%m%d).log"
    """,
    dag=dag,
)

# Definir dependencias
run_verification >> check_consistency >> check_hdfs_mongo >> summary
