#!/bin/bash
# Script para corregir configuración de Kafka para modo standalone

echo "=== Corrigiendo Configuración de Kafka ==="
echo ""

KAFKA_CONFIG="/opt/kafka/config/kraft/server.properties"

# Verificar que el archivo existe
if [ ! -f "$KAFKA_CONFIG" ]; then
    echo "ERROR: No se encuentra $KAFKA_CONFIG"
    exit 1
fi

echo "1. Haciendo backup de configuración..."
sudo cp "$KAFKA_CONFIG" "${KAFKA_CONFIG}.backup"

echo "2. Modificando configuración para usar localhost..."
sudo sed -i 's|nodo1|localhost|g' "$KAFKA_CONFIG"

echo "3. Verificando cambios..."
echo ""
echo "Configuración actualizada:"
grep -E "(controller.quorum.voters|advertised.listeners)" "$KAFKA_CONFIG"

echo ""
echo "✓ Configuración corregida"
echo ""
echo "Próximos pasos:"
echo "1. Limpiar storage de Kafka: rm -rf /tmp/kafka-logs/*"
echo "2. Formatear storage: cd /opt/kafka && CLUSTER_ID=\$(bin/kafka-storage.sh random-uuid) && bin/kafka-storage.sh format -t \$CLUSTER_ID -c config/kraft/server.properties"
echo "3. Iniciar Kafka: cd /opt/kafka && bin/kafka-server-start.sh config/kraft/server.properties &"
