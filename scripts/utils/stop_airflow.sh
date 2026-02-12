#!/bin/bash
# Script para detener Airflow (scheduler y webserver)
# Uso: bash scripts/utils/stop_airflow.sh

echo "=== Deteniendo Apache Airflow ==="

# Detener scheduler
if pgrep -f "airflow scheduler" > /dev/null; then
    pkill -f "airflow scheduler"
    echo "✓ Scheduler detenido"
else
    echo "⚠ Scheduler no estaba corriendo"
fi

# Detener webserver
if pgrep -f "airflow webserver" > /dev/null; then
    pkill -f "airflow webserver"
    echo "✓ Webserver detenido"
else
    echo "⚠ Webserver no estaba corriendo"
fi

echo ""
echo "Para verificar procesos restantes:"
echo "  ps aux | grep airflow"
