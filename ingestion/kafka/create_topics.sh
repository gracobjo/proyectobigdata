#!/bin/bash
# Script para crear los topics de Kafka necesarios para el proyecto

KAFKA_HOME=${KAFKA_HOME:-/opt/kafka}
BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-localhost:9092}

echo "Creando topics de Kafka..."

# Topic para datos crudos
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $BOOTSTRAP_SERVER \
  --topic raw-data \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --config segment.ms=86400000

# Topic para datos filtrados
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $BOOTSTRAP_SERVER \
  --topic filtered-data \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --config segment.ms=86400000

# Topic para alertas
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $BOOTSTRAP_SERVER \
  --topic alerts \
  --partitions 1 \
  --replication-factor 1

echo "Topics creados exitosamente:"
$KAFKA_HOME/bin/kafka-topics.sh --list --bootstrap-server $BOOTSTRAP_SERVER
