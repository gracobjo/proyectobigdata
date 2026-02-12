"""
DAG de Airflow para mantenimiento y limpieza del sistema (Housekeeping).
Limpia datos antiguos en HDFS, rota logs y optimiza almacenamiento.
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
    'system_maintenance',
    default_args=default_args,
    description='Mantenimiento y limpieza: HDFS, logs, optimización',
    schedule_interval='@weekly',  # Cada lunes
    start_date=days_ago(1),
    catchup=False,
    tags=['maintenance', 'housekeeping', 'cleanup'],
)

# Tarea 1: Limpiar datos raw antiguos en HDFS (>30 días)
def cleanup_hdfs_raw(**context):
    """Elimina ficheros en /user/hadoop/raw/ con más de 30 días."""
    import subprocess
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=30)
    cutoff_str = cutoff.strftime('%Y%m%d')
    
    cmd = f"""
    hdfs dfs -ls /user/hadoop/raw/ | grep -E "{cutoff_str}|$(date -d '30 days ago' +%Y%m%d)" | \
    awk '{{print $8}}' | xargs -r hdfs dfs -rm -r || true
    """
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Limpieza HDFS raw completada (datos anteriores a {cutoff.date()})")
    if result.stderr and "No such file" not in result.stderr:
        print(f"Advertencia: {result.stderr}")
    return result.returncode == 0

cleanup_hdfs = PythonOperator(
    task_id='cleanup_hdfs_raw',
    python_callable=cleanup_hdfs_raw,
    dag=dag,
)

# Tarea 2: Limpiar checkpoints antiguos
cleanup_checkpoints = BashOperator(
    task_id='cleanup_checkpoints',
    bash_command="""
    # Eliminar checkpoints de Spark con más de 7 días
    CUTOFF=$(date -d '7 days ago' +%s)
    hdfs dfs -ls /user/hadoop/checkpoints/*/ | while read line; do
        MOD_TIME=$(echo $line | awk '{print $6" "$7}')
        MOD_TS=$(date -d "$MOD_TIME" +%s)
        if [ $MOD_TS -lt $CUTOFF ]; then
            PATH=$(echo $line | awk '{print $8}')
            hdfs dfs -rm -r $PATH || true
        fi
    done
    echo "Limpieza de checkpoints completada"
    """,
    dag=dag,
)

# Tarea 3: Rotar logs de Airflow (mantener últimos 30 días)
rotate_airflow_logs = BashOperator(
    task_id='rotate_airflow_logs',
    bash_command="""
    LOG_DIR="$HOME/airflow/logs"
    if [ -d "$LOG_DIR" ]; then
        find $LOG_DIR -type f -mtime +30 -delete || true
        echo "Logs de Airflow rotados (mantenidos últimos 30 días)"
    else
        echo "Directorio de logs no encontrado"
    fi
    """,
    dag=dag,
)

# Tarea 4: Optimizar Parquet (compactar pequeños ficheros)
def optimize_parquet(**context):
    """Sugiere compactación de Parquet pequeños (ejecutar manualmente si es necesario)."""
    import subprocess
    
    # Listar particiones pequeñas que podrían beneficiarse de compactación
    cmd = "hdfs dfs -du -h /user/hadoop/processed/enriched/*/* | awk '$1 < 1048576 {print}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("⚠ Particiones pequeñas encontradas (considerar compactación):")
        print(result.stdout)
    else:
        print("✓ No se encontraron particiones pequeñas que requieran optimización")
    
    return True

optimize_storage = PythonOperator(
    task_id='optimize_storage',
    python_callable=optimize_parquet,
    dag=dag,
)

# Tarea 5: Reporte de espacio liberado
report_space = BashOperator(
    task_id='report_space',
    bash_command="""
    echo "=== Reporte de Mantenimiento ==="
    echo "Espacio usado en HDFS:"
    hdfs dfs -du -h /user/hadoop/ | tail -1
    echo "Espacio en disco local (logs):"
    df -h ~/airflow/logs 2>/dev/null || echo "N/A"
    """,
    dag=dag,
)

# Definir dependencias
cleanup_hdfs >> cleanup_checkpoints >> rotate_airflow_logs >> optimize_storage >> report_space
