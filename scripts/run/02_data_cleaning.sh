#!/bin/bash
# Terminal 2: Limpieza de datos
# Uso: bash scripts/run/02_data_cleaning.sh
# Dejar corriendo hasta que termine o presionar Ctrl+C

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Ejecutando limpieza de datos ==="
echo "Lee de: raw-data"
echo "Escribe en: filtered-data"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_cleaning.py
