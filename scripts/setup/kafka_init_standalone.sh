#!/bin/bash
# Inicializa Kafka en modo KRaft para standalone (formatear storage y opcionalmente aplicar config).
# Ejecutar UNA VEZ cuando aparece "No readable meta.properties files found".
# Uso: bash scripts/setup/kafka_init_standalone.sh

set -e
KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"
# Usar config KRaft si existe (el stack arranca con esta); si no, server.properties clásico
if [ -f "${KAFKA_HOME}/config/kraft/server.properties" ]; then
    CONFIG="${KAFKA_HOME}/config/kraft/server.properties"
else
    CONFIG="${KAFKA_HOME}/config/server.properties"
fi
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_CONFIG="$PROJECT_ROOT/config/kafka/server.properties"

echo "=== Inicializar Kafka KRaft (standalone) ==="
echo "  Config: $CONFIG"
echo ""

# 1. Aplicar config del proyecto a server.properties si usamos kraft (opcional)
if [ -f "$PROJECT_CONFIG" ] && [ "$CONFIG" = "${KAFKA_HOME}/config/server.properties" ]; then
    echo "1. Copiando config del proyecto..."
    sudo cp "$PROJECT_CONFIG" "$CONFIG"
else
    echo "1. Usando $CONFIG (ya existe)."
fi

# 2. Limpiar directorio de logs (si existe meta.properties viejo, format falla por cluster ID distinto)
LOG_DIRS=$(grep -E "^log\.dirs=" "$CONFIG" 2>/dev/null | cut -d= -f2)
if [ -z "$LOG_DIRS" ]; then
    LOG_DIRS="/tmp/kafka-logs"
fi
echo "2. Limpiando $LOG_DIRS (quitar meta.properties antiguo)..."
if [ -d "$LOG_DIRS" ]; then
    rm -rf "${LOG_DIRS:?}"/*
    echo "   Hecho."
else
    mkdir -p "$LOG_DIRS"
fi

# 3. Formatear storage (necesario la primera vez o tras borrar log.dirs)
echo "3. Formateando storage de Kafka (KRaft)..."
CLUSTER_ID=$("$KAFKA_HOME/bin/kafka-storage.sh" random-uuid)
"$KAFKA_HOME/bin/kafka-storage.sh" format -t "$CLUSTER_ID" -c "$CONFIG"
echo "   Cluster ID: $CLUSTER_ID"

echo ""
echo "4. Arrancar Kafka:"
echo "   $KAFKA_HOME/bin/kafka-server-start.sh -daemon $CONFIG"
echo ""
echo "   O usar el stack: bash $PROJECT_ROOT/scripts/stack/start_stack.sh"
echo "5. Comprobar: jps | grep -i kafka"
echo "6. Crear topics: bash $PROJECT_ROOT/ingestion/kafka/create_topics.sh"
echo "=== Fin ==="
