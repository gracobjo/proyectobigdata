#!/bin/bash
# Arranca todos los componentes de la arquitectura en el orden correcto
# (HDFS → YARN → Hive Metastore → MongoDB → Kafka → NiFi → Airflow).
# Uso: bash scripts/stack/start_stack.sh

set -e
source "$(dirname "$0")/stack_env.sh"

echo "=============================================="
echo "  Arranque de la pila - Proyecto BigData"
echo "=============================================="
echo ""

# --- 1. Hadoop HDFS ---
echo "[1/7] Hadoop HDFS"
if jps 2>/dev/null | grep -q NameNode; then
    echo "  ✓ HDFS ya está corriendo"
else
    if command -v start-dfs.sh &>/dev/null && [ -x "$HADOOP_HOME/sbin/start-dfs.sh" ]; then
        start-dfs.sh 2>/dev/null || true
        sleep 6
    fi
    if ! jps 2>/dev/null | grep -q NameNode; then
        echo "  Arrancando HDFS en modo local (daemons)..."
        hdfs --daemon start namenode 2>/dev/null || true
        sleep 4
        hdfs --daemon start datanode 2>/dev/null || true
        sleep 3
        hdfs --daemon start secondarynamenode 2>/dev/null || true
        sleep 2
    fi
    if jps 2>/dev/null | grep -q NameNode; then
        echo "  ✓ HDFS arrancado"
    else
        echo "  ⚠ HDFS no arrancó (revisa $HADOOP_HOME/logs)"
    fi
fi
hdfs dfsadmin -safemode leave 2>/dev/null || true
echo ""

# --- 2. Hadoop YARN ---
echo "[2/7] Hadoop YARN"
if jps 2>/dev/null | grep -q ResourceManager; then
    echo "  ✓ YARN ya está corriendo"
else
    if command -v start-yarn.sh &>/dev/null && [ -x "$HADOOP_HOME/sbin/start-yarn.sh" ]; then
        start-yarn.sh 2>/dev/null &
        sleep 12
    fi
    if ! jps 2>/dev/null | grep -q ResourceManager; then
        echo "  Arrancando YARN en modo local (daemons)..."
        yarn --daemon start resourcemanager 2>/dev/null || true
        sleep 3
        yarn --daemon start nodemanager 2>/dev/null || true
        sleep 2
    fi
    if jps 2>/dev/null | grep -q ResourceManager; then
        echo "  ✓ YARN arrancado"
    else
        echo "  ⚠ YARN no arrancó (revisa $HADOOP_HOME/logs)"
    fi
fi
echo ""

# --- 3. Hive Metastore ---
echo "[3/7] Hive Metastore"
if [ -n "$HIVE_HOME" ] && [ -x "$HIVE_HOME/bin/hive" ]; then
    if pgrep -f "hive.*metastore" >/dev/null 2>&1; then
        echo "  ✓ Metastore ya está corriendo"
    else
        mkdir -p "$HIVE_HOME/logs" 2>/dev/null || true
        nohup "$HIVE_HOME/bin/hive" --service metastore > "$HIVE_HOME/logs/metastore.log" 2>&1 &
        sleep 3
        echo "  ✓ Metastore arrancado (logs: $HIVE_HOME/logs/metastore.log)"
    fi
else
    echo "  ⊘ HIVE_HOME no configurado o hive no encontrado; omitido"
fi
echo ""

# --- 4. MongoDB ---
echo "[4/7] MongoDB"
if systemctl is-active --quiet mongod 2>/dev/null || systemctl is-active --quiet mongodb 2>/dev/null; then
    echo "  ✓ MongoDB ya está corriendo (systemd)"
elif pgrep -x mongod >/dev/null 2>&1; then
    echo "  ✓ MongoDB ya está corriendo"
else
    if systemctl start mongod 2>/dev/null; then
        echo "  ✓ MongoDB arrancado (systemctl mongod)"
    elif systemctl start mongodb 2>/dev/null; then
        echo "  ✓ MongoDB arrancado (systemctl mongodb)"
    elif command -v mongod &>/dev/null; then
        mkdir -p "$(dirname "$(mongod --version 2>&1 | head -1)" 2>/dev/null)" || true
        mongod --fork --logpath /tmp/mongod.log --pidfilepath /tmp/mongod.pid 2>/dev/null && echo "  ✓ MongoDB arrancado (fork)" || echo "  ⚠ No se pudo arrancar MongoDB (¿permisos?)"
    else
        echo "  ⊘ mongod no encontrado; omitido"
    fi
fi
echo ""

# --- 5. Kafka ---
echo "[5/7] Kafka"
if jps 2>/dev/null | grep -qi kafka; then
    echo "  ✓ Kafka ya está corriendo"
else
    if [ -x "$KAFKA_HOME/bin/kafka-server-start.sh" ] && [ -f "$KAFKA_CONFIG" ]; then
        "$KAFKA_HOME/bin/kafka-server-start.sh" -daemon "$KAFKA_CONFIG"
        sleep 4
        if jps | grep -qi kafka; then
            echo "  ✓ Kafka arrancado"
        else
            echo "  ⚠ Kafka no respondió; revisa logs en $KAFKA_HOME/logs"
            if [ -f "$KAFKA_HOME/logs/server.log" ] && grep -q "No readable meta.properties" "$KAFKA_HOME/logs/server.log" 2>/dev/null; then
                echo "  → Kafka en modo KRaft necesita formatear el storage. Ejecuta UNA VEZ:"
                echo "     bash $PROJECT_ROOT/scripts/setup/kafka_init_standalone.sh"
            fi
        fi
    else
        echo "  ⊘ KAFKA_HOME o config no encontrado; omitido"
    fi
fi
echo ""

# --- 6. NiFi ---
echo "[6/7] NiFi"
if [ -x "$NIFI_HOME/bin/nifi.sh" ]; then
    NIFI_STATUS=$("$NIFI_HOME/bin/nifi.sh" status 2>&1 || true)
    if echo "$NIFI_STATUS" | grep -qi "running"; then
        echo "  ✓ NiFi ya está corriendo"
    else
        "$NIFI_HOME/bin/nifi.sh" start
        sleep 5
        echo "  ✓ NiFi arrancado (UI: https://localhost:8443/nifi)"
    fi
else
    echo "  ⊘ NIFI_HOME no configurado o nifi.sh no encontrado; omitido"
fi
echo ""

# --- 7. Airflow ---
echo "[7/7] Airflow"
if [ -f "$PROJECT_ROOT/scripts/utils/start_airflow.sh" ]; then
    if pgrep -f "airflow scheduler" >/dev/null 2>&1; then
        echo "  ✓ Airflow ya está corriendo"
    else
        bash "$PROJECT_ROOT/scripts/utils/start_airflow.sh" 2>&1 | sed 's/^/  /'
    fi
else
    if pgrep -f "airflow scheduler" >/dev/null 2>&1; then
        echo "  ✓ Airflow ya está corriendo"
    elif command -v airflow &>/dev/null; then
        export AIRFLOW_HOME="${AIRFLOW_HOME:-$HOME/airflow}"
        airflow scheduler > "$AIRFLOW_HOME/logs/scheduler.log" 2>&1 &
        airflow webserver --port 8080 > "$AIRFLOW_HOME/logs/webserver.log" 2>&1 &
        sleep 3
        echo "  ✓ Airflow arrancado (UI: http://localhost:8080)"
    else
        echo "  ⊘ Airflow no encontrado; omitido"
    fi
fi
echo ""

echo "=============================================="
echo "  Arranque completado. Comprobar con:"
echo "  bash scripts/stack/status_stack.sh"
echo "=============================================="
