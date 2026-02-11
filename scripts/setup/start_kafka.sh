#!/bin/bash
# Script para arrancar Kafka (requiere que esté inicializado)
# Uso: bash scripts/setup/start_kafka.sh

KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"
CONFIG="${KAFKA_HOME}/config/server.properties"

echo "=== Arrancar Kafka ==="

# Verificar si ya está corriendo
if jps | grep -qi kafka; then
    echo "✓ Kafka ya está ejecutándose"
    jps | grep -i kafka
    exit 0
fi

# Verificar si está inicializado
LOG_DIRS=$(grep -E "^log\.dirs=" "$CONFIG" 2>/dev/null | cut -d= -f2 || echo "/tmp/kafka-logs")
if [ ! -f "$LOG_DIRS/meta.properties" ]; then
    echo "❌ Kafka no está inicializado."
    echo "Ejecuta primero: bash scripts/setup/kafka_init_standalone.sh"
    echo "(Requiere sudo para copiar config y limpiar logs)"
    exit 1
fi

# Arrancar Kafka
echo "Arrancando Kafka..."
"$KAFKA_HOME/bin/kafka-server-start.sh" -daemon "$CONFIG"

sleep 3

# Verificar
if jps | grep -qi kafka; then
    echo "✓ Kafka arrancado correctamente"
    jps | grep -i kafka
else
    echo "❌ Error arrancando Kafka. Revisa logs:"
    echo "   tail -f $LOG_DIRS/../server.log"
    exit 1
fi
