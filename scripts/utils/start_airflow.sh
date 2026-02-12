#!/bin/bash
# Script para iniciar Airflow (scheduler y webserver)
# Uso: bash scripts/utils/start_airflow.sh

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
export AIRFLOW_HOME=~/airflow

echo "=== Iniciando Apache Airflow ==="
echo "AIRFLOW_HOME: $AIRFLOW_HOME"
echo ""

# Verificar que la base de datos esté inicializada
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
    echo "⚠ Base de datos no encontrada. Ejecutando 'airflow db init'..."
    airflow db init
fi

# Verificar si el scheduler ya está corriendo
if pgrep -f "airflow scheduler" > /dev/null; then
    echo "⚠ El scheduler ya está corriendo (PID: $(pgrep -f 'airflow scheduler'))"
else
    echo "Iniciando scheduler..."
    airflow scheduler > "$AIRFLOW_HOME/logs/scheduler.log" 2>&1 &
    SCHEDULER_PID=$!
    echo "✓ Scheduler iniciado (PID: $SCHEDULER_PID)"
    echo "  Logs: $AIRFLOW_HOME/logs/scheduler.log"
fi

# Forzar registro de DAGs en la base de datos (reserialize)
echo "Registrando DAGs en la base de datos..."
airflow dags reserialize > /dev/null 2>&1

# Esperar un momento para que el scheduler procese los DAGs
sleep 3

# Verificar si el webserver ya está corriendo
if pgrep -f "airflow webserver" > /dev/null; then
    echo "⚠ El webserver ya está corriendo (PID: $(pgrep -f 'airflow webserver'))"
else
    echo "Iniciando webserver..."
    airflow webserver --port 8080 > "$AIRFLOW_HOME/logs/webserver.log" 2>&1 &
    WEBSERVER_PID=$!
    echo "✓ Webserver iniciado (PID: $WEBSERVER_PID)"
    echo "  URL: http://localhost:8080"
    echo "  Logs: $AIRFLOW_HOME/logs/webserver.log"
fi

echo ""
echo "=== Estado de los DAGs ==="
airflow dags list 2>&1 | grep -E "dag_id|==|data_quality|executive|monthly|simulation|system|transport|weekly" | head -10

echo ""
echo "Para detener Airflow:"
echo "  pkill -f 'airflow scheduler'"
echo "  pkill -f 'airflow webserver'"
echo ""
echo "O usar: bash scripts/utils/stop_airflow.sh"
