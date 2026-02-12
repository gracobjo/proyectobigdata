"""
DAG de Airflow para generación continua de datos de simulación.
Mantiene el flujo de datos vivo para desarrollo/demos.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': False,  # No alertar en fallos de simulación
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'simulation_data_stream',
    default_args=default_args,
    description='Generación continua de datos GPS simulados (cada 15 min)',
    schedule_interval='*/15 * * * *',  # Cada 15 minutos
    start_date=days_ago(1),
    catchup=False,
    tags=['simulation', 'data-generation', 'development'],
)

# Tarea única: Generar datos de prueba
generate_data = BashOperator(
    task_id='generate_sample_data',
    bash_command="""
    cd /home/hadoop/Documentos/ProyectoBigData
    source venv/bin/activate
    # Generar un pequeño lote cada vez (10-20 mensajes) para no saturar
    python scripts/utils/generate_sample_data.py 15
    echo "Datos generados: $(date)"
    """,
    dag=dag,
)

# Este DAG solo tiene una tarea
generate_data
