"""
DAG de Airflow para re-entrenamiento mensual del modelo de grafos
Ejecuta análisis completo de red y actualiza modelos de predicción
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(hours=1),
}

dag = DAG(
    'monthly_model_retraining',
    default_args=default_args,
    description='Re-entrenamiento mensual del modelo de análisis de grafos',
    schedule_interval='@monthly',  # Primer día de cada mes
    start_date=days_ago(1),
    catchup=False,
    tags=['model', 'retraining', 'graphframes'],
)

# Tarea 1: Backup del modelo actual
backup_current_model = BashOperator(
    task_id='backup_current_model',
    bash_command="""
    BACKUP_DIR="/tmp/model_backups/$(date +%Y%m%d)"
    mkdir -p $BACKUP_DIR
    hdfs dfs -copyToLocal /user/hive/warehouse/network_pagerank $BACKUP_DIR/ || true
    hdfs dfs -copyToLocal /user/hive/warehouse/network_degrees $BACKUP_DIR/ || true
    hdfs dfs -copyToLocal /user/hive/warehouse/network_bottlenecks $BACKUP_DIR/ || true
    echo "Backup completado en $BACKUP_DIR"
    """,
    dag=dag,
)

# Tarea 2: Re-entrenar modelo de grafos
retrain_graph_model = SparkSubmitOperator(
    task_id='retrain_graph_model',
    application='/home/hadoop/Documentos/ProyectoBigData/processing/spark/graphframes/network_analysis.py',
    conn_id='spark_default',
    packages='graphframes:graphframes:0.8.2-spark3.5-s_2.12',
    total_executor_cores=8,
    executor_cores=4,
    executor_memory='4g',
    driver_memory='2g',
    name='retrain_graph_model',
    dag=dag,
)

# Tarea 3: Validar nuevo modelo
validate_model = BashOperator(
    task_id='validate_model',
    bash_command="""
    echo "Validando nuevo modelo..."
    hive -e "SELECT COUNT(*) FROM network_pagerank;" || exit 1
    hive -e "SELECT COUNT(*) FROM network_degrees;" || exit 1
    echo "Modelo validado correctamente"
    """,
    dag=dag,
)

# Tarea 4: Notificar completación
notify_completion = BashOperator(
    task_id='notify_completion',
    bash_command="""
    echo "Re-entrenamiento mensual completado exitosamente"
    # Aquí se podría enviar un email o notificación
    """,
    dag=dag,
)

# Definir dependencias
backup_current_model >> retrain_graph_model >> validate_model >> notify_completion
