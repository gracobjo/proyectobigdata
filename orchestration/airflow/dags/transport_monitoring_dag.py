"""
DAG de Airflow para orquestar el pipeline de monitorización de transporte
Incluye re-entrenamiento mensual del modelo de grafos y limpieza de tablas temporales
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago

# Argumentos por defecto
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Definir el DAG
dag = DAG(
    'transport_monitoring_pipeline',
    default_args=default_args,
    description='Pipeline completo de monitorización de transporte',
    schedule_interval='@daily',  # Ejecutar diariamente
    start_date=days_ago(1),
    catchup=False,
    tags=['transport', 'big-data', 'kdd'],
)

# Tarea 1: Verificar servicios
check_services = BashOperator(
    task_id='check_services',
    bash_command="""
    echo "Verificando servicios..."
    jps | grep -E "(NameNode|ResourceManager|Kafka|NiFi)" || exit 1
    echo "Servicios activos"
    """,
    dag=dag,
)

# Tarea 2: Limpieza de datos (Fase II)
data_cleaning = SparkSubmitOperator(
    task_id='data_cleaning',
    application='/home/hadoop/Documentos/ProyectoBigData/processing/spark/sql/data_cleaning.py',
    conn_id='spark_default',
    total_executor_cores=4,
    executor_cores=2,
    executor_memory='2g',
    driver_memory='1g',
    name='data_cleaning',
    dag=dag,
)

# Tarea 3: Enriquecimiento de datos (Fase II)
data_enrichment = SparkSubmitOperator(
    task_id='data_enrichment',
    application='/home/hadoop/Documentos/ProyectoBigData/processing/spark/sql/data_enrichment.py',
    conn_id='spark_default',
    total_executor_cores=4,
    executor_cores=2,
    executor_memory='2g',
    driver_memory='1g',
    name='data_enrichment',
    dag=dag,
)

# Tarea 4: Análisis de red con GraphFrames (Fase II)
network_analysis = SparkSubmitOperator(
    task_id='network_analysis',
    application='/home/hadoop/Documentos/ProyectoBigData/processing/spark/graphframes/network_analysis.py',
    conn_id='spark_default',
    packages='graphframes:graphframes:0.8.2-spark3.5-s_2.12',
    total_executor_cores=4,
    executor_cores=2,
    executor_memory='2g',
    driver_memory='1g',
    name='network_analysis',
    dag=dag,
)

# Tarea 5: Análisis de retrasos (Fase III)
delay_analysis = SparkSubmitOperator(
    task_id='delay_analysis',
    application='/home/hadoop/Documentos/ProyectoBigData/processing/spark/streaming/delay_analysis.py',
    conn_id='spark_default',
    packages='org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0',
    total_executor_cores=4,
    executor_cores=2,
    executor_memory='2g',
    driver_memory='1g',
    name='delay_analysis',
    dag=dag,
)

# Tarea 6: Limpieza de tablas temporales en HDFS
def cleanup_temp_tables():
    """Limpia tablas temporales antiguas en HDFS"""
    import subprocess
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_str = cutoff_date.strftime('%Y%m%d')
    
    # Eliminar particiones antiguas
    cleanup_cmd = f"""
    hdfs dfs -rm -r /user/hadoop/processed/enriched/*/date={cutoff_str}* || true
    hdfs dfs -rm -r /user/hadoop/checkpoints/*/date={cutoff_str}* || true
    """
    
    subprocess.run(cleanup_cmd, shell=True)
    print(f"Limpieza completada para datos anteriores a {cutoff_date}")

cleanup_temp = PythonOperator(
    task_id='cleanup_temp_tables',
    python_callable=cleanup_temp_tables,
    dag=dag,
)

# Tarea 7: Generar reporte diario
generate_report = BashOperator(
    task_id='generate_daily_report',
    bash_command="""
    hive -f /home/hadoop/Documentos/ProyectoBigData/storage/hive/daily_report.sql \
    > /tmp/transport_report_$(date +%Y%m%d).txt 2>&1
    """,
    dag=dag,
)

# Definir dependencias
check_services >> [data_cleaning, data_enrichment]
data_cleaning >> network_analysis
data_enrichment >> delay_analysis
network_analysis >> cleanup_temp
delay_analysis >> cleanup_temp
cleanup_temp >> generate_report
