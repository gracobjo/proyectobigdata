#!/bin/bash
# Script helper para usar Airflow con el entorno virtual activado
# Uso: source scripts/utils/airflow_helper.sh
# Luego puedes usar: airflow dags list, airflow dags unpause <dag_id>, etc.

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
export AIRFLOW_HOME=~/airflow

echo "✓ Entorno virtual activado"
echo "✓ AIRFLOW_HOME=$AIRFLOW_HOME"
echo ""
echo "Comandos útiles:"
echo "  airflow dags list                    # Listar todos los DAGs"
echo "  airflow dags unpause <dag_id>        # Activar un DAG"
echo "  airflow dags pause <dag_id>          # Pausar un DAG"
echo "  airflow dags trigger <dag_id>        # Ejecutar un DAG manualmente"
echo "  airflow dags show <dag_id>           # Mostrar detalles de un DAG"
echo ""
