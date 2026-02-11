#!/bin/bash
# Terminal 3: Análisis de retrasos
# Uso: bash scripts/run/03_delay_analysis.sh
# Dejar corriendo hasta que termine o presionar Ctrl+C
# IMPORTANTE: Ejecutar DESPUÉS de que data_cleaning.py haya procesado algunos batches

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Ejecutando análisis de retrasos ==="
echo "Lee de: filtered-data"
echo "Escribe en: alerts (Kafka) y delay_aggregates (HDFS)"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/streaming/delay_analysis.py
