#!/bin/bash
# Script para arreglar permisos de Kafka y arrancarlo
# Uso: bash scripts/setup/fix_kafka_permissions.sh
# Requiere sudo para cambiar permisos de /tmp/kafka-logs

set -e
KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"
CONFIG="${KAFKA_HOME}/config/server.properties"
LOG_DIRS=$(grep -E "^log\.dirs=" "$CONFIG" 2>/dev/null | cut -d= -f2 || echo "/tmp/kafka-logs")

echo "=== Arreglar permisos de Kafka y arrancar ==="
echo ""

# Verificar si Kafka ya está corriendo
if jps | grep -qi kafka; then
    echo "✓ Kafka ya está ejecutándose"
    jps | grep -i kafka
    exit 0
fi

# Cambiar permisos del directorio de logs
echo "1. Cambiando permisos de $LOG_DIRS..."
sudo chown -R hadoop:hadoop "$LOG_DIRS" 2>/dev/null || {
    echo "⚠ No se pudieron cambiar permisos. Intentando crear directorio alternativo..."
    ALT_LOG_DIRS="$HOME/kafka-logs"
    mkdir -p "$ALT_LOG_DIRS"
    # Modificar config temporalmente para usar directorio alternativo
    sed -i.bak "s|^log\.dirs=.*|log.dirs=$ALT_LOG_DIRS|" "$CONFIG"
    LOG_DIRS="$ALT_LOG_DIRS"
    echo "   Usando directorio alternativo: $LOG_DIRS"
}

# Verificar si está inicializado
if [ ! -f "$LOG_DIRS/meta.properties" ]; then
    echo "2. Kafka no inicializado. Formateando..."
    CLUSTER_ID=$("$KAFKA_HOME/bin/kafka-storage.sh" random-uuid)
    "$KAFKA_HOME/bin/kafka-storage.sh" format -t "$CLUSTER_ID" -c "$CONFIG"
    echo "   Cluster ID: $CLUSTER_ID"
else
    echo "2. ✓ Kafka ya inicializado"
fi

# Arrancar Kafka
echo "3. Arrancando Kafka..."
"$KAFKA_HOME/bin/kafka-server-start.sh" -daemon "$CONFIG"

sleep 5

# Verificar
if jps | grep -qi kafka; then
    echo "✓ Kafka arrancado correctamente"
    jps | grep -i kafka
    echo ""
    echo "4. Verificar topics:"
    echo "   /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
else
    echo "❌ Error arrancando Kafka. Revisa logs en $LOG_DIRS"
    exit 1
fi
