#!/bin/bash
# Comprueba el estado de todos los componentes de la arquitectura.
# Uso: bash scripts/stack/status_stack.sh

source "$(dirname "$0")/stack_env.sh"

echo "=============================================="
echo "  Estado de la pila - Proyecto BigData"
echo "=============================================="
echo ""

_status() {
    if [ "$1" = "OK" ] || [ "$1" = "RUN" ]; then
        echo "  ✓ $2"
    else
        echo "  ✗ $2"
    fi
}

# HDFS
if jps 2>/dev/null | grep -q NameNode; then
    _status OK "HDFS (NameNode activo)"
    jps 2>/dev/null | grep -E "NameNode|DataNode|SecondaryNameNode" | sed 's/^/    /'
else
    _status STOP "HDFS"
fi
echo ""

# YARN
if jps 2>/dev/null | grep -q ResourceManager; then
    _status OK "YARN (ResourceManager activo)"
    jps 2>/dev/null | grep -E "ResourceManager|NodeManager" | sed 's/^/    /'
else
    _status STOP "YARN"
fi
echo ""

# Hive Metastore
if pgrep -f "hive.*metastore" >/dev/null 2>&1; then
    _status OK "Hive Metastore"
else
    _status STOP "Hive Metastore"
fi
echo ""

# MongoDB
if pgrep -x mongod >/dev/null 2>&1 || systemctl is-active --quiet mongod 2>/dev/null || systemctl is-active --quiet mongodb 2>/dev/null; then
    _status OK "MongoDB"
    if command -v mongosh &>/dev/null; then
        mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null && echo "    ping: OK" || true
    fi
else
    _status STOP "MongoDB"
fi
echo ""

# Kafka
if jps 2>/dev/null | grep -qi kafka; then
    _status OK "Kafka"
    jps 2>/dev/null | grep -i kafka | sed 's/^/    /'
else
    _status STOP "Kafka"
fi
echo ""

# NiFi
if [ -x "$NIFI_HOME/bin/nifi.sh" ]; then
    NIFI_STATUS=$("$NIFI_HOME/bin/nifi.sh" status 2>&1 || true)
    if echo "$NIFI_STATUS" | grep -qi "running"; then
        _status OK "NiFi (UI: https://localhost:8443/nifi)"
    else
        _status STOP "NiFi"
    fi
else
    echo "  ⊘ NiFi (no configurado)"
fi
echo ""

# Airflow
if pgrep -f "airflow scheduler" >/dev/null 2>&1; then
    _status OK "Airflow Scheduler"
else
    _status STOP "Airflow Scheduler"
fi
if pgrep -f "airflow webserver" >/dev/null 2>&1; then
    _status OK "Airflow Webserver (UI: http://localhost:8080)"
else
    _status STOP "Airflow Webserver"
fi
echo ""

# Spark: no es un servicio persistente; solo indicar si YARN está listo para ejecutar jobs
if jps 2>/dev/null | grep -q ResourceManager; then
    echo "  ℹ Spark: usa YARN; enviar jobs con spark-submit --master yarn"
else
    echo "  ℹ Spark: requiere YARN en marcha"
fi
echo ""

echo "=============================================="
echo "  Resumen rápido (jps):"
jps 2>/dev/null | grep -E "NameNode|DataNode|ResourceManager|NodeManager|Kafka|Hive|Metastore" || true
echo "=============================================="
