#!/bin/bash
# Inicializa Kafka en modo KRaft para standalone (formatear storage y opcionalmente aplicar config).
# Ejecutar UNA VEZ cuando aparece "No readable meta.properties files found".
# Uso: bash scripts/setup/kafka_init_standalone.sh

set -e
KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"
CONFIG="${KAFKA_HOME}/config/server.properties"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_CONFIG="$PROJECT_ROOT/config/kafka/server.properties"

echo "=== Inicializar Kafka KRaft (standalone) ==="
echo ""

# 1. Aplicar config del proyecto si existe (localhost en advertised y quorum)
if [ -f "$PROJECT_CONFIG" ]; then
    echo "1. Copiando config del proyecto (localhost para standalone)..."
    sudo cp "$PROJECT_CONFIG" "$CONFIG"
else
    echo "1. Ajustando $CONFIG a mano: advertised.listeners=PLAINTEXT://localhost:9092 y controller.quorum.voters=1@localhost:9093"
    sudo sed -i 's|advertised.listeners=PLAINTEXT://nodo1:9092|advertised.listeners=PLAINTEXT://localhost:9092|g' "$CONFIG"
    sudo sed -i 's|controller.quorum.voters=1@nodo1:9093|controller.quorum.voters=1@localhost:9093|g' "$CONFIG"
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
echo "5. Comprobar: jps | grep -i kafka"
echo "6. Crear topics: bash $PROJECT_ROOT/ingestion/kafka/create_topics.sh"
echo "=== Fin ==="
