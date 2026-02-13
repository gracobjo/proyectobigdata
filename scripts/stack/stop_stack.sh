#!/bin/bash
# Apaga todos los componentes de la arquitectura en el orden correcto
# (Airflow → NiFi → Kafka → Hive → MongoDB → YARN → HDFS).
# Uso: bash scripts/stack/stop_stack.sh

set -e
source "$(dirname "$0")/stack_env.sh"

echo "=============================================="
echo "  Apagado de la pila - Proyecto BigData"
echo "=============================================="
echo ""

# --- 1. Airflow ---
echo "[1/7] Airflow"
if [ -f "$PROJECT_ROOT/scripts/utils/stop_airflow.sh" ]; then
    bash "$PROJECT_ROOT/scripts/utils/stop_airflow.sh" 2>&1 | sed 's/^/  /'
else
    if pgrep -f "airflow scheduler" >/dev/null 2>&1; then
        pkill -f "airflow scheduler" 2>/dev/null || true
        echo "  ✓ Scheduler detenido"
    fi
    if pgrep -f "airflow webserver" >/dev/null 2>&1; then
        pkill -f "airflow webserver" 2>/dev/null || true
        echo "  ✓ Webserver detenido"
    fi
fi
echo ""

# --- 2. NiFi ---
echo "[2/7] NiFi"
if [ -x "$NIFI_HOME/bin/nifi.sh" ]; then
    NIFI_STATUS=$("$NIFI_HOME/bin/nifi.sh" status 2>&1 || true)
    if echo "$NIFI_STATUS" | grep -qi "running"; then
        "$NIFI_HOME/bin/nifi.sh" stop
        echo "  ✓ NiFi detenido"
    else
        echo "  ✓ NiFi no estaba corriendo"
    fi
else
    echo "  ⊘ NiFi no configurado"
fi
echo ""

# --- 3. Kafka ---
echo "[3/7] Kafka"
if jps 2>/dev/null | grep -qi kafka; then
    if [ -x "$KAFKA_HOME/bin/kafka-server-stop.sh" ]; then
        "$KAFKA_HOME/bin/kafka-server-stop.sh" 2>/dev/null || true
        sleep 3
    fi
    # Por si kafka-server-stop no acaba con el proceso
    pkill -f kafka.Kafka 2>/dev/null || true
    sleep 2
    echo "  ✓ Kafka detenido"
else
    echo "  ✓ Kafka no estaba corriendo"
fi
echo ""

# --- 4. Hive Metastore ---
echo "[4/7] Hive Metastore"
if pgrep -f "hive.*metastore" >/dev/null 2>&1; then
    pkill -f "hive.*metastore" 2>/dev/null || true
    sleep 2
    echo "  ✓ Metastore detenido"
else
    echo "  ✓ Metastore no estaba corriendo"
fi
if pgrep -f "hiveserver2" >/dev/null 2>&1; then
    pkill -f hiveserver2 2>/dev/null || true
    echo "  ✓ HiveServer2 detenido"
fi
echo ""

# --- 5. MongoDB ---
echo "[5/7] MongoDB"
if systemctl is-active --quiet mongod 2>/dev/null || systemctl is-active --quiet mongodb 2>/dev/null; then
    systemctl stop mongod 2>/dev/null || systemctl stop mongodb 2>/dev/null
    echo "  ✓ MongoDB detenido (systemd)"
elif pgrep -x mongod >/dev/null 2>&1; then
    if [ -f /tmp/mongod.pid ]; then
        kill "$(cat /tmp/mongod.pid)" 2>/dev/null || pkill -x mongod 2>/dev/null || true
    else
        pkill -x mongod 2>/dev/null || true
    fi
    sleep 2
    echo "  ✓ MongoDB detenido"
else
    echo "  ✓ MongoDB no estaba corriendo"
fi
echo ""

# --- 6. YARN ---
echo "[6/7] Hadoop YARN"
if command -v stop-yarn.sh &>/dev/null && [ -x "$HADOOP_HOME/sbin/stop-yarn.sh" ]; then
    if jps 2>/dev/null | grep -q ResourceManager; then
        stop-yarn.sh
        echo "  ✓ YARN detenido (stop-yarn.sh)"
    else
        echo "  ✓ YARN no estaba corriendo"
    fi
else
    if jps 2>/dev/null | grep -q ResourceManager; then
        yarn --daemon stop resourcemanager 2>/dev/null || true
        yarn --daemon stop nodemanager 2>/dev/null || true
        sleep 3
        echo "  ✓ YARN detenido"
    else
        echo "  ✓ YARN no estaba corriendo"
    fi
fi
echo ""

# --- 7. HDFS ---
echo "[7/7] Hadoop HDFS"
if command -v stop-dfs.sh &>/dev/null && [ -x "$HADOOP_HOME/sbin/stop-dfs.sh" ]; then
    if jps 2>/dev/null | grep -q NameNode; then
        stop-dfs.sh
        echo "  ✓ HDFS detenido (stop-dfs.sh)"
    else
        echo "  ✓ HDFS no estaba corriendo"
    fi
else
    if jps 2>/dev/null | grep -q NameNode; then
        hdfs --daemon stop datanode 2>/dev/null || true
        hdfs --daemon stop secondarynamenode 2>/dev/null || true
        hdfs --daemon stop namenode 2>/dev/null || true
        sleep 3
        echo "  ✓ HDFS detenido"
    else
        echo "  ✓ HDFS no estaba corriendo"
    fi
fi
echo ""

echo "=============================================="
echo "  Apagado completado. Comprobar con:"
echo "  bash scripts/stack/status_stack.sh"
echo "=============================================="
