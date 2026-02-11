#!/bin/bash
# Terminal 4: Consumidor MongoDB
# Uso: bash scripts/run/04_mongodb_consumer.sh
# Dejar corriendo hasta que termine o presionar Ctrl+C
# IMPORTANTE: Ejecutar DESPUÉS de que delay_analysis.py haya generado algunos alerts

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Consumidor Kafka → MongoDB ==="
echo "Lee de: alerts (Kafka)"
echo "Escribe en: route_delay_aggregates (MongoDB)"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

python storage/mongodb/kafka_to_mongodb_alerts.py
