#!/bin/bash
# Prueba rápida: escribe 1 mensaje en raw-data y lo lee con el consumer.
# Si ves "mensaje_test_123", el broker está bien. Usar 127.0.0.1 para evitar IPv6.
# Uso: bash scripts/utils/kafka_test_produce_consume.sh

set -e
BOOTSTRAP="${BOOTSTRAP_SERVER:-127.0.0.1:9092}"
TOPIC="${KAFKA_TOPIC:-raw-data}"
KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"

echo "=== Diagnóstico rápido ==="
echo "1. Proceso escuchando en 9092:"
ss -tlnp 2>/dev/null | grep 9092 || netstat -tlnp 2>/dev/null | grep 9092 || true
echo ""
echo "2. Config que usa Kafka (advertised.listeners):"
grep -E "^advertised.listeners=" "${KAFKA_HOME}/config/server.properties" 2>/dev/null || true
echo ""
echo "3. Enviando 1 mensaje a $TOPIC (bootstrap: $BOOTSTRAP)..."
echo "mensaje_test_123" | "$KAFKA_HOME/bin/kafka-console-producer.sh" --bootstrap-server "$BOOTSTRAP" --topic "$TOPIC"
sleep 2

echo "4. Leyendo 1 mensaje (timeout 15s, grupo nuevo)..."
"$KAFKA_HOME/bin/kafka-console-consumer.sh" --bootstrap-server "$BOOTSTRAP" \
  --topic "$TOPIC" --from-beginning --max-messages 1 --timeout-ms 15000 \
  --consumer-property group.id=test-group-$$

echo ""
echo "Si viste 'mensaje_test_123', el broker funciona. Si TimeoutException/0 messages, revisa advertised.listeners y reinicia Kafka."
