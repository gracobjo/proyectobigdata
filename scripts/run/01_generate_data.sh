#!/bin/bash
# Terminal 1: Generar datos de prueba
# Uso: bash scripts/run/01_generate_data.sh

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Generando datos de prueba ==="
echo "Generando 100 mensajes en raw-data..."
python scripts/utils/generate_sample_data.py 100

echo ""
echo "✓ Datos generados. Verifica con:"
echo "  /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw-data --from-beginning --max-messages 3"
